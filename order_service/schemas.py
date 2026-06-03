from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CartItemCreate(BaseModel):
    product_id: int = Field(validation_alias="book_id", serialization_alias="product_id")
    quantity: int = 1
    unit_price: Optional[float] = None


class CartItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: int
    cart_id: int
    product_id: int = Field(validation_alias="book_id", serialization_alias="product_id")
    quantity: int
    unit_price: Optional[float]


class CartOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: int
    is_active: bool
    items: List[CartItemOut] = []


class CheckoutRequest(BaseModel):
    customer_id: int
    coupon_code: Optional[str] = None
    ship_method: str = "standard"
    pay_method: str = "COD"
    note: Optional[str] = None


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: int
    product_id: int = Field(validation_alias="book_id", serialization_alias="product_id")
    product_title: Optional[str] = Field(validation_alias="book_title", serialization_alias="product_title")
    price: float
    quantity: int


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: int
    staff_id: Optional[int]
    coupon_code: Optional[str]
    total_price: float
    total_quantity: int
    status: str
    date: datetime
    note: Optional[str]

class ShippingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_id: int
    method: Optional[str]
    fee: float
    tracking_number: Optional[str]
    status: str

class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_id: int
    method: Optional[str]
    status: str
    amount: Optional[float]

class RefundCreate(BaseModel):
    order_id: int
    amount: float
    reason: Optional[str] = None


class RefundOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_id: int
    amount: float
    reason: Optional[str]
    status: str
    requested_at: datetime

