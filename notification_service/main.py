from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
import json
import logging
import threading

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:trungduc@mysql:3306/notification_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="Notification Service – Assignment 06", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notification_service")

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")


# ════════ MODELS ════════════════════════════════════════

class Notification(Base):
    __tablename__ = "notification"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(255), default="INFO")  # INFO | ORDER | PROMOTION | SYSTEM
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)


class StaffShift(Base):
    __tablename__ = "staff_shift"
    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, nullable=False)
    shift_name = Column(String(255), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    location = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)


class EmailTemplate(Base):
    __tablename__ = "email_template"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    subject = Column(String(255), nullable=False)
    html_body = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


# ══ Schemas ════════════════════════════════════════════
class NotificationCreate(BaseModel):
    customer_id: int; title: str; message: str; notification_type: str = "INFO"


class NotificationOut(BaseModel):
    id: int; customer_id: int; title: str; message: str
    notification_type: str; is_read: bool; created_at: datetime
    class Config: from_attributes = True


class ShiftCreate(BaseModel):
    staff_id: int; shift_name: str; start_time: datetime
    end_time: Optional[datetime] = None; location: Optional[str] = None


class ShiftOut(BaseModel):
    id: int; staff_id: int; shift_name: str; start_time: datetime; end_time: Optional[datetime]
    class Config: from_attributes = True


class EmailTemplateCreate(BaseModel):
    name: str; subject: str; html_body: str


class EmailTemplateOut(BaseModel):
    id: int; name: str; subject: str; is_active: bool
    class Config: from_attributes = True


# ══ Startup & DB ═══════════════════════════════════════
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    # Start RabbitMQ consumer in background thread
    t = threading.Thread(target=start_rabbitmq_consumer, daemon=True)
    t.start()


def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()


# ════════════════════════════════════════════════════════
# RABBITMQ CONSUMER – lắng nghe event order.created
# ════════════════════════════════════════════════════════
def handle_order_created(payload: dict):
    """Tự động tạo notification cho khách khi có đơn hàng mới."""
    customer_id = payload.get("customer_id")
    order_id    = payload.get("order_id")
    total_price = payload.get("total_price", 0)
    if not customer_id or not order_id:
        return
    db = SessionLocal()
    try:
        n = Notification(
            customer_id=customer_id,
            title=f"Đơn hàng #{order_id} đã được xác nhận",
            message=(
                f"Cảm ơn bạn đã đặt hàng! Đơn hàng #{order_id} của bạn "
                f"trị giá {int(total_price):,}đ đã được xác nhận và đang được xử lý."
            ),
            notification_type="ORDER",
        )
        db.add(n)
        db.commit()
        logger.info(f"[CONSUMER] Created notification for customer {customer_id}, order {order_id}")
    except Exception as e:
        logger.error(f"[CONSUMER] Error creating notification: {e}")
    finally:
        db.close()


def start_rabbitmq_consumer():
    """Khởi động consumer lắng nghe queue 'order.created'."""
    import time
    import pika

    # Retry loop – RabbitMQ có thể chưa sẵn sàng khi service khởi động
    for attempt in range(10):
        try:
            params = pika.URLParameters(RABBITMQ_URL)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.queue_declare(queue="order.created", durable=True)

            def callback(ch, method, properties, body):
                try:
                    payload = json.loads(body)
                    logger.info(f"[CONSUMER] Received order.created: {payload}")
                    handle_order_created(payload)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as e:
                    logger.error(f"[CONSUMER] Error processing message: {e}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue="order.created", on_message_callback=callback)
            logger.info("[CONSUMER] notification_service listening on queue 'order.created'")
            channel.start_consuming()
        except Exception as e:
            logger.warning(f"[CONSUMER] RabbitMQ not ready (attempt {attempt+1}/10): {e}")
            time.sleep(5)


# ════════════════════════════════════════════════════════
# HEALTH & METRICS
# ════════════════════════════════════════════════════════
@app.get("/health")
def health():
    return {"status": "ok", "service": "notification_service", "timestamp": datetime.utcnow().isoformat()}


@app.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    total = db.query(Notification).count()
    unread = db.query(Notification).filter(Notification.is_read == False).count()
    return {"service": "notification_service", "total_notifications": total, "unread": unread}


# ════════════════════════════════════════════════════════
# ROUTES
# ════════════════════════════════════════════════════════
@app.post("/notifications", response_model=NotificationOut, status_code=201)
def create_notification(body: NotificationCreate, db: Session = Depends(get_db)):
    n = Notification(**body.model_dump()); db.add(n); db.commit(); db.refresh(n); return n


@app.get("/notifications/{customer_id}", response_model=List[NotificationOut])
def get_notifications(customer_id: int, db: Session = Depends(get_db)):
    return db.query(Notification).filter(
        Notification.customer_id == customer_id
    ).order_by(Notification.created_at.desc()).all()


@app.patch("/notifications/{notification_id}/read")
def mark_read(notification_id: int, db: Session = Depends(get_db)):
    n = db.query(Notification).filter(Notification.id == notification_id).first()
    if not n: raise HTTPException(404, "Không tìm thấy thông báo")
    n.is_read = True; n.read_at = datetime.utcnow()
    db.commit()
    return {"notification_id": notification_id, "read": True}


@app.post("/shifts", response_model=ShiftOut, status_code=201)
def create_shift(body: ShiftCreate, db: Session = Depends(get_db)):
    shift = StaffShift(**body.model_dump()); db.add(shift); db.commit(); db.refresh(shift); return shift


@app.get("/shifts", response_model=List[ShiftOut])
def list_shifts(db: Session = Depends(get_db)):
    return db.query(StaffShift).order_by(StaffShift.start_time.desc()).all()


@app.get("/shifts/staff/{staff_id}", response_model=List[ShiftOut])
def get_staff_shifts(staff_id: int, db: Session = Depends(get_db)):
    return db.query(StaffShift).filter(StaffShift.staff_id == staff_id).order_by(StaffShift.start_time.desc()).all()


@app.post("/email-templates", response_model=EmailTemplateOut, status_code=201)
def create_template(body: EmailTemplateCreate, db: Session = Depends(get_db)):
    t = EmailTemplate(**body.model_dump()); db.add(t); db.commit(); db.refresh(t); return t


@app.get("/email-templates", response_model=List[EmailTemplateOut])
def list_templates(db: Session = Depends(get_db)):
    return db.query(EmailTemplate).filter(EmailTemplate.is_active == True).all()


@app.get("/email-templates/{name}", response_model=EmailTemplateOut)
def get_template(name: str, db: Session = Depends(get_db)):
    t = db.query(EmailTemplate).filter(EmailTemplate.name == name).first()
    if not t: raise HTTPException(404, "Không tìm thấy template")
    return t
