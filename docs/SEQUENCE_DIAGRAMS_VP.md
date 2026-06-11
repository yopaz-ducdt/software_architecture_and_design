# TÀI LIỆU SEQUENCE DIAGRAM CHI TIẾT (CHUẨN KIẾN TRÚC)
Tài liệu này cung cấp 10 Sequence Diagram được thiết kế riêng **có đầy đủ các layer: Người dùng -> Giao diện -> Gateway -> Controller -> Service -> Repository** cùng các hành động (message) logic cụ thể ở từng nhịp. 

Các sơ đồ này cực kỳ phù hợp để bạn tái tạo (vẽ lại) trong **Visual Paradigm**, **Draw.io**, hay **StarUML** và bỏ vào báo cáo đồ án môn học.

---

## 1. Khách Hàng Đăng Nhập & Nhận Token (Auth Service)

```mermaid
sequenceDiagram
    autonumber
    actor User as Khách Hàng (User)
    participant FE as Giao diện (Frontend)
    participant GW as API Gateway (Nginx/Kong)
    participant CTRL as Auth Controller (FastAPI)
    participant SVC as Auth Service
    participant REPO as Auth Repository

    User->>FE: 1. Nhập {email, password} & Bấm "Đăng nhập"
    FE->>GW: 2. POST /auth/login/customer {email, password}
    GW->>GW: 3. Kiểm tra cấu hình Route (Bỏ qua JWT check)
    GW->>CTRL: 4. Chuyển tiếp (Forward) -> POST /login/customer 
    CTRL->>SVC: 5. Gọi hàm authenticate(email, password)
    SVC->>REPO: 6. Truy vấn find_by_email(email)
    REPO-->>SVC: 7. Trả về đối tượng Customer (chứa hashed_password)
    SVC->>SVC: 8. Gọi verify_password(plain_pass, hashed_password)
    SVC-->>CTRL: 9. Trả kết quả Hợp lệ (True) kèm User Info
    CTRL->>CTRL: 10. Tạo JWT Access Token
    CTRL-->>GW: 11. Trả về HTTP 200 OK {access_token, user_type}
    GW-->>FE: 12. Trả về thông điệp thành công và Token
    FE->>FE: 13. Lưu Token vào LocalStorage
    FE-->>User: 14. Báo "Đăng nhập thành công" & Chuyển hướng Trang Chủ
```

---

## 2. API Gateway Kiểm tra Quyền Truy cập (RBAC) Bị Từ Chối

```mermaid
sequenceDiagram
    autonumber
    actor User as Khách Hàng (Customer)
    participant FE as Giao diện (Frontend)
    participant GW as API Gateway (Middleware)

    User->>FE: 1. Bấm nút xem trang "Quản lý kho" 
    FE->>GW: 2. GET /inventory/items (Kèm Header: Bearer <Customer_Token>)
    GW->>GW: 3. Extract Token từ Authorization Header
    GW->>GW: 4. Decode JWT Token lấy payload {user_type: "customer"}
    GW->>GW: 5. Tra cứu cấu hình Endpoint (Yêu cầu Role: "staff" hoặc "admin")
    GW->>GW: 6. So sánh Quyền hạn (customer != staff) -> Dữ liệu Không Hợp Lệ
    GW-->>FE: 7. Trả về mã lỗi HTTP 403 Forbidden ("Bạn không có quyền truy cập")
    FE-->>User: 8. Hiển thị Popup lỗi "Truy cập bị từ chối" 
```

---

## 3. Duyệt & Tìm Kiếm Theo Thể Loại (Book Service)

```mermaid
sequenceDiagram
    autonumber
    actor User as Khách Hàng
    participant FE as Giao diện (Frontend)
    participant GW as API Gateway
    participant CTRL as Book Controller
    participant SVC as Book Service
    participant REPO as Book Repository

    User->>FE: 1. Chọn thể loại "Tiểu thuyết" & Bấm "Tìm kiếm"
    FE->>GW: 2. GET /books/search?genre_id=1&skip=0&limit=20
    GW->>GW: 3. Check JWT & Rate Limiting
    GW->>CTRL: 4. Forward -> GET /search?genre_id=1
    CTRL->>SVC: 5. Gọi get_books_by_genre(genre_id, pagination)
    SVC->>REPO: 6. find_books(filters, skip, limit)
    REPO-->>SVC: 7. Trả về List[Book Model]
    SVC-->>CTRL: 8. Chuyển Model thành DTO (Schemas)
    CTRL-->>GW: 9. Trả về danh sách sách (JSON)
    GW-->>FE: 10. Trả về Response HTTP 200 OK [danh sách]
    FE->>FE: 11. Render Grid Sách HTML/CSS
    FE-->>User: 12. Hiển thị danh sách kết quả lên màn hình
```

---

## 4. Thêm Sách Vào Giỏ Hàng (Order Service)

