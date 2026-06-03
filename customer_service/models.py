from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


# ════════════════════════════════════════════════════════
# MODEL 1: CustomerProfile – Hồ sơ khách hàng mở rộng
# ════════════════════════════════════════════════════════
class CustomerProfile(Base):
    """Thông tin chi tiết khách hàng (auth_service chỉ giữ login info)"""
    __tablename__ = "customer_profile"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, unique=True, nullable=False)  # FK to auth_service
    phone = Column(String(255), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    avatar_url = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    points = Column(Integer, default=0)             # loyalty points
    membership_tier = Column(String(255), default="Bronze")  # Bronze | Silver | Gold | Platinum
    created_at = Column(DateTime, default=datetime.utcnow)

    addresses = relationship("Address", back_populates="profile")


# ════════════════════════════════════════════════════════
# MODEL 2: Address – Địa chỉ giao hàng
# ════════════════════════════════════════════════════════
class Address(Base):
    __tablename__ = "address"

    id = Column(Integer, primary_key=True, index=True)
    customer_profile_id = Column(Integer, ForeignKey("customer_profile.id"), nullable=False)
    street = Column(String(255), nullable=False)
    city = Column(String(255), nullable=False)
    state = Column(String(255), nullable=True)
    zip_code = Column(String(255), nullable=True)
    country = Column(String(255), default="Vietnam")
    is_default = Column(Boolean, default=False)

    profile = relationship("CustomerProfile", back_populates="addresses")


# ════════════════════════════════════════════════════════
# MODEL 3: Wishlist – Danh sách yêu thích
# ════════════════════════════════════════════════════════
class Wishlist(Base):
    __tablename__ = "wishlist"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("WishlistItem", back_populates="wishlist")


# ════════════════════════════════════════════════════════
# MODEL 4: WishlistItem – Mục trong Wishlist
# ════════════════════════════════════════════════════════
class WishlistItem(Base):
    __tablename__ = "wishlist_item"

    id = Column(Integer, primary_key=True, index=True)
    wishlist_id = Column(Integer, ForeignKey("wishlist.id"), nullable=False)
    book_id = Column(Integer, nullable=False)        # FK to book_service
    added_at = Column(DateTime, default=datetime.utcnow)

    wishlist = relationship("Wishlist", back_populates="items")


# ════════════════════════════════════════════════════════
# MODEL 5: Newsletter – Đăng ký nhận bản tin
# ════════════════════════════════════════════════════════
class Newsletter(Base):
    __tablename__ = "newsletter"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    customer_id = Column(Integer, nullable=True)     # optional, for logged-in users
    is_subscribed = Column(Boolean, default=True)
    subscribed_at = Column(DateTime, default=datetime.utcnow)
    unsubscribed_at = Column(DateTime, nullable=True)


# ════════════════════════════════════════════════════════
# MODEL 6: CustomerPreference – Sở thích đọc sách
# (thêm mới để đủ 50 model toàn hệ thống)
# ════════════════════════════════════════════════════════
class CustomerPreference(Base):
    """Sở thích đọc sách của khách hàng (genre, ngôn ngữ, tác giả yêu thích)"""
    __tablename__ = "customer_preference"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, unique=True, nullable=False)
    favorite_genres = Column(String(255), nullable=True)   # comma-separated genre IDs
    favorite_authors = Column(String(255), nullable=True)  # comma-separated author IDs
    preferred_language = Column(String(255), nullable=True)
    preferred_format = Column(String(255), nullable=True)  # paperback | ebook | audio
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
