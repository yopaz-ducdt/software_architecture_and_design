# HƯỚNG DẪN CHI TIẾT – BookStore Assignment 06
## Microservices với FastAPI · RabbitMQ · Saga · Docker

---

## MỤC LỤC

1. [TẠO PROJECT](#1-tạo-project)
2. [TẠO CÁC SERVICE](#2-tạo-các-service)
3. [SINH RA SEQUENCE DIAGRAM](#3-sinh-ra-sequence-diagram)
4. [DEPLOY](#4-deploy)

---

## 1. TẠO PROJECT

### 1.1. Cấu trúc thư mục tổng thể

```
assignment_6/
├── docker-compose.yml          ← Orchestrate toàn bộ hệ thống
├── README.md
│
├── api_gateway/                ← (MỚI) Smart proxy: JWT, RBAC, Rate Limit
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
│
├── auth_service/               ← Xác thực & JWT issuer
│   ├── Dockerfile
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   └── requirements.txt
│
├── book_service/               ← Quản lý sách & danh mục
├── order_service/              ← Giỏ hàng, đặt hàng, Saga
├── customer_service/           ← Hồ sơ khách hàng
├── staff_service/              ← Quản lý nhân viên
├── marketing_service/          ← Voucher, coupon, banner
├── inventory_service/          ← Tồn kho (RabbitMQ consumer)
├── content_service/            ← Blog, bài viết
├── interaction_service/        ← Reviews, ratings
├── analytics_service/          ← Thống kê, báo cáo
└── notification_service/       ← Thông báo (RabbitMQ consumer)
```

### 1.2. Yêu cầu môi trường

| Công cụ | Phiên bản | Mục đích |
|---------|-----------|---------|
| Python | ≥ 3.11 | Chạy FastAPI |
| Docker Desktop | ≥ 4.x | Container hóa |
| Docker Compose | v2 (bundled) | Điều phối services |

### 1.3. Khởi tạo một service mới (template)

Mỗi service là một **mini FastAPI app** độc lập. Cấu trúc cơ bản:

**Bước 1 – Tạo thư mục:**
```bash
mkdir my_service
cd my_service
```

**Bước 2 – Tạo `requirements.txt`:**
```
fastapi
uvicorn[standard]
sqlalchemy
pymysql
cryptography
python-jose[cryptography]
passlib[bcrypt]
```
> Thêm `pika` nếu service cần giao tiếp RabbitMQ.

**Bước 3 – Tạo `database.py`:**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./my_service.db"   # fallback local
)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from models import Base
    Base.metadata.create_all(bind=engine)
```

**Bước 4 – Tạo `Dockerfile`:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Bước 5 – Entry point `main.py` (skeleton):**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI(title="My Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    from database import init_db
    init_db()

# ── Observability (bắt buộc theo Assignment 06) ──────────
@app.get("/health")
def health():
    return {"status": "ok", "service": "my_service",
            "timestamp": datetime.utcnow().isoformat()}

@app.get("/metrics")
def metrics():
    return {"service": "my_service", "info": "custom metrics here"}
```

### 1.4. Kiến trúc tổng quan

```
                        ┌─────────────────────┐
  Browser / Client ────►│   API Gateway :8000  │
                        │  JWT · RBAC · Rate   │
                        └──────────┬──────────┘
                                   │  reverse proxy (httpx)
              ┌────────────────────┼────────────────────────┐
              ▼                    ▼                         ▼
     auth_service:8001   order_service:8003       book_service:8002
     (JWT issuer)        (Saga Orchestrator)      (catalog)
                                   │
                           publish event
                                   ▼
                            ┌──────────────┐
                            │  RabbitMQ    │  queue: order.created
                            └──────┬───────┘
                    ┌──────────────┴──────────────┐
                    ▼                              ▼
         notification_service:8011    inventory_service:8007
         (gửi thông báo KH)           (ghi log tồn kho)
```

---

## 2. TẠO CÁC SERVICE

### 2.1. API Gateway (`api_gateway/`)

**Vai trò:** Single entry-point, thay thế nginx thuần bằng logic thông minh.

**Các tính năng chính:**

| Tính năng | Chi tiết |
|-----------|----------|
| **Reverse Proxy** | Dùng `httpx.AsyncClient` forward request đến upstream service |
| **JWT Validation** | Check `Authorization: Bearer <token>` trước mỗi request |
| **RBAC** | `/staff/`, `/inventory/`, `/analytics/`, `/marketing/` → chỉ `user_type=staff` |
| **Rate Limiting** | Sliding window: 60 req / 60s mỗi IP (in-memory dict) |
| **Request Logging** | Log `METHOD PATH → TARGET [STATUS] Xms ip=x.x.x.x` |
| **Metrics** | `GET /metrics` trả về tổng số request, rejected, forwarded |

**Mapping upstream (trong `main.py`):**
```python
UPSTREAM = {
    "/auth/":          "http://auth_service:8001",
    "/books/":         "http://book_service:8002",
    "/orders/":        "http://order_service:8003",
    "/customers/":     "http://customer_service:8004",
    "/staff/":         "http://staff_service:8005",
    "/marketing/":     "http://marketing_service:8006",
    "/inventory/":     "http://inventory_service:8007",
    "/content/":       "http://content_service:8008",
    "/interaction/":   "http://interaction_service:8009",
    "/analytics/":     "http://analytics_service:8010",
    "/notifications/": "http://notification_service:8011",
}
```

**Public paths (không cần JWT):**
```python
PUBLIC_PATHS = {
    "/auth/login/customer",
    "/auth/login/staff",
    "/auth/register/customer",
    "/auth/register/staff",
    "/health", "/",
}
```

**Luồng xử lý mỗi request:**
```
Request đến
    ↓
1. Rate limit check  → 429 nếu vượt
    ↓
2. JWT check         → 401 nếu thiếu/sai token (trừ public paths)
    ↓
3. RBAC check        → 403 nếu customer truy cập staff-only route
    ↓
4. Route matching    → 404 nếu không có upstream
    ↓
5. Forward via httpx → inject X-User-Id, X-User-Type, X-User-Role headers
    ↓
6. Log & return response
```

---

### 2.2. Auth Service (`auth_service/`)

**Vai trò:** Quản lý tài khoản, cấp JWT.

**Models:**

```python
class Customer(Base):
    __tablename__ = "customer"
    id, name, email, password (bcrypt), is_active, created_at

class Staff(Base):
    __tablename__ = "staff"
    id, name, username, password (bcrypt), role, is_active, created_at
    # role: "staff" | "admin" | "manager"

class RefreshToken(Base):
    __tablename__ = "refresh_token"
    id, token, user_type, customer_id, staff_id, expires_at
```

**Endpoints quan trọng:**

| Method | Path | Mô tả |
|--------|------|-------|
| POST | `/register/customer` | Đăng ký khách hàng (bcrypt password) |
| POST | `/login/customer` | Đăng nhập → trả JWT 60 phút |
| POST | `/register/staff` | Tạo tài khoản nhân viên |
| POST | `/login/staff` | Đăng nhập nhân viên → JWT có `role` |
| GET | `/verify-token?token=...` | Xác minh JWT (dùng bởi các service khác) |
| GET | `/me` | Giải mã JWT, trả thông tin user |
| GET | `/health` | Health check |
| GET | `/metrics` | Tổng số customer/staff |

**JWT payload:**
```json
// Customer
{"sub": "42", "user_type": "customer", "name": "Nguyen Van A", "exp": 1234567890}

// Staff
{"sub": "5", "user_type": "staff", "role": "admin", "name": "Tran B", "exp": 1234567890}
```

---

### 2.3. Order Service (`order_service/`) – Saga Orchestrator

**Vai trò:** Quản lý giỏ hàng, đặt hàng; điều phối Saga pattern.

**Models:** `Cart`, `CartItem`, `Order`, `OrderItem`, `Payment`, `Shipping`, `Refund`

**Order status fields:**

| Field | Giá trị có thể |
|-------|---------------|
| `status` | `PENDING` → `APPROVED` / `CANCELLED` |
| `saga_status` | `INITIATED` → `PAYMENT_RESERVED` → `SHIPPING_RESERVED` → `CONFIRMED` / `PAYMENT_FAILED` / `SHIPPING_FAILED` |
| `saga_step` | `step1_order_created`, `step2_payment_reserved`, ... |

**Saga Checkout Flow (`POST /checkout/saga`):**

```
STEP 1: Tạo Order
  → status=PENDING, saga_status=INITIATED

      ↓ (thành công)

STEP 2: Reserve Payment
  → Tạo Payment(status="Reserved")
  → saga_status=PAYMENT_RESERVED
  
      ↓ FAIL → COMPENSATE:
                 order.status=CANCELLED
                 saga_status=PAYMENT_FAILED
      
      ↓ (thành công)

STEP 3: Reserve Shipping
  → Tạo Shipping(status="Reserved")
  → saga_status=SHIPPING_RESERVED
  
      ↓ FAIL → COMPENSATE:
                 payment.status=Cancelled
                 order.status=CANCELLED
                 saga_status=SHIPPING_FAILED

      ↓ (thành công)

STEP 4: Confirm
  → payment.status=Paid
  → order.status=APPROVED
  → saga_status=CONFIRMED
  → cart.is_active=False
  → PUBLISH event "order.created" → RabbitMQ
```

**Publish event RabbitMQ:**
```python
def publish_event(queue_name: str, payload: dict):
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
```

---

### 2.4. Notification Service (`notification_service/`) – RabbitMQ Consumer

**Vai trò:** Lắng nghe queue `order.created`, tự động tạo notification cho khách hàng.

**Pattern Consumer:**
```python
import pika, json, threading

def start_consumer():
    params = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue="order.created", durable=True)

    def callback(ch, method, properties, body):
        data = json.loads(body)
        # Tạo notification record trong DB
        # ...
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue="order.created", on_message_callback=callback)
    channel.start_consuming()

# Khởi động consumer trong background thread khi app startup
@app.on_event("startup")
def startup():
    thread = threading.Thread(target=start_consumer, daemon=True)
    thread.start()
```

---

### 2.5. Inventory Service (`inventory_service/`) – RabbitMQ Consumer

**Vai trò:** Lắng nghe `order.created`, ghi log xuất kho tự động khi có đơn hàng mới.

Cơ chế tương tự `notification_service`:
- Subscribe queue `order.created`
- Với mỗi item trong order → ghi `StockLog(type="OUT", quantity=...)`

---

### 2.6. Các Service còn lại (cùng template)

Tất cả đều:
- **FastAPI** + **SQLite** (dev) / **MySQL** (prod)
- Expose `/health` và `/metrics`
- Có `Dockerfile` + `requirements.txt`

| Service | Port | Chức năng chính |
|---------|------|----------------|
| `book_service` | 8002 | CRUD sách, danh mục, tìm kiếm |
| `customer_service` | 8004 | Hồ sơ, địa chỉ, wishlist |
| `staff_service` | 8005 | Thông tin nhân viên |
| `marketing_service` | 8006 | Voucher, coupon, banner |
| `content_service` | 8008 | Blog, bài viết |
| `interaction_service` | 8009 | Review, rating, bình luận |
| `analytics_service` | 8010 | Thống kê doanh số, báo cáo |

---

## 3. 10 CHỨC NĂNG CỐT LÕI (KÈM SEQUENCE DIAGRAM)

Dưới đây là 10 luồng nghiệp vụ (chức năng) chính yếu của hệ thống, minh họa cách các Microservices tương tác với nhau thông qua API Gateway và RabbitMQ.

### 3.1. Chức năng 1: Khách hàng Đăng nhập & Lấy JWT (Auth Service)
Luồng xác thực cơ bản để lấy JSON Web Token (JWT) phục vụ cho các request tiếp theo.

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant GW as API Gateway :8000
    participant Auth as auth_service :8001

    Client->>GW: POST /auth/login/customer {email, password}
    Note over GW: Nằm trong PUBLIC_PATHS → Bỏ qua check JWT
    GW->>Auth: POST /login/customer (forward)
    Auth->>Auth: Lấy thông tin & hash check password
    Auth-->>GW: {access_token, user_type: "customer"}
    GW-->>Client: 200 OK kèm JWT Token
```

---

### 3.2. Chức năng 2: Quyền truy cập Staff bị từ chối (RBAC qua Gateway)
Ví dụ về Role-Based Access Control, API Gateway chặn khách hàng truy cập API nội bộ.

```mermaid
sequenceDiagram
    autonumber
    actor Customer
    participant GW as API Gateway :8000

    Customer->>GW: GET /inventory/items (Cung cấp Customer JWT)
    GW->>GW: Validate JWT thành công -> lấy role
    GW->>GW: Kiểm tra Role: /inventory/ yêu cầu "staff"
    GW->>GW: Role "customer" < "staff" => TỪ CHỐI
    GW-->>Customer: 403 Forbidden (Bạn không có quyền truy cập)
```

---

### 3.3. Chức năng 3: Xem & Tìm kiếm Sách (Book Service)
Khách hàng duyệt danh mục, thông tin chi tiết các loại sách có sẵn.

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant GW as API Gateway :8000
    participant BK as book_service :8002

    Client->>GW: GET /books/search?q=Python (Có JWT)
    GW->>GW: Rate limiting check (Thành công)
    GW->>GW: Decode JWT & RBAC check (Thành công)
    GW->>BK: GET /search?q=Python (+ Headers X-User-Id)
    BK-->>GW: 200 OK [Danh sách sách]
    GW-->>Client: Trả về JSON Danh Sách Sách
```

---

### 3.4. Chức năng 4: Quản lý & Thêm Sách vào Giỏ hàng (Order Service)
Mỗi khách hàng có một phiên giỏ hàng tạm thời. Khách có thể cập nhật, thêm sách trước khi thanh toán.

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant GW as API Gateway
    participant OS as order_service

    Client->>GW: POST /orders/cart/1/add {book_id: 10, qty: 2}
    GW->>OS: Forward xác nhận ID user
    OS->>OS: Tìm / Tạo mới Active Cart
    OS->>OS: Insert/Update CartItem
    OS-->>GW: 200 OK (Cart Object)
    GW-->>Client: Hiển thị giỏ hàng hiện tại
```

---

### 3.5. Chức năng 5: Đánh giá & Bình luận Sách (Interaction Service)
Cho phép khách hàng để lại rating 5★ hoặc bình luận về cuốn sách họ đã đọc.

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant GW as API Gateway
    participant IX as interaction_service

    Client->>GW: POST /interaction/reviews {book_id, rating, comment}
    GW->>IX: Forward kèm X-User-Id 
    IX->>IX: Validate dữ liệu (1-5 sao)
    IX->>IX: Insert Review (Interaction_DB)
    IX-->>GW: 201 Created
    GW-->>Client: Thông báo Bình luận đã được gửi
```

---

### 3.6. Chức năng 6: Cập nhật Hồ sơ Địa chỉ Giao Hàng (Customer Service)
Quản lý thông tin cá nhân, địa chỉ ship để làm defaults khi Checkout.

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant GW as API Gateway
    participant CS as customer_service

    Client->>GW: PATCH /customers/profile {address, phone}
    GW->>CS: Forward request (chỉ lấy user_id từ Token)
    CS->>CS: Cập nhật record Customer_DB
    CS-->>GW: 200 OK
    GW-->>Client: Thay đổi thành công
```

---

### 3.7. Chức năng 7: Áp dụng Mã Giảm Giá - Voucher (Marketing Service)
Xác minh mã giảm giá (coupon) trong bước tính giá trị Giỏ Hàng.

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant GW as Gateway
    participant OS as order_service
    participant MK as marketing_service

    Client->>GW: POST /orders/cart/discount {coupon_code}
    GW->>OS: Tính lại tổng tiền
    OS->>GW: Xin validate mã (Gọi vòng sang Marketing Service)
    GW->>MK: GET /marketing/coupons/validate?code=...
    MK-->>GW: Trả về phần trăm giảm giá (ví dụ: -10%)
    GW-->>OS: Nhận tỷ lệ chiết khấu
    OS->>OS: Cập nhật lại số tiền phải trả (Total Amount)
    OS-->>Client: 200 OK {discounted_total}
```

---

### 3.8. Chức năng 8: Thanh toán phân tán (Saga Orchestration Checkout)
Luồng thanh toán cốt lõi. Giao tiếp nhiều Node và Rollback khi lỗi.

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant GW as API Gateway
    participant OS as order_service (Orchestrator)
    participant MQ as RabbitMQ
    participant IS as inventory_service

    Client->>GW: POST /orders/checkout/saga
    GW->>OS: Forward payment method
    OS->>OS: 1. Tạo Order tạm (PENDING)
    OS->>OS: 2. Reserve Payment (Local DB)
    OS->>OS: 3. Reserve Shipping (Local DB)
    OS->>OS: 4. Ghi nhận Thành công (APPROVED)
    OS->>MQ: 5. PUBLISH sự kiện "order.created"
    OS-->>Client: 201 Checkout Success!
    
    par Async Workers
        MQ->>IS: Bắn event "order.created"
        IS->>IS: Chạy worker trừ Tồn Kho sách
    end
```

---

### 3.9. Chức năng 9: Tự động Gửi Thông Báo (Notification Consumer)
Bất đồng bộ xử lý khối lượng lớn email. Gửi SMS/Email mà báo cáo về đơn hàng qua queue.

```mermaid
sequenceDiagram
    autonumber
    participant MQ as RabbitMQ
    participant NS as notification_service

    Note over MQ: Khi Order_Service publish sự kiện
    MQ->>NS: PUSH "order.created" payload
    NS->>NS: Phân tích payload JSON
    NS->>NS: Render nội dung mail "Cảm ơn bạn đã đặt..."
    NS->>NS: Gọi Mailer API nội bộ (Giả lập)
    NS->>NS: Append vào Bảng Notification Logs
    NS->>MQ: Trả ACK xác nhận xử lý xong
```

---

### 3.10. Chức năng 10: Xem Thống Kê & Báo Cáo Doanh Thu (Analytics Service)
Báo cáo kinh doanh dành riêng cho Admin (Staff role) lấy số liệu mua bán của toàn hệ thống.

```mermaid
sequenceDiagram
    autonumber
    actor Admin
    participant GW as Gateway
    participant AN as analytics_service

    Admin->>GW: GET /analytics/reports/revenue (Admin Token)
    GW->>GW: RBAC Kiểm tra role "staff/admin" (Thành công)
    GW->>AN: Gửi request lấy Metrics tổng
    AN->>AN: Chạy hàm queries, aggregation Doanh số
    AN-->>GW: 200 OK (JSON Chart Data)
    GW-->>Admin: Hiển thị biểu đồ Report
```

---

### Cách tạo Sequence Diagram bằng Mermaid

**Thêm vào bất kỳ file `.md` nào:**

````markdown
```mermaid
sequenceDiagram
    participant A as ServiceA
    participant B as ServiceB

    A->>B: Request
    B-->>A: Response
```
````

**Công cụ compile/render Mermaid:**
- VS Code: Cài Extension **Mermaid Preview**
- Online: [mermaid.live](https://mermaid.live)
- GitHub: Support tự động dịch Mermaid thành Graphics.

---

## 4. DEPLOY

### 4.1. Yêu cầu trước khi Deploy

- [ ] Docker Desktop đang chạy
- [ ] Không có process nào chiếm port 8000–8011, 5672, 15672
- [ ] Đã ở trong thư mục `assignment_6/`

---

### 4.2. Deploy bằng Docker Compose (cách chính)

**Lần đầu (build images + khởi động):**
```bash
docker-compose up --build
```

**Những lần sau (không cần rebuild):**
```bash
docker-compose up
```

**Chạy nền (detached mode):**
```bash
docker-compose up -d --build
```

**Dừng hệ thống:**
```bash
docker-compose down
```

**Dừng và xóa volumes (reset toàn bộ data):**
```bash
docker-compose down -v
```

---

### 4.3. Cấu hình `docker-compose.yml`

**RabbitMQ (phải khởi động trước):**
```yaml
rabbitmq:
  image: rabbitmq:3-management
  ports:
    - "5672:5672"    # AMQP
    - "15672:15672"  # Management UI
  environment:
    RABBITMQ_DEFAULT_USER: guest
    RABBITMQ_DEFAULT_PASS: guest
  healthcheck:
    test: ["CMD", "rabbitmq-diagnostics", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5
```

**API Gateway (phụ thuộc tất cả services):**
```yaml
api_gateway:
  build: ./api_gateway
  ports:
    - "8000:8000"
  volumes:
    - ./api_gateway:/app        # hot-reload code changes
  command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
  depends_on:
    - auth_service
    - book_service
    - order_service
    # ... tất cả services
```

**Service phụ thuộc RabbitMQ:**
```yaml
order_service:
  build: ./order_service
  ports:
    - "8003:8003"
  environment:
    RABBITMQ_URL: amqp://guest:guest@rabbitmq:5672/
  depends_on:
    rabbitmq:
      condition: service_healthy   # đợi RabbitMQ sẵn sàng
```

---

### 4.4. Kiểm tra sau Deploy

**Mở browser / Postman / curl:**

```bash
# 1. Kiểm tra gateway
curl http://localhost:8000/

# 2. Health check tất cả services qua gateway
curl http://localhost:8000/auth/health
curl http://localhost:8000/books/health
curl http://localhost:8000/orders/health
curl http://localhost:8000/customers/health
curl http://localhost:8000/inventory/health
curl http://localhost:8000/notifications/health

# 3. Metrics gateway
curl http://localhost:8000/metrics

# 4. Đăng nhập lấy token
curl -X POST http://localhost:8000/auth/login/customer \
  -H "Content-Type: application/json" \
  -d '{"email": "test@mail.com", "password": "password123"}'

# 5. Dùng token để gọi API
curl http://localhost:8000/books/ \
  -H "Authorization: Bearer <token_từ_bước_4>"

# 6. RabbitMQ Dashboard
# Truy cập: http://localhost:15672  (guest/guest)
```

---

### 4.5. Xem Log của từng Service

```bash
# Xem log realtime của tất cả services
docker-compose logs -f

# Xem log của một service cụ thể
docker-compose logs -f api_gateway
docker-compose logs -f order_service
docker-compose logs -f rabbitmq

# Xem 100 dòng log gần nhất
docker-compose logs --tail=100 order_service
```

---

### 4.6. Thực hiện Saga Checkout (End-to-End Test)

**Bước 1 – Đăng ký + Đăng nhập:**
```bash
# Đăng ký
curl -X POST http://localhost:8000/auth/register/customer \
  -H "Content-Type: application/json" \
  -d '{"name": "Test User", "email": "test@mail.com", "password": "password123"}'

# Đăng nhập lấy token
curl -X POST http://localhost:8000/auth/login/customer \
  -H "Content-Type: application/json" \
  -d '{"email": "test@mail.com", "password": "password123"}'
# → Lưu "access_token"
```

**Bước 2 – Thêm sách vào giỏ:**
```bash
TOKEN="eyJ..."  # token từ bước 1

curl -X POST http://localhost:8000/orders/cart/1/add \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"book_id": 1, "quantity": 2, "unit_price": 95000}'
```

**Bước 3 – Saga Checkout:**
```bash
curl -X POST http://localhost:8000/orders/checkout/saga \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "pay_method": "credit_card",
    "ship_method": "fast",
    "note": "Giao nhanh giúp mình"
  }'
```

**Bước 4 – Kiểm tra notification được tạo tự động:**
```bash
curl http://localhost:8000/notifications/ \
  -H "Authorization: Bearer $TOKEN"
# Notification được tạo bởi RabbitMQ consumer (không cần gọi API thủ công)
```

---

### 4.7. Troubleshooting thường gặp

| Vấn đề | Nguyên nhân | Giải pháp |
|--------|-------------|-----------|
| `502 Bad Gateway` | Upstream service chưa sẵn sàng | Đợi thêm vài giây, check `docker-compose logs <service>` |
| `Connection refused` trên RabbitMQ | RabbitMQ chưa khởi động xong | `order_service` dùng `depends_on: condition: service_healthy` |
| `401 Unauthorized` | Không có/sai token | Gọi `/auth/login/customer` trước để lấy token |
| `403 Forbidden` | Customer dùng staff route | Đăng nhập với tài khoản staff |
| `429 Too Many Requests` | Vượt rate limit | Đợi 60 giây, hoặc đổi IP |
| Database locked (SQLite) | Nhiều service cùng ghi | Production dùng MySQL/PostgreSQL |
| Port conflict | Port đã bị dùng | `docker-compose down` rồi `up` lại, hoặc kill process |

---

### 4.8. Tóm tắt các Port

| Service | Port local | URL |
|---------|-----------|-----|
| **Frontend Web Client** | **4000** | **http://localhost:4000** |
| API Gateway | 8000 | http://localhost:8000 |
| auth_service | 8001 | http://localhost:8001 (direct) |
| product_service | 8002 | http://localhost:8002 (direct) |
| order_service | 8003 | http://localhost:8003 (direct) |
| customer_service | 8004 | http://localhost:8004 (direct) |
| staff_service | 8005 | http://localhost:8005 (direct) |
| marketing_service | 8006 | http://localhost:8006 (direct) |
| inventory_service | 8007 | http://localhost:8007 (direct) |
| content_service | 8008 | http://localhost:8008 (direct) |
| interaction_service | 8009 | http://localhost:8009 (direct) |
| analytics_service | 8010 | http://localhost:8010 (direct) |
| notification_service | 8011 | http://localhost:8011 (direct) |
| ai_chat_service | 8012 | http://localhost:8012 (direct) |
| behavior_service | 8013 | http://localhost:8013 (direct) |
| MySQL | 3307 | localhost:3307 (password: `Duyanh090@`) |
| Neo4j UI | 7474 | http://localhost:7474 (neo4j/learnmart_graph_password) |
| RabbitMQ AMQP | 5672 | amqp://guest:guest@localhost:5672 |
| RabbitMQ UI | 15672 | http://localhost:15672 (guest/guest) |

> ⚡ **Khuyến nghị:**
> - Luôn truy cập giao diện qua **Frontend Client** (:4000) để trải nghiệm ứng dụng đầy đủ.
> - API Gateway (:8000) chịu trách nhiệm xác thực JWT + RBAC giữa frontend và các service phía sau.


---

## 5. DATABASE MIGRATION

Hệ thống được thiết kế để xử lý khởi tạo cơ sở dữ liệu (Migration) theo hai phương pháp tùy chỉnh theo môi trường:

### 5.1. Tự động (Khuyên dùng khi chạy Docker)

Khi chạy bằng Docker Compose, quá trình tạo Database và Tables được thiết kế **hoàn toàn tự động**:

1. **Auto-create Database:** Container `mysql:8.0` sẽ tự động đọc script từ thư mục `mysql-init/init.sql` ở lần chạy đầu tiên. Script này chứa các câu lệnh `CREATE DATABASE IF NOT EXISTS ...` cho toàn bộ 11 database (`auth_db`, `book_db`, `order_db`, v.v.).
2. **Auto-create Tables:** Khi các file `main.py` của từng service khởi tạo, script có định nghĩa `app.on_event("startup")` để chạy `Base.metadata.create_all(bind=engine)`. SQLAlchemy sẽ tự động dò các Class định nghĩa (models) và tự động ánh xạ tạo table dưới database mà không cần chạy lệnh phụ nào!

### 5.2. Thủ công (Khi Dev ở máy Local - không dùng Docker)

Nếu bạn muốn chạy từng file `main.py` trực tiếp ở host (máy ảo local) mà vẫn muốn khởi tạo 11 database MySQL tương ứng, project cung cấp sẵn công cụ migrate.

**Điều kiện:** MySQL Server tại máy (hoặc Docker chạy riêng MySQL ở cổng 3306) đang hoạt động với tài khoản tương ứng trong config (mặc định: `root` / `Duyanh090@`).

**Chạy Migration Script:**
Bạn có thể sử dụng 1 trong 2 file `setup_and_migrate.py` hoặc `migrate.py`. (Khuyên dùng `setup_and_migrate.py` phiên bản mới).

```bash
# Di chuyển vào gốc của thư mục assignment_6/
cd assignment_6/

# Chạy công cụ migrate thủ công
python setup_and_migrate.py
```

**Workflow của script thủ công:**
1. Tạo kết nối pymysql tới MySQL server.
2. Chạy `CREATE DATABASE IF NOT EXISTS ...` để khởi tạo 11 DB trắng.
3. Vòng lặp duyệt qua tất cả folder service (`auth_service/`, `book_service/`, ...).
4. Tại mỗi service, script dynamically import SQLAlchemy `Base` model từ `models.py` hoặc cục bộ `main.py`.
5. Gọi hàm `create_all()` để generate trực tiếp tables vào database vừa tạo. Mọi chi tiết sinh DB sẽ in thẳng ra console của bạn.