```mermaid
sequenceDiagram
    autonumber
    actor User as Khách Hàng
    participant FE as Giao diện (Frontend)
    participant GW as API Gateway
    participant CTRL as Cart Controller
    participant SVC as Cart Service
    participant REPO as Cart Repository

    User->>FE: 1. Nhập Số Lượng = 2 & Bấm "🛒 Thêm vào giỏ"
    FE->>GW: 2. POST /orders/cart/{customer_id}/add {book_id: 1, qty: 2}
    GW->>GW: 3. Verify Access Token của khách hàng hợp lệ
    GW->>CTRL: 4. Forward -> POST /cart/{customer_id}/add
    CTRL->>SVC: 5. add_item_to_cart(customer_id, book_id, qty, price)
    SVC->>REPO: 6. find_active_cart(customer_id)
    REPO-->>SVC: 7. Trả về ActiveCart Object (hoặc None)
    SVC->>REPO: 8. create_cart() (Nếu None)
    SVC->>REPO: 9. upsert_cart_item(cart_id, book_id, qty)
    REPO-->>SVC: 10. Xác nhận Lệnh lưu Database
    SVC-->>CTRL: 11. Trả về Giỏ Hàng đã cập nhật
    CTRL-->>GW: 12. HTTP 200 OK + Cart DTO
    GW-->>FE: 13. Forward JSON
    FE->>FE: 14. Cập nhật Số đếm Card Badge trên Header
    FE-->>User: 15. Hiển thị Toast "Đã thêm vào giỏ hàng"
```

---

## 5. Viết Bình Luận & Đánh Giá 5 Sao (Interaction Service)

```mermaid
sequenceDiagram
    autonumber
    actor User as Khách Hàng
    participant FE as Giao diện (Frontend)
    participant GW as API Gateway
    participant CTRL as Interaction Controller
    participant SVC as Review Service
    participant REPO as Review Repository

    User->>FE: 1. Chọn 5 sao, Nhập nội dung bình luận & Bấm Gửi
    FE->>GW: 2. POST /interaction/reviews {book_id, rating, body}
    GW->>GW: 3. Verify Token và XSS Payload check
    GW->>CTRL: 4. Forward request tới Interaction Service
    CTRL->>SVC: 5. create_review_and_rating(book_id, customer_id, rating, body)
    SVC->>SVC: 6. Kiểm tra nội dung bình luận (Spam filters)
    SVC->>REPO: 7. INSERT INTo reviews_table () VALUES ()
    REPO-->>SVC: 8. Lưu thành công (Return Review ID)
    SVC-->>CTRL: 9. Trả về Review Details DTO
    CTRL-->>GW: 10. HTTP 201 Created
    GW-->>FE: 11. Trả về thông điệp thành công
    FE->>FE: 12. Gắn Bình luận mới vào cuối trang
    FE-->>User: 13. Hiển thị thông báo "Cảm ơn đánh giá của bạn"
```

---

## 6. Cập Nhật Hồ Sơ Của Khách Hàng (Customer Service)

```mermaid
sequenceDiagram
    autonumber
    actor User as Khách Hàng
    participant FE as Giao diện (Frontend)
    participant GW as API Gateway
    participant CTRL as Customer Controller
    participant SVC as Profile Service
    participant REPO as Profile Repository

    User->>FE: 1. Gõ Số ĐT mới, Sở thích & Bấm "Lưu thay đổi"
    FE->>GW: 2. PUT /customers/profile/{customer_id} {phone, bio}
    GW->>CTRL: 3. Đã Auth -> Đẩy request sang Customer Service
    CTRL->>SVC: 4. update_profile(customer_id, phone, bio)
    SVC->>REPO: 5. Gửi lệnh cập nhật dữ liệu Customers DB (UPDATE)
    REPO-->>SVC: 6. Xác nhận cập nhật số Data (Row affected = 1)
    SVC-->>CTRL: 7. Parse Data -> Profile Model
    CTRL-->>GW: 8. Trả Code 200 OK + Payload Profile 
    GW-->>FE: 9. Chuyển tiếp Response
    FE->>FE: 10. Cập nhật Data State trên Javascript
    FE-->>User: 11. Toast "Cập nhật hồ sơ thành công"
```

---

## 7. Kiểm Tra & Áp Dụng Mã Giảm Giá (Marketing Service)

```mermaid
sequenceDiagram
    autonumber
    actor User as Khách Hàng
    participant FE as Giao diện (Frontend)
    participant GW as API Gateway
    participant CTRL as Marketing Controller
    participant SVC as Promotion Service
    participant REPO as Coupon Repository

    User->>FE: 1. Nhập Mã "SALE20" trong Giỏ Hàng & Bấm "Áp Dụng"
    FE->>GW: 2. GET /marketing/coupons/validate/SALE20?total=...
    GW->>CTRL: 3. Forward request vào Marketing Service
    CTRL->>SVC: 4. validate_coupon_code(code, order_total)
    SVC->>REPO: 5. find_coupon_by_code('SALE20')
    REPO-->>SVC: 6. Trả về Database object (CouponModel)
    SVC->>SVC: 7. Kiểm tra: Hạn sử dụng, Min Order Value, Max uses
    SVC-->>CTRL: 8. Hợp lệ -> Trả về Tỷ Lệ Giảm Giá (20%)
    CTRL-->>GW: 9. HTTP 200 OK {discount_value, discount_percent}
    GW-->>FE: 10. Forward tới UI
    FE->>FE: 11. Tính toán lại Tổng tiền (Grand Total -= Discount)
    FE-->>User: 12. Hiển thị "Mã hợp lệ! Bạn tiết kiệm 20.000đ"
```

