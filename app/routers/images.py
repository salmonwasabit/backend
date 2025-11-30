import hashlib
import io
import logging
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps
from sqlalchemy import and_
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..main import User
from ..models.image import Image as ImageModel

router = APIRouter()
logger = logging.getLogger(__name__)

# Try to import python-magic, fallback to basic validation if not available
try:
    import magic

    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logger.warning("python-magic not available, falling back to basic file validation")

# Configuration
UPLOAD_DIR = Path("uploads")
ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_WIDTH = 2000
MAX_HEIGHT = 2000
THUMBNAIL_SIZE = (300, 300)
QUALITY = 85

# Create directories
for entity_type in ["products", "categories", "banners", "temp"]:
    (UPLOAD_DIR / entity_type).mkdir(parents=True, exist_ok=True)


def validate_image_content(file_content: bytes, filename: str) -> str:
    """Validate image content using magic numbers or fallback validation"""
    if MAGIC_AVAILABLE:
        try:
            mime_type = magic.from_buffer(file_content, mime=True)
            if mime_type not in ALLOWED_TYPES:
                raise HTTPException(400, f"Invalid file type: {mime_type}")
            return mime_type
        except Exception as e:
            logger.error(f"Magic validation failed for {filename}: {e}")
            # Fall through to basic validation

    # Fallback: Basic file signature validation
    if len(file_content) < 4:
        raise HTTPException(400, "File too small")

    # Check file signatures (magic numbers)
    signatures = {
        b"\xff\xd8\xff": "image/jpeg",  # JPEG
        b"\x89PNG\r\n\x1a\n": "image/png",  # PNG
        b"GIF87a": "image/gif",  # GIF87a
        b"GIF89a": "image/gif",  # GIF89a
        b"RIFF": (
            "image/webp"
            if len(file_content) > 12 and file_content[8:12] == b"WEBP"
            else None
        ),  # WebP
    }

    for signature, mime_type in signatures.items():
        if file_content.startswith(signature) and mime_type in ALLOWED_TYPES:
            return mime_type

    # If no signature matches, try to validate with PIL as final fallback
    try:
        import io

        from PIL import Image

        Image.open(io.BytesIO(file_content)).verify()
        # If PIL can open it, assume it's a valid image
        # Check file extension for MIME type
        ext = filename.lower().split(".")[-1]
        ext_to_mime = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
            "gif": "image/gif",
        }
        mime_type = ext_to_mime.get(ext, "image/jpeg")  # Default to JPEG
        if mime_type in ALLOWED_TYPES:
            return mime_type
    except Exception as e:
        logger.error(f"Fallback validation failed for {filename}: {e}")

    raise HTTPException(400, "Invalid or unsupported image file")


def optimize_image(
    image: Image.Image,
    max_width: int = MAX_WIDTH,
    max_height: int = MAX_HEIGHT,
    quality: int = QUALITY,
) -> Image.Image:
    """Optimize image for web delivery"""
    # Convert to RGB if necessary
    if image.mode in ("RGBA", "LA", "P"):
        # Create white background for transparent images
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "P":
            image = image.convert("RGBA")
        background.paste(
            image, mask=image.split()[-1] if image.mode == "RGBA" else None
        )
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    # Auto-rotate based on EXIF
    image = ImageOps.exif_transpose(image)

    # Resize if too large
    if image.width > max_width or image.height > max_height:
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

    return image


def create_thumbnail(image: Image.Image, size: tuple = THUMBNAIL_SIZE) -> Image.Image:
    """Create thumbnail version of image"""
    # Create square thumbnail
    thumb = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
    return thumb


def cleanup_temp_files(temp_path: str):
    """Background task to clean up temporary files"""
    try:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            logger.info(f"Cleaned up temp file: {temp_path}")
    except Exception as e:
        logger.error(f"Failed to cleanup {temp_path}: {e}")


