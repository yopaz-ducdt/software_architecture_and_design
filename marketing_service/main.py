import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from models import Base, Coupon, Promotion, Bundle, MembershipTier, Discount, FlashSale, ReferralCode
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
import uuid

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:Duyanh090%40@mysql:3306/marketing_db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def wait_for_db(retries: int = 30, delay: int = 2):
    last_error = None
    for _ in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception as exc:
            last_error = exc
            import time
            time.sleep(delay)
    if last_error:
        raise last_error


app = FastAPI(title="Marketing Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    wait_for_db()
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok", "service": "marketing_service", "timestamp": datetime.utcnow().isoformat()}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Schemas ──────────────────────────────────────────────
class CouponCreate(BaseModel):
    code: str
    discount_percent: Optional[float] = None
    discount_amount: Optional[float] = None
    min_order_value: float = 0
    max_uses: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None


class CouponOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    discount_percent: Optional[float]
    discount_amount: Optional[float]
    min_order_value: float
    used_count: int
    active: bool
class PromotionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    discount_percent: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class PromotionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: Optional[str]
    discount_percent: Optional[float]
    is_active: bool
class MembershipTierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    min_points: int
    discount_percent: float
    free_shipping: bool
class FlashSaleCreate(BaseModel):
    name: str
    discount_percent: float
    max_quantity: Optional[int] = None
    start_at: datetime
    end_at: datetime
    product_id: Optional[int] = None


class FlashSaleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    discount_percent: float
    max_quantity: Optional[int]
    sold_quantity: int
    start_at: datetime
    end_at: datetime
    product_id: Optional[int]
    is_active: bool


class ReferralCodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    owner_customer_id: int
    reward_points: int
    used_count: int


# ════════════════════════════════════════════════════════
# COUPON
# ════════════════════════════════════════════════════════
@app.post("/coupons", response_model=CouponOut, status_code=201)
def create_coupon(body: CouponCreate, db: Session = Depends(get_db)):
    coupon = Coupon(**body.model_dump())
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


@app.get("/coupons", response_model=List[CouponOut])
def list_coupons(db: Session = Depends(get_db)):
    return db.query(Coupon).filter(Coupon.active == True).all()


@app.get("/coupons/validate/{code}")
def validate_coupon(code: str, order_total: float = 0, db: Session = Depends(get_db)):
    """Xác minh mã coupon – gọi bởi order_service"""
    coupon = db.query(Coupon).filter(Coupon.code == code.upper(), Coupon.active == True).first()
    if not coupon:
        raise HTTPException(404, "Mã giảm giá không hợp lệ hoặc đã hết hạn")
    if coupon.valid_to and coupon.valid_to < datetime.utcnow():
        raise HTTPException(400, "Mã giảm giá đã hết hạn")
    if order_total < coupon.min_order_value:
        raise HTTPException(400, f"Đơn hàng phải tối thiểu {coupon.min_order_value}")
    discount = 0
    if coupon.discount_percent:
        discount = order_total * coupon.discount_percent / 100
    elif coupon.discount_amount:
        discount = coupon.discount_amount
    return {"valid": True, "discount": discount, "coupon": CouponOut.model_validate(coupon)}


# ════════════════════════════════════════════════════════
# PROMOTION
# ════════════════════════════════════════════════════════
@app.post("/promotions", response_model=PromotionOut, status_code=201)
def create_promotion(body: PromotionCreate, db: Session = Depends(get_db)):
    promo = Promotion(**body.model_dump())
    db.add(promo)
    db.commit()
    db.refresh(promo)
    return promo


@app.get("/promotions", response_model=List[PromotionOut])
def list_promotions(db: Session = Depends(get_db)):
    return db.query(Promotion).filter(Promotion.is_active == True).all()


# ════════════════════════════════════════════════════════
# MEMBERSHIP TIER
# ════════════════════════════════════════════════════════
@app.get("/tiers", response_model=List[MembershipTierOut])
def list_tiers(db: Session = Depends(get_db)):
    return db.query(MembershipTier).all()


@app.post("/tiers/seed")
def seed_tiers(db: Session = Depends(get_db)):
    """Tạo sẵn 4 hạng thành viên"""
    tiers = [
        {"name": "Bronze",   "min_points": 0,    "discount_percent": 0,   "free_shipping": False},
        {"name": "Silver",   "min_points": 500,  "discount_percent": 3,   "free_shipping": False},
        {"name": "Gold",     "min_points": 2000, "discount_percent": 5,   "free_shipping": True},
        {"name": "Platinum", "min_points": 5000, "discount_percent": 10,  "free_shipping": True},
    ]
    for t in tiers:
        if not db.query(MembershipTier).filter(MembershipTier.name == t["name"]).first():
            db.add(MembershipTier(**t))
    db.commit()
    return {"message": "Đã tạo 4 hạng thành viên"}


# ════════════════════════════════════════════════════════
# FLASH SALE
# ════════════════════════════════════════════════════════
@app.post("/flash-sales", response_model=FlashSaleOut, status_code=201)
def create_flash_sale(body: FlashSaleCreate, db: Session = Depends(get_db)):
    fs = FlashSale(**body.model_dump())
    db.add(fs)
    db.commit()
    db.refresh(fs)
    return fs


@app.get("/flash-sales", response_model=List[FlashSaleOut])
def list_flash_sales(db: Session = Depends(get_db)):
    return db.query(FlashSale).filter(FlashSale.is_active == True).all()


# ════════════════════════════════════════════════════════
# REFERRAL CODE
# ════════════════════════════════════════════════════════
@app.post("/referrals/{customer_id}", response_model=ReferralCodeOut, status_code=201)
def generate_referral(customer_id: int, db: Session = Depends(get_db)):
    """Tạo mã giới thiệu cho khách hàng"""
    existing = db.query(ReferralCode).filter(
        ReferralCode.owner_customer_id == customer_id,
        ReferralCode.is_active == True
    ).first()
    if existing:
        return existing
    code = str(uuid.uuid4()).replace("-", "")[:8].upper()
    ref = ReferralCode(code=code, owner_customer_id=customer_id)
    db.add(ref)
    db.commit()
    db.refresh(ref)
    return ref


@app.get("/referrals/{customer_id}", response_model=ReferralCodeOut)
def get_referral(customer_id: int, db: Session = Depends(get_db)):
    ref = db.query(ReferralCode).filter(ReferralCode.owner_customer_id == customer_id).first()
    if not ref:
        raise HTTPException(404, "Chưa có mã giới thiệu")
    return ref
