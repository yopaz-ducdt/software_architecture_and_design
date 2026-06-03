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

import os
import json
import logging
import threading

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:Duyanh090%40@mysql:3306/inventory_db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
app = FastAPI(title="Inventory Service – Assignment 06", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("inventory_service")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")


# ════════ MODELS ════════════════════════════════════════

# MODEL 1: Supplier – Nhà cung cấp
class Supplier(Base):
    __tablename__ = "supplier"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    contact_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")


# MODEL 2: PurchaseOrder – Đơn nhập hàng
class PurchaseOrder(Base):
    __tablename__ = "purchase_order"
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("supplier.id"), nullable=False)
    total_amount = Column(Float, default=0)
    status = Column(String(255), default="DRAFT")    # DRAFT | ORDERED | RECEIVED | CANCELLED
    order_date = Column(DateTime, default=datetime.utcnow)
    received_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    supplier = relationship("Supplier", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="order")


# MODEL 3: PurchaseOrderItem – Chi tiết đơn nhập
class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_item"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("purchase_order.id"), nullable=False)
    book_id = Column(Integer, nullable=False)   # FK to book_service
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Float, nullable=False)
    order = relationship("PurchaseOrder", back_populates="items")


# MODEL 4: Warehouse – Kho
class Warehouse(Base):
    __tablename__ = "warehouse"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    capacity = Column(Integer, nullable=True)
    logs = relationship("InventoryLog", back_populates="warehouse")


# MODEL 5: InventoryLog – Nhật ký tồn kho
class InventoryLog(Base):
    __tablename__ = "inventory_log"
    id = Column(Integer, primary_key=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouse.id"), nullable=True)
    book_id = Column(Integer, nullable=False)
    change_type = Column(String(255), nullable=False)   # IN | OUT | ADJUSTMENT
    quantity = Column(Integer, nullable=False)
    note = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    warehouse = relationship("Warehouse", back_populates="logs")


# MODEL 6: InventoryAlert – Cảnh báo hết hàng (thêm mới)
class InventoryAlert(Base):
    """Cảnh báo khi tồn kho một cuốn sách xuống dưới ngưỡng"""
    __tablename__ = "inventory_alert"
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, nullable=False)
    threshold = Column(Integer, default=10)     # cảnh báo khi stock < threshold
    current_stock = Column(Integer, nullable=True)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ══ Schemas ════════════════════════════════════════════
class SupplierCreate(BaseModel):
    name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class SupplierOut(BaseModel):
    id: int; name: str; contact_name: Optional[str]; email: Optional[str]; is_active: bool
    class Config: from_attributes = True


class POCreate(BaseModel):
    supplier_id: int
    notes: Optional[str] = None


class POOut(BaseModel):
    id: int; supplier_id: int; total_amount: float; status: str; order_date: datetime
    class Config: from_attributes = True


class WarehouseCreate(BaseModel):
    name: str
    location: Optional[str] = None
    capacity: Optional[int] = None


class WarehouseOut(BaseModel):
    id: int; name: str; location: Optional[str]; capacity: Optional[int]
    class Config: from_attributes = True


class LogCreate(BaseModel):
    warehouse_id: Optional[int] = None
    book_id: int
    change_type: str
    quantity: int
    note: Optional[str] = None


class LogOut(BaseModel):
    id: int; book_id: int; change_type: str; quantity: int; timestamp: datetime
    class Config: from_attributes = True


class AlertCreate(BaseModel):
    book_id: int
    threshold: int = 10
    current_stock: Optional[int] = None


class AlertOut(BaseModel):
    id: int; book_id: int; threshold: int; current_stock: Optional[int]; is_resolved: bool
    class Config: from_attributes = True


# ══ RabbitMQ Consumer ══════════════════════════════════
def handle_order_created_inventory(payload: dict):
    """Khi có đơn hàng mới, ghi log tồn kho OUT cho từng sách."""
    items = payload.get("items", [])
    order_id = payload.get("order_id")
    db = SessionLocal()
    try:
        for item in items:
            book_id  = item.get("book_id")
            quantity = item.get("quantity", 0)
            if book_id and quantity > 0:
                log = InventoryLog(
                    book_id=book_id,
                    change_type="OUT",
                    quantity=quantity,
                    note=f"Saga order #{order_id} confirmed – auto deduct",
                )
                db.add(log)
        db.commit()
        logger.info(f"[CONSUMER] Inventory deducted for order {order_id}: {items}")
    except Exception as e:
        logger.error(f"[CONSUMER] Inventory deduct error: {e}")
    finally:
        db.close()


