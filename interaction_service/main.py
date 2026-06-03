import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:Duyanh090%40@mysql:3306/interaction_db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
app = FastAPI(title="Interaction Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ════════ MODELS ════════════════════════════════════════

# MODEL 1: GiftCard – Thẻ quà tặng
class GiftCard(Base):
    __tablename__ = "gift_card"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(255), unique=True, nullable=False)
    initial_balance = Column(Float, nullable=False)
    current_balance = Column(Float, nullable=False)
    active = Column(Boolean, default=True)
    buyer_customer_id = Column(Integer, nullable=True)
    recipient_email = Column(String(255), nullable=True)
    message = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# MODEL 2: Subscription – Gói đăng ký đọc sách
class Subscription(Base):
    __tablename__ = "subscription"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=False)
    plan_name = Column(String(255), nullable=False)   # Basic | Super Reader
    price = Column(Float, nullable=False)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    auto_renew = Column(Boolean, default=True)


# MODEL 3: LoyaltyPoint – Giao dịch điểm tích lũy (thêm mới)
class LoyaltyPoint(Base):
    """Lịch sử giao dịch điểm tích lũy của khách hàng"""
    __tablename__ = "loyalty_point"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=False)
    points = Column(Integer, nullable=False)       # positive = earned, negative = redeemed
    reason = Column(String(255), nullable=True)          # "purchase", "referral", "review", "redeem"
    reference_id = Column(Integer, nullable=True)   # order_id or other reference
    balance_after = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ══ Schemas ════════════════════════════════════════════
class GiftCardCreate(BaseModel):
    amount: float
    buyer_customer_id: Optional[int] = None
    recipient_email: Optional[str] = None
    message: Optional[str] = None


class GiftCardOut(BaseModel):
    id: int; code: str; initial_balance: float; current_balance: float; active: bool
    class Config: from_attributes = True


class SubscriptionCreate(BaseModel):
    customer_id: int
    plan_name: str
    price: float
    auto_renew: bool = True


class SubscriptionOut(BaseModel):
    id: int; customer_id: int; plan_name: str; price: float; is_active: bool; auto_renew: bool
    class Config: from_attributes = True


class LoyaltyPointCreate(BaseModel):
    customer_id: int; points: int; reason: Optional[str] = None
    reference_id: Optional[int] = None; balance_after: int


class LoyaltyPointOut(BaseModel):
    id: int; customer_id: int; points: int; reason: Optional[str]; balance_after: int; created_at: datetime
    class Config: from_attributes = True


# ══ Startup ════════════════════════════════════════════
def wait_for_db(retries: int = 30, delay: int = 2):
    import time
    last_error = None
    for _ in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception as exc:
            last_error = exc
            time.sleep(delay)
    if last_error:
        raise last_error

@app.on_event("startup")
def startup():
    wait_for_db()
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok", "service": "interaction_service", "timestamp": datetime.utcnow().isoformat()}


def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()


# ════════ ROUTES ════════════════════════════════════════

@app.post("/gift-cards", response_model=GiftCardOut, status_code=201)
def buy_gift_card(body: GiftCardCreate, db: Session = Depends(get_db)):
    code = str(uuid.uuid4()).replace("-", "").upper()[:12]
    gc = GiftCard(
        code=code, initial_balance=body.amount, current_balance=body.amount,
        buyer_customer_id=body.buyer_customer_id, recipient_email=body.recipient_email,
        message=body.message
    )
    db.add(gc); db.commit(); db.refresh(gc); return gc


@app.get("/gift-cards/{code}", response_model=GiftCardOut)
def get_gift_card(code: str, db: Session = Depends(get_db)):
    gc = db.query(GiftCard).filter(GiftCard.code == code.upper()).first()
    if not gc: raise HTTPException(404, "Không tìm thấy thẻ quà tặng")
    return gc


@app.patch("/gift-cards/{code}/redeem")
def redeem_gift_card(code: str, amount: float, db: Session = Depends(get_db)):
    gc = db.query(GiftCard).filter(GiftCard.code == code.upper(), GiftCard.active == True).first()
    if not gc: raise HTTPException(404, "Thẻ không hợp lệ hoặc đã hết hạn")
    if gc.current_balance < amount: raise HTTPException(400, "Số dư không đủ")
    gc.current_balance -= amount
    if gc.current_balance == 0: gc.active = False
    db.commit()
    return {"code": code, "redeemed": amount, "remaining": gc.current_balance}


@app.post("/subscriptions", response_model=SubscriptionOut, status_code=201)
def create_subscription(body: SubscriptionCreate, db: Session = Depends(get_db)):
    sub = Subscription(**body.model_dump()); db.add(sub); db.commit(); db.refresh(sub); return sub


@app.get("/subscriptions/{customer_id}", response_model=SubscriptionOut)
def get_subscription(customer_id: int, db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(
        Subscription.customer_id == customer_id, Subscription.is_active == True
    ).first()
    if not sub: raise HTTPException(404, "Không có gói đăng ký nào")
    return sub


@app.post("/loyalty-points", response_model=LoyaltyPointOut, status_code=201)
def add_points(body: LoyaltyPointCreate, db: Session = Depends(get_db)):
    lp = LoyaltyPoint(**body.model_dump()); db.add(lp); db.commit(); db.refresh(lp); return lp


@app.get("/loyalty-points/{customer_id}", response_model=List[LoyaltyPointOut])
def get_loyalty_history(customer_id: int, db: Session = Depends(get_db)):
    return db.query(LoyaltyPoint).filter(
        LoyaltyPoint.customer_id == customer_id
    ).order_by(LoyaltyPoint.created_at.desc()).all()
