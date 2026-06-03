from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProfileCreate(BaseModel):
    customer_id: int
    phone: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: int
    phone: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    points: int
    membership_tier: str
class AddressCreate(BaseModel):
    customer_profile_id: int
    street: str
    city: str
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: str = "Vietnam"
    is_default: bool = False


class AddressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_profile_id: int
    street: str
    city: str
    state: Optional[str]
    zip_code: Optional[str]
    country: str
    is_default: bool
class WishlistItemCreate(BaseModel):
    product_id: int = Field(validation_alias="book_id", serialization_alias="product_id")


class WishlistItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: int
    product_id: int = Field(validation_alias="book_id", serialization_alias="product_id")
    added_at: datetime


class WishlistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: int
    items: List[WishlistItemOut] = []


class NewsletterCreate(BaseModel):
    email: str
    customer_id: Optional[int] = None


class NewsletterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    is_subscribed: bool


class PreferenceCreate(BaseModel):
    customer_id: int
    favorite_genres: Optional[str] = None
    favorite_authors: Optional[str] = None
    preferred_language: Optional[str] = None
    preferred_format: Optional[str] = None


class PreferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: int
    favorite_genres: Optional[str]
    favorite_authors: Optional[str]
    preferred_language: Optional[str]
    preferred_format: Optional[str]