def start_rabbitmq_consumer():
    """Lắng nghe queue 'order.created' để tự động giảm tồn kho."""
    import time
    import pika
    for attempt in range(10):
        try:
            params = pika.URLParameters(RABBITMQ_URL)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.queue_declare(queue="order.created", durable=True)

            def callback(ch, method, properties, body):
                try:
                    payload = json.loads(body)
                    logger.info(f"[CONSUMER] order.created received: {payload}")
                    handle_order_created_inventory(payload)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as e:
                    logger.error(f"[CONSUMER] Error processing: {e}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue="order.created", on_message_callback=callback)
            logger.info("[CONSUMER] inventory_service listening on 'order.created'")
            channel.start_consuming()
        except Exception as e:
            logger.warning(f"[CONSUMER] RabbitMQ not ready (attempt {attempt+1}/10): {e}")
            time.sleep(5)


# ══ Startup ═══════════════════════════════════════════
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
    t = threading.Thread(target=start_rabbitmq_consumer, daemon=True)
    t.start()


def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()


# ══ Health & Metrics ════════════════════════════════════
@app.get("/health")
def health():
    return {"status": "ok", "service": "inventory_service", "timestamp": datetime.utcnow().isoformat()}


@app.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    total_logs = db.query(InventoryLog).count()
    total_suppliers = db.query(Supplier).count()
    unresolved_alerts = db.query(InventoryAlert).filter(InventoryAlert.is_resolved == False).count()
    return {
        "service": "inventory_service",
        "total_inventory_logs": total_logs,
        "total_suppliers": total_suppliers,
        "unresolved_alerts": unresolved_alerts,
    }


# ════════ ROUTES ════════════════════════════════════════

@app.post("/suppliers", response_model=SupplierOut, status_code=201)
def create_supplier(body: SupplierCreate, db: Session = Depends(get_db)):
    s = Supplier(**body.model_dump()); db.add(s); db.commit(); db.refresh(s); return s


@app.get("/suppliers", response_model=List[SupplierOut])
def list_suppliers(db: Session = Depends(get_db)):
    return db.query(Supplier).all()


@app.post("/purchase-orders", response_model=POOut, status_code=201)
def create_po(body: POCreate, db: Session = Depends(get_db)):
    po = PurchaseOrder(**body.model_dump()); db.add(po); db.commit(); db.refresh(po); return po


@app.get("/purchase-orders", response_model=List[POOut])
def list_pos(db: Session = Depends(get_db)):
    return db.query(PurchaseOrder).order_by(PurchaseOrder.order_date.desc()).all()


@app.patch("/purchase-orders/{po_id}/status")
def update_po_status(po_id: int, status: str, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po: raise HTTPException(404, "Không tìm thấy đơn nhập hàng")
    po.status = status
    if status == "RECEIVED": po.received_date = datetime.utcnow()
    db.commit()
    return {"po_id": po_id, "status": status}


@app.post("/warehouses", response_model=WarehouseOut, status_code=201)
def create_warehouse(body: WarehouseCreate, db: Session = Depends(get_db)):
    w = Warehouse(**body.model_dump()); db.add(w); db.commit(); db.refresh(w); return w


@app.get("/warehouses", response_model=List[WarehouseOut])
def list_warehouses(db: Session = Depends(get_db)):
    return db.query(Warehouse).all()


@app.post("/logs", response_model=LogOut, status_code=201)
def add_log(body: LogCreate, db: Session = Depends(get_db)):
    log = InventoryLog(**body.model_dump()); db.add(log); db.commit(); db.refresh(log); return log


@app.get("/logs", response_model=List[LogOut])
def list_logs(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(InventoryLog).order_by(InventoryLog.timestamp.desc()).limit(limit).all()


@app.post("/alerts", response_model=AlertOut, status_code=201)
def create_alert(body: AlertCreate, db: Session = Depends(get_db)):
    alert = InventoryAlert(**body.model_dump()); db.add(alert); db.commit(); db.refresh(alert); return alert


@app.get("/alerts", response_model=List[AlertOut])
def list_alerts(db: Session = Depends(get_db)):
    return db.query(InventoryAlert).filter(InventoryAlert.is_resolved == False).all()


@app.patch("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(InventoryAlert).filter(InventoryAlert.id == alert_id).first()
    if not alert: raise HTTPException(404, "Không tìm thấy cảnh báo")
    alert.is_resolved = True; db.commit()
    return {"alert_id": alert_id, "resolved": True}