@router.post("/upload/{entity_type}")
async def upload_image(
    entity_type: str,
    file: UploadFile = File(...),
    alt_text: Optional[str] = None,
    entity_id: Optional[int] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload and process image with comprehensive validation and optimization"""

    # Validate entity type
    allowed_entities = ["products", "categories", "banners"]
    if entity_type not in allowed_entities:
        raise HTTPException(400, f"Invalid entity type. Allowed: {allowed_entities}")

    # Validate file size
    file_content = await file.read()
    file_size = len(file_content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            400, f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    if file_size == 0:
        raise HTTPException(400, "Empty file")

    # Validate content
    mime_type = validate_image_content(file_content, file.filename)

    # Generate secure filename
    file_hash = hashlib.sha256(file_content).hexdigest()[:16]
    file_extension = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4().hex}_{file_hash}{file_extension}"

    try:
        # Process image
        image = Image.open(io.BytesIO(file_content))

        # Validate image dimensions
        if image.width > MAX_WIDTH * 2 or image.height > MAX_HEIGHT * 2:
            raise HTTPException(
                400, f"Image dimensions too large. Max: {MAX_WIDTH*2}x{MAX_HEIGHT*2}"
            )

        # Optimize main image
        optimized_image = optimize_image(image)

        # Create thumbnail
        thumbnail = create_thumbnail(image)

        # Save files
        entity_dir = UPLOAD_DIR / entity_type
        main_path = entity_dir / unique_filename
        thumb_filename = f"thumb_{unique_filename}"
        thumb_path = entity_dir / thumb_filename

        # Save optimized image
        optimized_image.save(main_path, "JPEG", quality=QUALITY, optimize=True)

        # Save thumbnail
        thumbnail.save(thumb_path, "JPEG", quality=QUALITY, optimize=True)

        # Get final file sizes
        final_size = main_path.stat().st_size
        thumb_size = thumb_path.stat().st_size

        # Save to database
        db_image = ImageModel(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=str(main_path),
            thumbnail_path=str(thumb_path),
            file_size=final_size,
            mime_type="image/jpeg",  # We convert everything to JPEG
            width=optimized_image.width,
            height=optimized_image.height,
            entity_type=entity_type,
            entity_id=entity_id,
            alt_text=alt_text,
            uploaded_by=current_user.id,
        )

        db.add(db_image)
        db.commit()
        db.refresh(db_image)

        logger.info(f"Image uploaded: {unique_filename} by user {current_user.id}")

        return {
            "success": True,
            "id": db_image.id,
            "filename": unique_filename,
            "url": f"/api/images/{entity_type}/{unique_filename}",
            "thumbnail_url": f"/api/images/{entity_type}/thumb_{unique_filename}",
            "width": optimized_image.width,
            "height": optimized_image.height,
            "size": final_size,
            "mime_type": "image/jpeg",
        }

    except Exception as e:
        logger.error(f"Image upload failed: {e}")
        # Clean up any partially created files
        for path in [main_path, thumb_path]:
            if path.exists():
                path.unlink()
        raise HTTPException(500, f"Image processing failed: {str(e)}")


@router.get("/{entity_type}/{filename}")
async def get_image(entity_type: str, filename: str):
    """Serve optimized images with proper caching headers"""

    allowed_entities = ["products", "categories", "banners"]
    if entity_type not in allowed_entities:
        raise HTTPException(404, "Entity type not found")

    file_path = UPLOAD_DIR / entity_type / filename

    if not file_path.exists():
        raise HTTPException(404, "Image not found")

    # Return file with caching headers
    response = FileResponse(
        file_path,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "public, max-age=31536000",  # 1 year
            "ETag": f'"{file_path.stat().st_mtime}"',
        },
    )
    return response


@router.get("/meta/{image_id}")
async def get_image_metadata(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get image metadata"""
    image = db.query(ImageModel).filter(ImageModel.id == image_id).first()
    if not image:
        raise HTTPException(404, "Image not found")

    return {
        "id": image.id,
        "filename": image.filename,
        "original_filename": image.original_filename,
        "url": f"/api/images/{image.entity_type}/{image.filename}",
        "thumbnail_url": f"/api/images/{image.entity_type}/thumb_{image.filename}",
        "width": image.width,
        "height": image.height,
        "size": image.file_size,
        "mime_type": image.mime_type,
        "entity_type": image.entity_type,
        "entity_id": image.entity_id,
        "alt_text": image.alt_text,
        "is_active": image.is_active,
        "uploaded_by": image.uploaded_by,
        "created_at": image.created_at,
    }


@router.put("/{image_id}")
async def update_image_metadata(
    image_id: int,
    alt_text: Optional[str] = None,
    entity_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update image metadata"""
    image = db.query(ImageModel).filter(ImageModel.id == image_id).first()
    if not image:
        raise HTTPException(404, "Image not found")

    # Update fields
    if alt_text is not None:
        image.alt_text = alt_text
    if entity_id is not None:
        image.entity_id = entity_id
    if is_active is not None:
        image.is_active = is_active

    image.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Image updated successfully"}


@router.delete("/{image_id}")
async def delete_image(
    image_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete image and clean up files"""
    image = db.query(ImageModel).filter(ImageModel.id == image_id).first()
    if not image:
        raise HTTPException(404, "Image not found")

    # Delete files
    files_to_delete = []
    if image.file_path and os.path.exists(image.file_path):
        files_to_delete.append(image.file_path)
    if image.thumbnail_path and os.path.exists(image.thumbnail_path):
        files_to_delete.append(image.thumbnail_path)

    # Delete from database
    db.delete(image)
    db.commit()

    # Clean up files in background
    for file_path in files_to_delete:
        background_tasks.add_task(cleanup_temp_files, file_path)

    logger.info(f"Image deleted: {image.filename} by user {current_user.id}")

    return {"message": "Image deleted successfully"}


@router.get("/list/{entity_type}")
async def list_images(
    entity_type: str,
    entity_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List images with pagination"""
    query = db.query(ImageModel).filter(
        and_(ImageModel.entity_type == entity_type, ImageModel.is_active == True)
    )

    if entity_id is not None:
        query = query.filter(ImageModel.entity_id == entity_id)

    total = query.count()
    images = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "images": [
            {
                "id": img.id,
                "filename": img.filename,
                "url": f"/api/images/{img.entity_type}/{img.filename}",
                "thumbnail_url": f"/api/images/{img.entity_type}/thumb_{img.filename}",
                "width": img.width,
                "height": img.height,
                "size": img.file_size,
                "alt_text": img.alt_text,
                "created_at": img.created_at,
            }
            for img in images
        ],
    }
