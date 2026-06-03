import os
from collections import Counter
from datetime import datetime
from typing import Any, Optional

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text, create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from graph_sync import BehaviorGraphSync

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:Duyanh090%40@mysql:3306/behavior_db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="Behavior Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
graph_sync = BehaviorGraphSync()


class BehaviorEvent(Base):
    __tablename__ = "behavior_event"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    product_id = Column(Integer, nullable=True, index=True)
    category_name = Column(String(255), nullable=True, index=True)
    source = Column(String(100), nullable=True)
    query = Column(String(255), nullable=True)
    price = Column(Float, nullable=True)
    quantity = Column(Integer, nullable=True)
    event_metadata = Column("metadata", JSON, nullable=True)
    occurred_at = Column(DateTime, default=datetime.utcnow, index=True)


class CustomerBehaviorProfile(Base):
    __tablename__ = "customer_behavior_profile"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, unique=True, nullable=False, index=True)
    persona = Column(String(100), default="new_explorer")
    price_sensitivity = Column(String(50), default="medium")
    purchase_intent = Column(Float, default=0.1)
    next_best_action = Column(String(100), default="recommend_entry_products")
    preferred_categories = Column(JSON, nullable=False, default=list)
    feature_values = Column(JSON, nullable=False, default=dict)
    summary = Column(Text, nullable=True)
    last_event_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BehaviorEventCreate(BaseModel):
    customer_id: int
    event_type: str
    product_id: Optional[int] = Field(default=None, validation_alias="book_id", serialization_alias="product_id")
    category_name: Optional[str] = None
    source: Optional[str] = None
    query: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = 1
    event_metadata: Optional[dict[str, Any]] = Field(default=None, alias="metadata")
    occurred_at: Optional[datetime] = None


class BehaviorEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: int
    customer_id: int
    event_type: str
    product_id: Optional[int]
    category_name: Optional[str]
    source: Optional[str]
    query: Optional[str]
    price: Optional[float]
    quantity: Optional[int]
    event_metadata: Optional[dict[str, Any]] = Field(default=None, serialization_alias="metadata")
    occurred_at: datetime


class BehaviorProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    customer_id: int
    persona: str
    price_sensitivity: str
    purchase_intent: float
    next_best_action: str
    preferred_categories: list[str]
    feature_values: dict[str, Any]
    summary: Optional[str]
    last_event_at: Optional[datetime]
    updated_at: datetime


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
    graph_sync.ensure_ready()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _compute_profile(events: list[BehaviorEvent]) -> dict[str, Any]:
    category_counter: Counter[str] = Counter()
    search_count = 0
    view_count = 0
    wishlist_count = 0
    cart_item_count = 0
    order_count = 0
    total_spent = 0.0
    promo_keyword_count = 0
    last_event_at = events[-1].occurred_at if events else None

    for event in events:
        if event.category_name:
            if event.event_type in {"product_viewed", "recent_view", "product_clicked_from_listing"}:
                category_counter[event.category_name] += 2
            elif event.event_type in {"wishlist_added", "wishlist_toggled"}:
                category_counter[event.category_name] += 3
            elif event.event_type in {"cart_added", "checkout_started"}:
                category_counter[event.category_name] += 4
            elif event.event_type in {"order_completed", "order_item"}:
                category_counter[event.category_name] += max(1, event.quantity or 1)

        if event.event_type in {"search_performed", "search"}:
            search_count += 1
            query = (event.query or "").lower()
            if any(keyword in query for keyword in ["sale", "giảm", "voucher", "coupon", "khuyến mãi"]):
                promo_keyword_count += 1
        elif event.event_type in {"product_viewed", "recent_view", "product_clicked_from_listing"}:
            view_count += 1
        elif event.event_type in {"wishlist_added", "wishlist_toggled"}:
            wishlist_count += 1
        elif event.event_type == "cart_added":
            cart_item_count += max(1, event.quantity or 1)
        elif event.event_type == "order_completed":
            order_count += 1
            total_spent += float(event.price or 0) * max(1, event.quantity or 1)
        elif event.event_type == "checkout_started":
            cart_item_count += max(1, event.quantity or 1)

    preferred_categories = [name for name, _ in category_counter.most_common(3)]
    avg_order_value = round(total_spent / order_count, 2) if order_count else 0.0
    engagement = search_count + view_count + wishlist_count * 2 + cart_item_count * 3 + order_count * 2
    purchase_intent = min(
        0.95,
        max(
            0.05,
            round(
                0.04 * search_count
                + 0.05 * view_count
                + 0.12 * wishlist_count
                + 0.18 * cart_item_count
                + 0.08 * order_count,
                3,
            ),
        ),
    )

    if order_count == 0 and engagement <= 2:
        persona = "new_explorer"
        next_best_action = "recommend_entry_products"
    elif promo_keyword_count >= 2 and total_spent < 500000:
        persona = "deal_hunter"
        next_best_action = "push_coupon"
    elif order_count >= 5 and total_spent > 1200000:
        persona = "loyal_member"
        next_best_action = "upsell_membership"
    elif cart_item_count >= 1 or wishlist_count >= 2:
        persona = "high_intent_buyer"
        next_best_action = "bundle_related_products"
        purchase_intent = max(purchase_intent, 0.68)
    else:
        persona = "category_browser"
        next_best_action = "reengage_catalog"

    if promo_keyword_count >= 2 or (avg_order_value and avg_order_value < 120000):
        price_sensitivity = "high"
    elif avg_order_value < 280000 or total_spent < 900000:
        price_sensitivity = "medium"
    else:
        price_sensitivity = "low"

    feature_values = {
        "search_count": search_count,
        "view_count": view_count,
        "wishlist_count": wishlist_count,
        "cart_item_count": cart_item_count,
        "order_count": order_count,
        "avg_order_value": avg_order_value,
        "total_spent": round(total_spent, 2),
        "promo_keyword_count": promo_keyword_count,
        "membership_points": int(total_spent // 8000),
        "preferred_genre_count": len(preferred_categories),
    }
    summary = (
        f"Persona={persona}; price_sensitivity={price_sensitivity}; "
        f"preferred_categories={', '.join(preferred_categories) if preferred_categories else 'none'}; "
        f"purchase_intent={purchase_intent:.2f}"
    )
    return {
        "persona": persona,
        "price_sensitivity": price_sensitivity,
        "purchase_intent": purchase_intent,
        "next_best_action": next_best_action,
        "preferred_categories": preferred_categories,
        "feature_values": feature_values,
        "summary": summary,
        "last_event_at": last_event_at,
    }


def _upsert_profile(db: Session, customer_id: int) -> CustomerBehaviorProfile:
    events = (
        db.query(BehaviorEvent)
        .filter(BehaviorEvent.customer_id == customer_id)
        .order_by(BehaviorEvent.occurred_at.asc(), BehaviorEvent.id.asc())
        .all()
    )
    computed = _compute_profile(events)
    profile = db.query(CustomerBehaviorProfile).filter(CustomerBehaviorProfile.customer_id == customer_id).first()
    if not profile:
        profile = CustomerBehaviorProfile(customer_id=customer_id)
        db.add(profile)

    profile.persona = computed["persona"]
    profile.price_sensitivity = computed["price_sensitivity"]
    profile.purchase_intent = computed["purchase_intent"]
    profile.next_best_action = computed["next_best_action"]
    profile.preferred_categories = computed["preferred_categories"]
    profile.feature_values = computed["feature_values"]
    profile.summary = computed["summary"]
    profile.last_event_at = computed["last_event_at"]
    db.commit()
    db.refresh(profile)
    return profile


@app.get("/health")
def health():
    return {"status": "ok", "service": "behavior_service", "timestamp": datetime.utcnow().isoformat()}


@app.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    return {
        "service": "behavior_service",
        "total_events": db.query(BehaviorEvent).count(),
        "total_profiles": db.query(CustomerBehaviorProfile).count(),
    }


@app.post("/events", response_model=BehaviorEventOut, status_code=201)
def create_event(body: BehaviorEventCreate, db: Session = Depends(get_db)):
    event = BehaviorEvent(
        customer_id=body.customer_id,
        event_type=body.event_type,
        product_id=body.product_id,
        category_name=body.category_name,
        source=body.source,
        query=body.query,
        price=body.price,
        quantity=body.quantity,
        event_metadata=body.event_metadata,
        occurred_at=body.occurred_at or datetime.utcnow(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    graph_sync.sync_event(
        {
            "id": event.id,
            "customer_id": event.customer_id,
            "event_type": event.event_type,
            "product_id": event.product_id,
            "category_name": event.category_name,
            "query": event.query,
            "quantity": event.quantity,
            "occurred_at": event.occurred_at.isoformat() if event.occurred_at else None,
        }
    )
    _upsert_profile(db, body.customer_id)
    return event


@app.get("/events/{customer_id}", response_model=list[BehaviorEventOut])
def list_events(customer_id: int, limit: int = 50, db: Session = Depends(get_db)):
    return (
        db.query(BehaviorEvent)
        .filter(BehaviorEvent.customer_id == customer_id)
        .order_by(BehaviorEvent.occurred_at.desc(), BehaviorEvent.id.desc())
        .limit(limit)
        .all()
    )


@app.get("/profiles/{customer_id}", response_model=BehaviorProfileOut)
def get_profile(customer_id: int, db: Session = Depends(get_db)):
    profile = db.query(CustomerBehaviorProfile).filter(CustomerBehaviorProfile.customer_id == customer_id).first()
    if not profile:
        profile = _upsert_profile(db, customer_id)
    return profile


@app.post("/profiles/{customer_id}/refresh", response_model=BehaviorProfileOut)
def refresh_profile(customer_id: int, db: Session = Depends(get_db)):
    return _upsert_profile(db, customer_id)


@app.get("/features/{customer_id}")
def get_features(customer_id: int, db: Session = Depends(get_db)):
    profile = db.query(CustomerBehaviorProfile).filter(CustomerBehaviorProfile.customer_id == customer_id).first()
    if not profile:
        profile = _upsert_profile(db, customer_id)
    return {
        "customer_id": customer_id,
        "preferred_categories": profile.preferred_categories or [],
        "feature_values": profile.feature_values or {},
        "persona": profile.persona,
        "price_sensitivity": profile.price_sensitivity,
        "purchase_intent": profile.purchase_intent,
        "next_best_action": profile.next_best_action,
        "updated_at": profile.updated_at,
    }
