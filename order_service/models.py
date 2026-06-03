from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


# ════════════════════════════════════════════════════════
# MODEL 1: Cart – Giỏ hàng
# ════════════════════════════════════════════════════════
class Cart(Base):
    __tablename__ = "cart"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=False)   # FK to auth_service
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("CartItem", back_populates="cart")


# ════════════════════════════════════════════════════════
# MODEL 2: CartItem – Chi tiết giỏ hàng
# ════════════════════════════════════════════════════════
class CartItem(Base):
    __tablename__ = "cart_item"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("cart.id"), nullable=False)
    book_id = Column(Integer, nullable=False)   # FK to book_service
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=True)   # price at time of add

    cart = relationship("Cart", back_populates="items")


# ════════════════════════════════════════════════════════
# MODEL 3: Order – Đơn hàng (UPGRADED for Assignment 06)
# ════════════════════════════════════════════════════════
class Order(Base):
    __tablename__ = "order"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=False)
    staff_id = Column(Integer, nullable=True)           # assigned staff
    coupon_code = Column(String(255), nullable=True)    # denormalized from marketing_service
    total_price = Column(Float, nullable=False)
    total_quantity = Column(Integer, nullable=False)
    status = Column(String(255), default="PENDING")     # PENDING | APPROVED | SHIPPING | COMPLETED | REJECTED | CANCELLED
    date = Column(DateTime, default=datetime.utcnow)
    note = Column(Text, nullable=True)

    # ── SAGA fields (Assignment 06) ───────────────────
    saga_status = Column(String(255), default="INITIATED")
    # INITIATED → PAYMENT_RESERVED → SHIPPING_RESERVED → CONFIRMED
    # or PAYMENT_FAILED | SHIPPING_FAILED | COMPENSATED (rollback)
    saga_step = Column(String(255), nullable=True)   # current saga step description
    saga_error = Column(Text, nullable=True)          # error message nếu có bước thất bại

    items    = relationship("OrderItem", back_populates="order")
    shipping = relationship("Shipping",  back_populates="order", uselist=False)
    payment  = relationship("Payment",   back_populates="order", uselist=False)
    refunds  = relationship("Refund",    back_populates="order")


# ════════════════════════════════════════════════════════
# MODEL 4: OrderItem – Chi tiết đơn hàng
# ════════════════════════════════════════════════════════
class OrderItem(Base):
    __tablename__ = "order_item"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("order.id"), nullable=False)
    book_id = Column(Integer, nullable=False)
    book_title = Column(String(255), nullable=True)     # snapshot tên sách lúc đặt hàng
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")


# ════════════════════════════════════════════════════════
# MODEL 5: Shipping – Thông tin vận chuyển
# ════════════════════════════════════════════════════════
class Shipping(Base):
    __tablename__ = "shipping"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("order.id"), nullable=False)
    method = Column(String(255), nullable=True)         # standard | fast | express
    fee = Column(Float, default=0)
    tracking_number = Column(String(255), nullable=True)
    status = Column(String(255), default="PENDING")
    shipped_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)

    order = relationship("Order", back_populates="shipping")


# ════════════════════════════════════════════════════════
# MODEL 6: Payment – Thanh toán
# ════════════════════════════════════════════════════════
class Payment(Base):
    __tablename__ = "payment"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("order.id"), nullable=False)
    method = Column(String(255), nullable=True)         # COD | credit_card | momo | bank_transfer
    status = Column(String(255), default="Pending")     # Pending | Paid | Failed | Refunded
    amount = Column(Float, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    transaction_id = Column(String(255), nullable=True)

    order = relationship("Order", back_populates="payment")


# ════════════════════════════════════════════════════════
# MODEL 7: Refund – Hoàn tiền
# ════════════════════════════════════════════════════════
class Refund(Base):
    __tablename__ = "refund"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("order.id"), nullable=False)
    amount = Column(Float, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(255), default="REQUESTED")   # REQUESTED | APPROVED | COMPLETED | REJECTED
    requested_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    order = relationship("Order", back_populates="refunds")
