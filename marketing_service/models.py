from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Table
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

# ── Junction: Bundle ↔ Book (many-to-many) ──────────────
bundle_product = Table(
    "bundle_product", Base.metadata,
    Column("bundle_id", Integer, ForeignKey("bundle.id"), primary_key=True),
    Column("product_id", Integer, primary_key=True),
)


# ════════════════════════════════════════════════════════
# MODEL 1: Coupon – Mã giảm giá
# ════════════════════════════════════════════════════════
class Coupon(Base):
    __tablename__ = "coupon"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(255), unique=True, nullable=False)
    discount_percent = Column(Float, nullable=True)
    discount_amount = Column(Float, nullable=True)
    min_order_value = Column(Float, default=0)
    max_uses = Column(Integer, nullable=True)
    used_count = Column(Integer, default=0)
    valid_from = Column(DateTime, nullable=True)
    valid_to = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)


# ════════════════════════════════════════════════════════
# MODEL 2: Promotion – Chương trình khuyến mãi
# ════════════════════════════════════════════════════════
class Promotion(Base):
    __tablename__ = "promotion"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    discount_percent = Column(Float, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)


# ════════════════════════════════════════════════════════
# MODEL 3: Bundle – Combo sách
# ════════════════════════════════════════════════════════
class Bundle(Base):
    __tablename__ = "bundle"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)


# ════════════════════════════════════════════════════════
# MODEL 4: MembershipTier – Hạng thành viên
# ════════════════════════════════════════════════════════
class MembershipTier(Base):
    __tablename__ = "membership_tier"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)    # Bronze | Silver | Gold | Platinum
    min_points = Column(Integer, nullable=False)
    discount_percent = Column(Float, default=0)
    free_shipping = Column(Boolean, default=False)
    description = Column(Text, nullable=True)


# ════════════════════════════════════════════════════════
# MODEL 5: Discount – Giảm giá theo sách/category
# ════════════════════════════════════════════════════════
class Discount(Base):
    __tablename__ = "discount"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    product_id = Column(Integer, nullable=True)       # FK to product_service (nullable = category discount)
    genre_id = Column(Integer, nullable=True)
    discount_percent = Column(Float, nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)


# ════════════════════════════════════════════════════════
# MODEL 6: FlashSale – Flash sale (thêm mới)
# ════════════════════════════════════════════════════════
class FlashSale(Base):
    """Flash sale giới hạn thời gian và số lượng"""
    __tablename__ = "flash_sale"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    discount_percent = Column(Float, nullable=False)
    max_quantity = Column(Integer, nullable=True)
    sold_quantity = Column(Integer, default=0)
    start_at = Column(DateTime, nullable=False)
    end_at = Column(DateTime, nullable=False)
    product_id = Column(Integer, nullable=True)   # FK to product_service
    is_active = Column(Boolean, default=True)


# ════════════════════════════════════════════════════════
# MODEL 7: ReferralCode – Referral / giới thiệu bạn bè
# (thêm mới để đủ 50 model)
# ════════════════════════════════════════════════════════
class ReferralCode(Base):
    """Mã giới thiệu bạn bè – thưởng điểm khi bạn đăng ký"""
    __tablename__ = "referral_code"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(255), unique=True, nullable=False)
    owner_customer_id = Column(Integer, nullable=False)  # FK to auth_service
    reward_points = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    used_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
