from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
import json
import logging

from database import get_db, init_db
from models import Cart, CartItem, Order, OrderItem, Shipping, Payment, Refund
from schemas import (
    CartItemCreate, CartItemOut, CartOut,
    CheckoutRequest,
    OrderOut, OrderItemOut,
    ShippingOut, PaymentOut,
    RefundCreate, RefundOut
)

logger = logging.getLogger("order_service")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Order Service – Assignment 06", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── RabbitMQ config ───────────────────────────────────
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")


def publish_event(queue_name: str, payload: dict):
    """
    Publish một message lên RabbitMQ queue.
    Dùng pika (blocking). Nếu RabbitMQ chưa sẵn sàng thì log warning thay vì crash.
    """
    try:
        import pika
        params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.queue_declare(queue=queue_name, durable=True)
        channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=json.dumps(payload),
            properties=pika.BasicProperties(delivery_mode=2),  # persistent
        )
        connection.close()
        logger.info(f"[EVENT BUS] Published to '{queue_name}': {payload}")
    except Exception as e:
        logger.warning(f"[EVENT BUS] Không thể publish event tới RabbitMQ: {e}")


@app.on_event("startup")
def startup():
    init_db()


# ════════════════════════════════════════════════════════
# HEALTH & METRICS
# ════════════════════════════════════════════════════════
_request_count = 0

@app.get("/health")
def health():
    return {"status": "ok", "service": "order_service", "timestamp": datetime.utcnow().isoformat()}


@app.get("/metrics")
def order_metrics(db: Session = Depends(get_db)):
    from sqlalchemy import func
    total_orders = db.query(Order).count()
    total_revenue = db.query(func.sum(Order.total_price)).scalar() or 0
    return {
        "service": "order_service",
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "uptime_since": "N/A",
    }


# ════════════════════════════════════════════════════════
# CART
# ════════════════════════════════════════════════════════
@app.get("/cart/{customer_id}", response_model=CartOut)
def view_cart(customer_id: int, db: Session = Depends(get_db)):
    cart = db.query(Cart).filter(Cart.customer_id == customer_id, Cart.is_active == True).first()
    if not cart:
        cart = Cart(customer_id=customer_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


@app.post("/cart/{customer_id}/add")
def add_to_cart(customer_id: int, body: CartItemCreate, db: Session = Depends(get_db)):
    """Thêm sản phẩm vào giỏ hàng"""
    cart = db.query(Cart).filter(Cart.customer_id == customer_id, Cart.is_active == True).first()
    if not cart:
        cart = Cart(customer_id=customer_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)

    item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id, CartItem.book_id == body.product_id
    ).first()
    if item:
        item.quantity += body.quantity
    else:
        item = CartItem(
            cart_id=cart.id, book_id=body.product_id,
            quantity=body.quantity, unit_price=body.unit_price
        )
        db.add(item)
    db.commit()
    return {"message": "Đã thêm vào giỏ", "cart_id": cart.id}


@app.patch("/cart/{customer_id}/item/{item_id}/quantity")
def update_cart_quantity(customer_id: int, item_id: int, quantity: int, db: Session = Depends(get_db)):
    """Cập nhật số lượng sản phẩm trong giỏ"""
    cart = db.query(Cart).filter(Cart.customer_id == customer_id, Cart.is_active == True).first()
    if not cart:
        raise HTTPException(404, "Không tìm thấy giỏ hàng")
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not item:
        raise HTTPException(404, "Không tìm thấy sản phẩm trong giỏ")
    if quantity <= 0:
        db.delete(item)
    else:
        item.quantity = quantity
    db.commit()
    return {"message": "Đã cập nhật", "item_id": item_id, "quantity": max(quantity, 0)}


@app.delete("/cart/{customer_id}/item/{item_id}", status_code=204)
def remove_cart_item(customer_id: int, item_id: int, db: Session = Depends(get_db)):
    """Xóa 1 mục khỏi giỏ hàng"""
    cart = db.query(Cart).filter(Cart.customer_id == customer_id, Cart.is_active == True).first()
    if not cart:
        raise HTTPException(404, "Không tìm thấy giỏ hàng")
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not item:
        raise HTTPException(404, "Không tìm thấy sản phẩm trong giỏ")
    db.delete(item)
    db.commit()


@app.delete("/cart/{customer_id}/clear", status_code=204)
def clear_cart(customer_id: int, db: Session = Depends(get_db)):
    """Xóa toàn bộ giỏ hàng"""
    cart = db.query(Cart).filter(Cart.customer_id == customer_id, Cart.is_active == True).first()
    if cart:
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
        db.commit()


@app.get("/cart/{customer_id}/summary")
def cart_summary(customer_id: int, db: Session = Depends(get_db)):
    """Tóm tắt giỏ hàng: tổng tiền, số lượng items"""
    cart = db.query(Cart).filter(Cart.customer_id == customer_id, Cart.is_active == True).first()
    if not cart:
        return {"item_count": 0, "total_price": 0.0, "cart_id": None}
    items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()
    total = sum((i.unit_price or 0) * i.quantity for i in items)
    count = sum(i.quantity for i in items)
    return {"item_count": count, "total_price": round(total, 2), "cart_id": cart.id}


