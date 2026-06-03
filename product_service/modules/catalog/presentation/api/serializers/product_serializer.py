from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, ConfigDict

class ProductBase(BaseModel):
    name: str
    sku: str
    description: str | None = None
    price: float
    stock_quantity: int = 0
    image_url: str | None = None
    category_id: int | None = None
    brand_id: int | None = None
    product_type_id: int | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: str | None = None
    sku: str | None = None
    description: str | None = None
    price: float | None = None
    stock_quantity: int | None = None
    image_url: str | None = None
    category_id: int | None = None
    brand_id: int | None = None
    product_type_id: int | None = None
    attributes: dict[str, Any] | None = None
    is_active: bool | None = None

class ProductOut(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    category_name: str | None = None
    brand_name: str | None = None
    product_type_name: str | None = None
    rating_avg: float = 0
    rating_count: int = 0
    title: str | None = None
    cover_image_url: str | None = None
    author_name: str | None = None
    language: str | None = None

class CategoryCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    parent_id: int | None = None

class CategoryOut(CategoryCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int

class BrandCreate(BaseModel):
    name: str
    slug: str

class BrandOut(BrandCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int

class ProductTypeCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None

class ProductTypeOut(ProductTypeCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int

class RatingCreate(BaseModel):
    product_id: int
    customer_id: int
    score: float

class RatingOut(RatingCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

class ProductReviewCreate(BaseModel):
    product_id: int
    customer_id: int
    title: str | None = None
    body: str

class ProductReviewOut(ProductReviewCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_approved: bool
    created_at: datetime