---

## 8. Đặt Hàng Thanh Toán Bằng Saga Pattern (Order Service)

```mermaid
sequenceDiagram
    autonumber
    actor User as Khách Hàng
    participant FE as Giao diện (Frontend)
    participant GW as API Gateway
    participant CTRL as Order Controller (Saga Orch)
    participant SVC as Order Service (Saga Logic)
    participant REPO as Order Repository
    participant MQ as Message Broker (RabbitMQ)

    User->>FE: 1. Xác nhận địa chỉ & Phí ship -> Bấm "Xác nhận đặt hàng"
    FE->>GW: 2. POST /orders/checkout {pay_method, ship_method}
    GW->>CTRL: 3. Forward POST /checkout
    CTRL->>SVC: 4. execute_checkout_saga(customer_id, pay, ship)
    SVC->>REPO: 5. Tính toán giỏ hàng & Tính tổng
    REPO-->>SVC: 6. Trả về Items
    SVC->>REPO: 7. Tạo Order(status=PENDING)
    SVC->>REPO: 8. Phase 1: Tạo Payment Invoice (RESERVED)
    SVC->>REPO: 9. Phase 2: Tạo Lệnh Shipping (RESERVED)
    SVC->>REPO: 10. Phase 3: Hoàn thành duyệt đơn -> UPDATE Order=APPROVED
    REPO-->>SVC: 11. Các Table Insert thành công
    SVC->>MQ: 12. PUBLISH Event "order.created" {order_id, sum}
    SVC-->>CTRL: 13. Phân luồng luân chuyển hoàn tất
    CTRL-->>GW: 14. HTTP 201 Created {order_id, total}
    GW-->>FE: 15. Push JSON về trình duyệt
    FE-->>User: 16. Màn hình Cảm ơn "Đặt hàng thành công!"
```

---

## 9. Lắng Nghe Event Async Để Gửi Email (Notification Service)

```mermaid
sequenceDiagram
    autonumber
    participant MQ as Message Broker (RabbitMQ)
    participant CTRL as Amqp Consumer Listener
    participant SVC as Notification Service
    participant REPO as Notification DB

    Note over MQ: Khi Order Service vừa Publish "order.created"
    MQ->>CTRL: 1. Push payload JSON vào Queue "notification_queue"
    CTRL->>SVC: 2. Gọi process_new_order_event(payload)
    SVC->>SVC: 3. Phân rã dữ liệu order, lấy customer email
    SVC->>SVC: 4. Gọi Template Engine render HTML "Cảm ơn bạn mua hàng!"
    SVC->>SVC: 5. Gọi Tích hợp Mail API ngoài (Google SMTP, v.v) Gửi Thư
    SVC->>REPO: 6. INSERT Log gửi Email thành công -> history_table
    REPO-->>SVC: 7. Xong
    SVC-->>CTRL: 8. Hoàn tất chu trình
    CTRL->>MQ: 9. Trả tín hiệu ACK -> Đánh dấu Xóa Message khỏi Queue
```

---

## 10. Xem Báo Cáo Doanh Thu Hệ Thống (Analytics API)

```mermaid
sequenceDiagram
    autonumber
    actor User as Nhân Viên (Admin)
    participant FE as Staff Dashboard UI
    participant GW as API Gateway
    participant CTRL as Analytics Controller
    participant SVC as Data Analysis Service
    participant REPO as Analytics DB (Data Lake)

    User->>FE: 1. Bấm mở "Thống kê Doanh Thu"
    FE->>GW: 2. GET /analytics/sales (Kèm JWT Staff Role)
    GW->>GW: 3. Decode Token, RBAC pass (Admin)
    GW->>CTRL: 4. Forward GET /sales sang Analytics
    CTRL->>SVC: 5. generate_revenue_report(kì hạn: tuần này)
    SVC->>REPO: 6. Thực thi SQL Aggregation (SUM total) GroupBy Days
    REPO-->>SVC: 7. Trả List các Record (Ngày - Tiền Lãi)
    SVC->>SVC: 8. Map sang Chart DTO & Tính chỉ số tăng trưởng (%)
    SVC-->>CTRL: 9. Trả về Data Structure (Dataset)
    CTRL-->>GW: 10. HTTP 200 OK + JSON
    GW-->>FE: 11. Forward response
    FE->>FE: 12. Javascript Dùng Biểu đồ (vd: Chart.js) Render HTML Canvas
    FE-->>User: 13. Hiển thị Đồ Thị Doanh Số Sinh Động
```
