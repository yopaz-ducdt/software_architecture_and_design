from datetime import datetime
from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base
class CategoryModel(Base):
    __tablename__ = 'catalog_category'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey('catalog_category.id'))
    parent = relationship('CategoryModel', remote_side=[id])
class BrandModel(Base):
    __tablename__ = 'catalog_brand'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
class ProductTypeModel(Base):
    __tablename__ = 'catalog_product_type'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
class ProductModel(Base):
    __tablename__ = 'catalog_product'
    __table_args__ = (UniqueConstraint('sku', name='uq_product_sku'),)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    sku = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, default=0)
    image_url = Column(String(500))
    attributes = Column(JSON, nullable=False, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    category_id = Column(Integer, ForeignKey('catalog_category.id'))
    brand_id = Column(Integer, ForeignKey('catalog_brand.id'))
    product_type_id = Column(Integer, ForeignKey('catalog_product_type.id'))
    category = relationship('CategoryModel'); brand = relationship('BrandModel'); product_type = relationship('ProductTypeModel')
    ratings = relationship('RatingModel', back_populates='product', cascade='all, delete-orphan')
    reviews = relationship('ProductReviewModel', back_populates='product', cascade='all, delete-orphan')
class RatingModel(Base):
    __tablename__ = 'catalog_rating'
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('catalog_product.id'), nullable=False)
    customer_id = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    product = relationship('ProductModel', back_populates='ratings')
class ProductReviewModel(Base):
    __tablename__ = 'catalog_product_review'
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('catalog_product.id'), nullable=False)
    customer_id = Column(Integer, nullable=False)
    title = Column(String(255))
    body = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    product = relationship('ProductModel', back_populates='reviews')