# ════════════════════════════════════════════════════════
# CHECKOUT (legacy – direct, không dùng Saga)
# ════════════════════════════════════════════════════════
@app.post("/checkout", response_model=OrderOut, status_code=201)
def checkout(body: CheckoutRequest, db: Session = Depends(get_db)):
    """Đặt hàng từ giỏ hàng hiện tại (legacy, không dùng Saga)"""
    cart = db.query(Cart).filter(
        Cart.customer_id == body.customer_id, Cart.is_active == True
    ).first()
    if not cart:
        raise HTTPException(400, "Giỏ hàng trống hoặc không tồn tại")
    items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()
    if not items:
        raise HTTPException(400, "Giỏ hàng không có sản phẩm")

    total_price = sum((i.unit_price or 0) * i.quantity for i in items)
    total_qty = sum(i.quantity for i in items)
    fee = 30000 if body.ship_method == "fast" else 15000

    order = Order(
        customer_id=body.customer_id,
        coupon_code=body.coupon_code,
        total_price=total_price + fee,
        total_quantity=total_qty,
        note=body.note,
        saga_status="CONFIRMED",  # legacy checkout = trực tiếp confirm
        saga_step="direct_checkout",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    for item in items:
        db.add(OrderItem(
            order_id=order.id,
            book_id=item.book_id,
            price=item.unit_price or 0,
            quantity=item.quantity
        ))

    db.add(Shipping(order_id=order.id, method=body.ship_method, fee=fee))
    db.add(Payment(order_id=order.id, method=body.pay_method, amount=total_price + fee))

    cart.is_active = False
    db.commit()
    db.refresh(order)

    # Publish event qua RabbitMQ
    publish_event("order.created", {
        "order_id": order.id,
        "customer_id": order.customer_id,
        "total_price": order.total_price,
        "total_quantity": order.total_quantity,
        "pay_method": body.pay_method,
        "ship_method": body.ship_method,
        "items": [{"product_id": i.book_id, "quantity": i.quantity} for i in items],
    })
    return order


# ════════════════════════════════════════════════════════
# SAGA CHECKOUT (Assignment 06 – Orchestration Pattern)
# ════════════════════════════════════════════════════════
@app.post("/checkout/saga", response_model=OrderOut, status_code=201)
def checkout_saga(body: CheckoutRequest, db: Session = Depends(get_db)):
    """
    Saga Orchestration – Order Creation Flow:
      Step 1: Create Order (PENDING)
      Step 2: Reserve Payment
      Step 3: Reserve Shipping
      Step 4: Confirm Order (CONFIRMED)
      Compensate: nếu step nào thất bại → CANCEL order + rollback
    """
    # ── Validate cart ──────────────────────────────────
    cart = db.query(Cart).filter(
        Cart.customer_id == body.customer_id, Cart.is_active == True
    ).first()
    if not cart:
        raise HTTPException(400, "Giỏ hàng trống hoặc không tồn tại")
    items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()
    if not items:
        raise HTTPException(400, "Giỏ hàng không có sản phẩm")

    total_price = sum((i.unit_price or 0) * i.quantity for i in items)
    total_qty   = sum(i.quantity for i in items)
    fee = 30000 if body.ship_method == "fast" else 15000

    # ── STEP 1: Create Order (PENDING) ────────────────
    order = Order(
        customer_id=body.customer_id,
        coupon_code=body.coupon_code,
        total_price=total_price + fee,
        total_quantity=total_qty,
        note=body.note,
        status="PENDING",
        saga_status="INITIATED",
        saga_step="step1_order_created",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    for item in items:
        db.add(OrderItem(
            order_id=order.id,
            book_id=item.book_id,
            price=item.unit_price or 0,
            quantity=item.quantity
        ))
    db.commit()

    logger.info(f"[SAGA] Order {order.id} – Step 1: CREATED (PENDING)")

    # ── STEP 2: Reserve Payment ────────────────────────
    try:
        payment = Payment(
            order_id=order.id,
            method=body.pay_method,
            amount=total_price + fee,
            status="Reserved",
        )
        db.add(payment)
        db.commit()
        order.saga_status = "PAYMENT_RESERVED"
        order.saga_step   = "step2_payment_reserved"
        db.commit()
        logger.info(f"[SAGA] Order {order.id} – Step 2: PAYMENT RESERVED")
    except Exception as e:
        # Compensate: cancel order
        order.status      = "CANCELLED"
        order.saga_status = "PAYMENT_FAILED"
        order.saga_error  = str(e)
        order.saga_step   = "compensate_payment_failed"
        db.commit()
        logger.error(f"[SAGA] Order {order.id} – COMPENSATE: payment failed: {e}")
        raise HTTPException(500, f"Saga compensation: Payment failed – {e}")

    # ── STEP 3: Reserve Shipping ───────────────────────
    try:
        shipping = Shipping(
            order_id=order.id,
            method=body.ship_method,
            fee=fee,
            status="Reserved",
        )
        db.add(shipping)
        db.commit()
        order.saga_status = "SHIPPING_RESERVED"
        order.saga_step   = "step3_shipping_reserved"
        db.commit()
        logger.info(f"[SAGA] Order {order.id} – Step 3: SHIPPING RESERVED")
    except Exception as e:
        # Compensate: cancel payment + order
        payment.status    = "Cancelled"
        order.status      = "CANCELLED"
        order.saga_status = "SHIPPING_FAILED"
        order.saga_error  = str(e)
        order.saga_step   = "compensate_shipping_failed"
        db.commit()
        logger.error(f"[SAGA] Order {order.id} – COMPENSATE: shipping failed: {e}")
        raise HTTPException(500, f"Saga compensation: Shipping failed – {e}")

    # ── STEP 4: Confirm Order ──────────────────────────
    try:
        payment.status    = "Paid"
        order.status      = "APPROVED"
        order.saga_status = "CONFIRMED"
        order.saga_step   = "step4_confirmed"
        cart.is_active    = False
        db.commit()
        db.refresh(order)
        logger.info(f"[SAGA] Order {order.id} – Step 4: CONFIRMED ✓")
    except Exception as e:
        order.saga_status = "COMPENSATED"
        order.saga_error  = str(e)
        db.commit()
        raise HTTPException(500, f"Saga compensation: Confirm failed – {e}")

    # ── Publish event to RabbitMQ ──────────────────────
    publish_event("order.created", {
        "order_id": order.id,
        "customer_id": order.customer_id,
        "total_price": order.total_price,
        "total_quantity": order.total_quantity,
        "pay_method": body.pay_method,
        "ship_method": body.ship_method,
        "saga_status": order.saga_status,
        "items": [{"product_id": i.book_id, "quantity": i.quantity} for i in items],
    })

    return order


# ════════════════════════════════════════════════════════
# ORDERS
# ════════════════════════════════════════════════════════
@app.get("/orders/customer/{customer_id}", response_model=List[OrderOut])
def get_customer_orders(customer_id: int, db: Session = Depends(get_db)):
    return db.query(Order).filter(Order.customer_id == customer_id).order_by(Order.date.desc()).all()


@app.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Không tìm thấy đơn hàng")
    return order


@app.get("/orders/{order_id}/items", response_model=List[OrderItemOut])
def get_order_items(order_id: int, db: Session = Depends(get_db)):
    return db.query(OrderItem).filter(OrderItem.order_id == order_id).all()


@app.get("/orders", response_model=List[OrderOut])
def list_all_orders(skip: int = 0, limit: int = 50, status: str = None, db: Session = Depends(get_db)):
    """[STAFF] Xem tất cả đơn hàng, có thể filter theo status"""
    q = db.query(Order)
    if status:
        q = q.filter(Order.status == status)
    return q.order_by(Order.date.desc()).offset(skip).limit(limit).all()


@app.patch("/orders/{order_id}/status")
def update_order_status(order_id: int, status: str, staff_id: int = None, db: Session = Depends(get_db)):
    """[STAFF] Cập nhật trạng thái đơn hàng"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Không tìm thấy đơn hàng")
    order.status = status
    if staff_id:
        order.staff_id = staff_id
    db.commit()
    return {"order_id": order_id, "new_status": status}


@app.get("/orders/stats/summary")
def order_stats(db: Session = Depends(get_db)):
    """[STAFF] Thống kê nhanh đơn hàng theo trạng thái"""
    from sqlalchemy import func
    results = db.query(Order.status, func.count(Order.id), func.sum(Order.total_price)).group_by(Order.status).all()
    return [{"status": r[0], "count": r[1], "total_revenue": r[2] or 0} for r in results]


# ════════════════════════════════════════════════════════
# REFUND
# ════════════════════════════════════════════════════════
@app.post("/refunds", response_model=RefundOut, status_code=201)
def request_refund(body: RefundCreate, db: Session = Depends(get_db)):
    refund = Refund(**body.model_dump())
    db.add(refund)
    db.commit()
    db.refresh(refund)
    return refund


@app.get("/refunds", response_model=List[RefundOut])
def list_refunds(db: Session = Depends(get_db)):
    return db.query(Refund).all()


@app.patch("/refunds/{refund_id}/status")
def update_refund(refund_id: int, status: str, db: Session = Depends(get_db)):
    refund = db.query(Refund).filter(Refund.id == refund_id).first()
    if not refund:
        raise HTTPException(404, "Không tìm thấy yêu cầu hoàn tiền")
    refund.status = status
    if status == "COMPLETED":
        refund.resolved_at = datetime.utcnow()
    db.commit()
    return {"refund_id": refund_id, "new_status": status}
