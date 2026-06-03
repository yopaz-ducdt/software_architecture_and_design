from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


# ═══════════════════════════════════════════════════════
# MODEL 1: Customer
# ═══════════════════════════════════════════════════════
class Customer(Base):
    """Khách hàng của cửa hàng sách"""
    __tablename__ = "customer"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)  # hashed
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tokens = relationship("RefreshToken", back_populates="customer")


# ═══════════════════════════════════════════════════════
# MODEL 2: Staff
# ═══════════════════════════════════════════════════════
class Staff(Base):
    """Nhân viên / Quản trị viên"""
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    username = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)  # hashed
    role = Column(String(255), default="staff")      # staff | admin | manager
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tokens = relationship("RefreshToken", back_populates="staff")


# ═══════════════════════════════════════════════════════
# MODEL 3: RefreshToken
# ═══════════════════════════════════════════════════════
class RefreshToken(Base):
    """Lưu refresh token để revoke khi logout"""
    __tablename__ = "refresh_token"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), unique=True, nullable=False)
    user_type = Column(String(255), nullable=False)   # "customer" | "staff"
    customer_id = Column(Integer, ForeignKey("customer.id"), nullable=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="tokens")
    staff = relationship("Staff", back_populates="tokens")
