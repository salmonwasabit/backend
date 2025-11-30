import os
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import uvicorn
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker
from sqlalchemy.sql import func

# Database setup
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://vape_user:vape_password@localhost:5432/vape_cms"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Auth configuration
SECRET_KEY = os.getenv(
    "SECRET_KEY", "your-super-secure-secret-key-change-this-in-production"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category = Column(String)
    image_url = Column(String(500))  # Add image_url field
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship with images
    images = relationship(
        "Image",
        back_populates="product",
        cascade="all, delete-orphan",
        primaryjoin="and_(Product.id == foreign(Image.entity_id), Image.entity_type == 'products')",
    )


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), unique=True, index=True, nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    thumbnail_path = Column(String(500))
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    width = Column(Integer)
    height = Column(Integer)
    entity_type = Column(
        String(50), nullable=False
    )  # "products", "categories", "banners"
    entity_id = Column(Integer, index=True)  # Link to product/category
    alt_text = Column(String(255))  # For accessibility
    is_active = Column(Boolean, default=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    uploader = relationship("User", backref="uploaded_images")
    product = relationship(
        "Product",
        back_populates="images",
        primaryjoin="and_(foreign(Image.entity_id) == Product.id, Image.entity_type == 'products')",
    )


class Media(Base):
    __tablename__ = "media"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    mime_type = Column(String)
    size = Column(Integer)
    url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ProductImage(Base):
    __tablename__ = "product_images"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    media_id = Column(Integer, ForeignKey("media.id"))
    product = relationship("Product")
    media = relationship("Media")


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Create tables with retry (helps when the DB container isn't ready yet)
def create_tables_with_retry(retries: int = 8, delay: float = 2.0):
    for attempt in range(1, retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except OperationalError as e:
            # Print to stdout so container logs show retry attempts
            print(f"Database not ready (attempt {attempt}/{retries}): {e}")
            if attempt == retries:
                # re-raise after final attempt so failure is visible
                raise
            time.sleep(delay)


# create_tables_with_retry()


# Pydantic models
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    image_url: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    images: List[dict] = []

    class Config:
        from_attributes = True


class MediaBase(BaseModel):
    filename: str
    original_filename: str
    mime_type: Optional[str]
    size: Optional[int]
    url: str


class MediaCreate(BaseModel):
    filename: str
    original_filename: str
    mime_type: Optional[str]
    size: Optional[int]


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    username: str
    email: str
    is_active: int


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# FastAPI app
app = FastAPI(title="Vape CMS API", version="1.0.0")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


# Test route - moved to right after app creation
@app.get("/test123")
def test123():
    return {"message": "Test123 working"}


# Redirect /login to /admin/login for convenience
@app.get("/login")
def redirect_login():
    return RedirectResponse(url="/admin/login", status_code=302)


# CORS middleware
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
from .routers import images

app.include_router(images.router, prefix="/api/images", tags=["images"])

# Templates
templates = Jinja2Templates(directory="templates")


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Auth functions
def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user


# Auth API Routes
@app.post("/api/auth/login", response_model=Token)
def login(credentials: dict, db: Session = Depends(get_db)):
    user = authenticate_user(
        db, credentials.get("username"), credentials.get("password")
    )
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


# API Routes
@app.get("/api/test2")
def get_test2():
    return {"message": "Test2 working"}


@app.get("/api/products", response_model=List[ProductResponse])
def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = db.query(Product).offset(skip).limit(limit).all()
    # Add images to each product
    for product in products:
        product_images = (
            db.query(Image)
            .filter(
                Image.entity_type == "products",
                Image.entity_id == product.id,
                Image.is_active == True,
            )
            .all()
        )
        product.images = [
            {
                "id": img.id,
                "filename": img.filename,
                "url": f"/api/images/products/{img.filename}",
                "thumbnail_url": f"/api/images/products/thumb_{img.filename}",
                "alt_text": img.alt_text,
            }
            for img in product_images
        ]
    return products


@app.post("/api/products", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.get("/api/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    # Add images to product
    product_images = (
        db.query(Image)
        .filter(
            Image.entity_type == "products",
            Image.entity_id == product.id,
            Image.is_active == True,
        )
        .all()
    )
    product.images = [
        {
            "id": img.id,
            "filename": img.filename,
            "url": f"/api/images/products/{img.filename}",
            "thumbnail_url": f"/api/images/products/thumb_{img.filename}",
            "alt_text": img.alt_text,
        }
        for img in product_images
    ]

    return product


@app.put("/api/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int, product: ProductCreate, db: Session = Depends(get_db)
):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    for key, value in product.dict().items():
        setattr(db_product, key, value)

    db.commit()
    db.refresh(db_product)
    return db_product


@app.delete("/api/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return {"message": "Product deleted"}


# Test route
@app.get("/api/test")
def test_endpoint():
    return {"message": "Test endpoint working"}


@app.get("/api/simple")
def simple_endpoint():
    return {"message": "Simple endpoint working"}


@app.get("/api/categories", response_model=List[CategoryResponse])
def get_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    categories = db.query(Category).offset(skip).limit(limit).all()
    return categories


@app.post("/api/categories", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    # Check if category name already exists
    existing_category = (
        db.query(Category).filter(Category.name == category.name).first()
    )
    if existing_category:
        raise HTTPException(status_code=400, detail="Category name already exists")

    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@app.get("/api/categories/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@app.put("/api/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int, category: CategoryCreate, db: Session = Depends(get_db)
):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    # Check if the new name conflicts with another category
    existing_category = (
        db.query(Category)
        .filter(Category.name == category.name, Category.id != category_id)
        .first()
    )
    if existing_category:
        raise HTTPException(status_code=400, detail="Category name already exists")

    for key, value in category.dict().items():
        setattr(db_category, key, value)

    db.commit()
    db.refresh(db_category)
    return db_category


@app.delete("/api/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(category)
    db.commit()
    return {"message": "Category deleted"}


@app.post("/api/upload")
def upload_file(file: UploadFile = File(...)):
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)

    file_path = upload_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"filename": file.filename, "url": f"/uploads/{file.filename}"}


# GraphQL placeholder (for compatibility)
@app.get("/graphql")
def graphql_placeholder():
    return {"message": "GraphQL endpoint - not implemented yet"}


@app.post("/graphql")
def graphql_placeholder_post():
    return {"message": "GraphQL endpoint - not implemented yet"}


# Admin Interface Routes
@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return templates.TemplateResponse(
        "admin.html",
        {"request": request, "products": products, "products_count": len(products)},
    )


@app.get("/admin/products", response_class=HTMLResponse)
def admin_products(
    request: Request, page: int = 1, per_page: int = 20, db: Session = Depends(get_db)
):
    # Ensure valid page and per_page values
    page = max(1, page)
    per_page = max(5, min(100, per_page))  # Between 5 and 100

    # Get total count for pagination
    total_products = db.query(Product).count()
    total_pages = (total_products + per_page - 1) // per_page

    # Ensure page doesn't exceed total pages
    page = min(page, max(1, total_pages))

    # Calculate offset
    offset = (page - 1) * per_page

    # Get paginated products
    products = db.query(Product).offset(offset).limit(per_page).all()

    return templates.TemplateResponse(
        "products.html",
        {
            "request": request,
            "products": products,
            "page": page,
            "per_page": per_page,
            "total_products": total_products,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages,
            "prev_page": page - 1,
            "next_page": page + 1,
        },
    )


@app.get("/admin/products/new", response_class=HTMLResponse)
def admin_new_product(request: Request):
    return templates.TemplateResponse(
        "product_form.html",
        {"request": request, "product": None, "action": "Create Product"},
    )


@app.post("/admin/products")
def create_product_admin(
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    category: str = Form(""),
    db: Session = Depends(get_db),
):
    db_product = Product(
        name=name, description=description, price=price, category=category
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return RedirectResponse(url="/admin/products", status_code=303)


@app.get("/admin/products/{product_id}/edit", response_class=HTMLResponse)
def admin_edit_product(
    product_id: int, request: Request, db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return templates.TemplateResponse(
        "product_form.html",
        {"request": request, "product": product, "action": "Update Product"},
    )


@app.post("/admin/products/{product_id}/edit")
def update_product_admin(
    product_id: int,
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    category: str = Form(""),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    product.name = name
    product.description = description
    product.price = price
    product.category = category

    db.commit()
    return RedirectResponse(url="/admin/products", status_code=303)


@app.post("/admin/products/{product_id}/delete")
def delete_product_admin(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return RedirectResponse(url="/admin/products", status_code=303)


# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy", "test": "added"}


# Populate database with sample products and categories
@app.post("/api/populate")
def populate_database():
    """Populate database with sample products and categories for demo"""
    db = SessionLocal()
    try:
        # Clear existing data
        db.query(Product).delete()
        db.query(Category).delete()

        # Sample categories
        categories_data = [
            Category(
                name="บุหรี่ไฟฟ้าทิ้ง",
                description="Starter Kit และ Cartridge หลากหลายรสชาติ เหมาะสำหรับผู้เริ่มต้น",
            ),
            Category(
                name="ระบบพอต", description="Pod ระบบปิดพร้อมรสชาติพรีเมียมและการใช้งานที่สะดวก"
            ),
            Category(name="โมดส์", description="อุปกรณ์สูบไอระดับพรีเมียมพร้อมคุณสมบัติขั้นสูง"),
            Category(name="น้ำยาสูบ", description="น้ำยาสูบไอหลากหลายรสชาติและความเข้มข้น"),
            Category(name="อุปกรณ์เสริม", description="อุปกรณ์และอะไหล่สำหรับการสูบไอ"),
            Category(name="ธีมเกม", description="สินค้าการสูบไอธีมเกมและตัวละครสุดพิเศษ"),
            Category(name="อื่นๆ", description="สินค้าอื่นๆที่เกี่ยวข้องกับการสูบไอ"),
        ]

        # Add categories first
        for category in categories_data:
            db.add(category)

        # Sample products
        products_data = [
            Product(
                name="Esko Switch Starter Kit",
                description="Starter Kit และ Cartridge หลากหลายรสชาติ",
                price=79.99,
                category="บุหรี่ไฟฟ้าทิ้ง",
            ),
            Product(
                name="Esko Switch Strawberry Ice",
                description="Cartridge รสสตรอเบอร์รี่เย็นฉ่ำ",
                price=19.99,
                category="บุหรี่ไฟฟ้าทิ้ง",
            ),
            Product(
                name="Esko Switch Blue Razz",
                description="Cartridge รสบลูราสเบอร์รี่",
                price=19.99,
                category="บุหรี่ไฟฟ้าทิ้ง",
            ),
            Product(
                name="Pikka Pod System",
                description="Pod ระบบปิดพร้อมรสชาติพรีเมียม",
                price=59.99,
                category="ระบบพอต",
            ),
            Product(
                name="Pikka Pod Mint",
                description="Pod รสมิ้นต์สดชื่น",
                price=14.99,
                category="ระบบพอต",
            ),
            Product(
                name="Pikka Pod Berry Blast",
                description="Pod รสเบอร์รี่รวม",
                price=14.99,
                category="ระบบพอต",
            ),
            Product(
                name="Vortex Pro Device",
                description="อุปกรณ์สูบไอระดับพรีเมียม",
                price=129.99,
                category="โมดส์",
            ),
            Product(
                name="Vortex Pro Tank",
                description="ถังสำหรับ Vortex Pro",
                price=39.99,
                category="โมดส์",
            ),
            Product(
                name="Game Theme Pod",
                description="Pod ธีมเกมสุดพิเศษ",
                price=49.99,
                category="ธีมเกม",
            ),
            Product(
                name="Premium Cleaning Kit",
                description="ชุดทำความสะอาดอุปกรณ์สูบไอ",
                price=15.99,
                category="อุปกรณ์เสริม",
            ),
        ]

        for product in products_data:
            db.add(product)

        db.commit()

        total_products = len(products_data)
        total_categories = len(categories_data)
        return {
            "message": f"Database populated with {total_categories} categories and {total_products} products",
            "categories_count": total_categories,
            "products_count": total_products,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to populate database: {str(e)}"
        )
    finally:
        db.close()


@app.post("/api/populate-categories")
def populate_categories():
    """Populate database with sample categories only"""
    db = SessionLocal()
    try:
        # Clear existing categories
        db.query(Category).delete()

        # Sample categories
        categories_data = [
            Category(
                name="บุหรี่ไฟฟ้าทิ้ง",
                description="Starter Kit และ Cartridge หลากหลายรสชาติ เหมาะสำหรับผู้เริ่มต้น",
            ),
            Category(
                name="ระบบพอต", description="Pod ระบบปิดพร้อมรสชาติพรีเมียมและการใช้งานที่สะดวก"
            ),
            Category(name="โมดส์", description="อุปกรณ์สูบไอระดับพรีเมียมพร้อมคุณสมบัติขั้นสูง"),
            Category(name="น้ำยาสูบ", description="น้ำยาสูบไอหลากหลายรสชาติและความเข้มข้น"),
            Category(name="อุปกรณ์เสริม", description="อุปกรณ์และอะไหล่สำหรับการสูบไอ"),
            Category(name="ธีมเกม", description="สินค้าการสูบไอธีมเกมและตัวละครสุดพิเศษ"),
            Category(name="อื่นๆ", description="สินค้าอื่นๆที่เกี่ยวข้องกับการสูบไอ"),
        ]

        # Add categories
        for category in categories_data:
            db.add(category)

        db.commit()

        total_categories = len(categories_data)
        return {
            "message": f"Database populated with {total_categories} categories",
            "categories_count": total_categories,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to populate categories: {str(e)}"
        )
    finally:
        db.close()


@app.get("/test-end")
def test_end():
    return {"status": "test working"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
