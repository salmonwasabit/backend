from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


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
    product = relationship("Product", back_populates="images", foreign_keys=[entity_id])

    def __repr__(self):
        return f"<Image(id={self.id}, filename='{self.filename}', entity_type='{self.entity_type}')>"
