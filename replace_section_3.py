import codecs

new_section_3 = """## 3. 10 CHỨC NĂNG CỐT LÕI (KÈM SEQUENCE DIAGRAM)

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

"""

try:
    with codecs.open("HUONG_DAN_CHI_TIET.md", "r", "utf-8") as f:
        lines = f.readlines()

    start_idx = -1
    end_idx = -1
    for i, line in enumerate(lines):
        if line.startswith("## 3. SINH RA SEQUENCE DIAGRAM"):
            start_idx = i
        elif line.startswith("## 4. DEPLOY"):
            end_idx = i
            break

    if start_idx != -1 and end_idx != -1:
        new_lines = lines[:start_idx] + [new_section_3] + lines[end_idx:]
        with codecs.open("HUONG_DAN_CHI_TIET.md", "w", "utf-8") as f:
            f.writelines(new_lines)
        print("Updated section 3 successfully!")
    else:
        print(f"Could not find markers. start: {start_idx}, end: {end_idx}")
except Exception as e:
    print(f"Error: {e}")
