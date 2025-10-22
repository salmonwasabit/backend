from dotenv import load_dotenv
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict
import time
import secrets
load_dotenv()
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import List, Optional
import uvicorn
import os
from pathlib import Path
import shutil
from datetime import datetime
import time
from sqlalchemy.exc import OperationalError

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://vape_user:vape_password@localhost:5432/vape_cms")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
# Authentication configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")
# Rate limiting
login_attempts = defaultdict(list)
MAX_LOGIN_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 300  # 5 minutes

def check_rate_limit(identifier: str) -> bool:
    """Check if the identifier has exceeded rate limits"""
    now = time.time()
    attempts = login_attempts[identifier]
    
    # Remove old attempts outside the window
    attempts[:] = [t for t in attempts if now - t < LOGIN_WINDOW_SECONDS]
    
    return len(attempts) < MAX_LOGIN_ATTEMPTS

def record_login_attempt(identifier: str):
    """Record a login attempt"""
    now = time.time()
    login_attempts[identifier].append(now)

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

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None

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
    username = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True

class Media(Base):
    __tablename__ = "media"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    mime_type = Column(String)
    size = Column(Integer)
    url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ProductImage(Base):
    __tablename__ = "product_images"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    media_id = Column(Integer, ForeignKey("media.id"))
    product = relationship("Product")
    media = relationship("Media")

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
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

create_tables_with_retry()

# Pydantic models
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

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

# FastAPI app
app = FastAPI(title="Vape CMS API", version="1.0.0")

# Test route - moved to right after app creation
@app.get("/test123")
def test123():
    return {"message": "Test123 working"}

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],  # In production, specify your domain
)

# Security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self';"
    return response

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Templates
templates = Jinja2Templates(directory="templates")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# API Routes
# Authentication routes
@app.post("/api/auth/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.username == user_credentials.username).first()

    if not user or not verify_password(user_credentials.password, user.hashed_password):

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



@app.post("/api/auth/register", response_model=UserResponse)

async def register(user: UserCreate, db: Session = Depends(get_db)):

    # Check if user already exists

    db_user = db.query(User).filter(

        (User.username == user.username) | (User.email == user.email)

    ).first()

    if db_user:

        raise HTTPException(status_code=400, detail="Username or email already registered")

    

    # Hash password and create user

    hashed_password = get_password_hash(user.password)

    db_user = User(

        username=user.username,

        email=user.email,

        hashed_password=hashed_password

    )

    db.add(db_user)

    db.commit()

    db.refresh(db_user)

    return db_user



async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):

    credentials_exception = HTTPException(

        status_code=401,

        detail="Could not validate credentials",

        headers={"WWW-Authenticate": "Bearer"},

    )

    username = verify_token(token)

    if username is None:

        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()

    if user is None:

        raise credentials_exception

    return user



@app.get("/api/auth/me", response_model=UserResponse)

async def read_users_me(current_user: User = Depends(get_current_user)):

    return current_user


@app.get("/api/test2")
def get_test2():
    return {"message": "Test2 working"}

@app.get("/api/products", response_model=List[ProductResponse])
def get_products(skip: int = 0, limit: int = 100,
                 db: Session = Depends(get_db)):
    products = db.query(Product).offset(skip).limit(limit).all()
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
    return product


@app.put("/api/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product: ProductCreate,
                   db: Session = Depends(get_db)):
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
    existing_category = db.query(Category).filter(Category.name == category.name).first()
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
def update_category(category_id: int, category: CategoryCreate,
                   db: Session = Depends(get_db)):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    # Check if the new name conflicts with another category
    existing_category = db.query(Category).filter(
        Category.name == category.name,
        Category.id != category_id
    ).first()
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
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "products": products,
        "products_count": len(products)
    })


@app.get("/admin/products", response_class=HTMLResponse)
def admin_products(request: Request, db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return templates.TemplateResponse("products.html", {
        "request": request,
        "products": products
    })


@app.get("/admin/products/new", response_class=HTMLResponse)
def admin_new_product(request: Request):
    return templates.TemplateResponse("product_form.html", {
        "request": request,
        "product": None,
        "action": "Create Product"
    })


@app.post("/admin/products")
def create_product_admin(
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    category: str = Form(""),
    db: Session = Depends(get_db)
):
    db_product = Product(
        name=name,
        description=description,
        price=price,
        category=category
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return RedirectResponse(url="/admin/products", status_code=303)


@app.get("/admin/products/{product_id}/edit", response_class=HTMLResponse)
def admin_edit_product(product_id: int, request: Request, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return templates.TemplateResponse("product_form.html", {
        "request": request,
        "product": product,
        "action": "Update Product"
    })


@app.post("/admin/products/{product_id}/edit")
def update_product_admin(
    product_id: int,
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    category: str = Form(""),
    db: Session = Depends(get_db)
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

@app.get("/test-end")
def test_end():
    return {"status": "test working"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
