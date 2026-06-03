import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, text
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:Duyanh090%40@mysql:3306/analytics_db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
app = FastAPI(title="Analytics Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ════════ MODELS ════════════════════════════════════════

# MODEL 1: DailySalesSummary – Thống kê doanh thu ngày
class DailySalesSummary(Base):
    __tablename__ = "daily_sales_summary"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False)
    total_orders = Column(Integer, default=0)
    total_revenue = Column(Float, default=0)
    total_items_sold = Column(Integer, default=0)
    new_customers = Column(Integer, default=0)


# MODEL 2: UserSearchHistory – Lịch sử tìm kiếm
class UserSearchHistory(Base):
    __tablename__ = "user_search_history"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=True)   # null = guest search
    query = Column(String(255), nullable=False)
    results_count = Column(Integer, nullable=True)
    searched_at = Column(DateTime, default=datetime.utcnow)


# MODEL 3: RecentlyViewed – Xem gần đây
class RecentlyViewed(Base):
    __tablename__ = "recently_viewed"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=False)
    product_id = Column(Integer, nullable=False)
    viewed_at = Column(DateTime, default=datetime.utcnow)


# ══ Schemas ════════════════════════════════════════════
class SalesCreate(BaseModel):
    date: date; total_orders: int = 0; total_revenue: float = 0
    total_items_sold: int = 0; new_customers: int = 0


class SalesOut(BaseModel):
    id: int; date: date; total_orders: int; total_revenue: float; total_items_sold: int
    class Config: from_attributes = True


class SearchLogCreate(BaseModel):
    customer_id: Optional[int] = None; query: str; results_count: Optional[int] = None


class SearchLogOut(BaseModel):
    id: int; customer_id: Optional[int]; query: str; results_count: Optional[int]; searched_at: datetime
    class Config: from_attributes = True


class RecentlyViewedCreate(BaseModel):
    customer_id: int
    product_id: int


class RecentlyViewedOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: int
    customer_id: int
    product_id: int
    viewed_at: datetime


@app.get("/health")
def health():
    return {"status": "ok", "service": "analytics_service", "timestamp": datetime.utcnow().isoformat()}

# ══ Startup ════════════════════════════════════════════
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


@app.on_event("startup")
def startup():
    wait_for_db()
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()


# ════════ ROUTES ════════════════════════════════════════

@app.post("/sales", response_model=SalesOut, status_code=201)
def upsert_daily_sales(body: SalesCreate, db: Session = Depends(get_db)):
    existing = db.query(DailySalesSummary).filter(DailySalesSummary.date == body.date).first()
    if existing:
        existing.total_orders += body.total_orders
        existing.total_revenue += body.total_revenue
        existing.total_items_sold += body.total_items_sold
        db.commit(); db.refresh(existing); return existing
    s = DailySalesSummary(**body.model_dump()); db.add(s); db.commit(); db.refresh(s); return s


@app.get("/sales", response_model=List[SalesOut])
def list_sales(limit: int = 30, db: Session = Depends(get_db)):
    return db.query(DailySalesSummary).order_by(DailySalesSummary.date.desc()).limit(limit).all()


@app.get("/sales/summary")
def summary(db: Session = Depends(get_db)):
    all_sales = db.query(DailySalesSummary).all()
    return {
        "total_revenue": sum(s.total_revenue for s in all_sales),
        "total_orders": sum(s.total_orders for s in all_sales),
        "total_items_sold": sum(s.total_items_sold for s in all_sales),
    }


@app.post("/search-history", response_model=SearchLogOut, status_code=201)
def log_search(body: SearchLogCreate, db: Session = Depends(get_db)):
    sh = UserSearchHistory(**body.model_dump()); db.add(sh); db.commit(); db.refresh(sh); return sh


@app.get("/search-history", response_model=List[SearchLogOut])
def list_searches(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(UserSearchHistory).order_by(UserSearchHistory.searched_at.desc()).limit(limit).all()


@app.post("/recently-viewed", response_model=RecentlyViewedOut, status_code=201)
def log_view(body: RecentlyViewedCreate, db: Session = Depends(get_db)):
    # Remove old entry for same book if exists (update viewed_at)
    old = db.query(RecentlyViewed).filter(
        RecentlyViewed.customer_id == body.customer_id,
        RecentlyViewed.product_id == body.product_id
    ).first()
    if old: db.delete(old)
    rv = RecentlyViewed(customer_id=body.customer_id, product_id=body.product_id); db.add(rv); db.commit(); db.refresh(rv); return rv


@app.get("/recently-viewed/{customer_id}", response_model=List[RecentlyViewedOut])
def get_recently_viewed(customer_id: int, limit: int = 20, db: Session = Depends(get_db)):
    return db.query(RecentlyViewed).filter(
        RecentlyViewed.customer_id == customer_id
    ).order_by(RecentlyViewed.viewed_at.desc()).limit(limit).all()
