# Kiến Trúc Hệ Thống: LearnMart Marketplace

## 1. Tổng quan

**LearnMart Marketplace** là hệ thống thương mại điện tử được phát triển theo hướng **Domain-Driven Design (DDD)** và **Microservices**. Dự án được mở rộng từ mô hình bookstore cũ sang một marketplace đa sản phẩm, trong đó catalog hiện tại hỗ trợ 10 nhóm sản phẩm khác nhau như sách, dụng cụ học tập, đồ chơi, gói quà, ba lô, bình nước và các phụ kiện học tập.

Đặc điểm chính:
- Triển khai bằng `Docker Compose`
- `API Gateway` là điểm vào duy nhất ở cổng `8000`
- Mỗi service có database riêng theo nguyên tắc `database per service`
- Giao tiếp kết hợp giữa `REST` và `RabbitMQ`
- Có `AI Chat Service` và `Behavior Service` để phục vụ recommendation và personalization

## 2. Thành phần hệ thống

### 2.1. Infrastructure Layer

- `mysql`
  - Cổng host: `3307`
  - Lưu toàn bộ database cho các service
- `rabbitmq`
  - AMQP: `5672`
  - Management UI: `15672`
  - Dùng cho event-driven flow và các tác vụ bất đồng bộ

### 2.2. Gateway & Frontend

- `api_gateway`
  - Cổng: `8000`
  - Đóng vai trò reverse proxy và entry point cho frontend
  - Định tuyến request đến các microservice nội bộ
- `frontend`
  - Cổng: `4000`
  - Giao diện người dùng cho customer, staff và popup AI assistant

## 3. Danh sách microservices

Hệ thống hiện tại có các backend service sau:

### 3.1. Auth Service
- Cổng: `8001`
- Bounded context: `Identity / Access`
- Chức năng:
  - đăng ký customer
  - đăng nhập customer và staff
  - xác thực token
  - phân quyền cơ bản

### 3.2. Product Service
- Cổng: `8002`
- Bounded context: `Catalog`
- Chức năng:
  - quản lý `categories`
  - quản lý `brands`
  - quản lý `product types`
  - quản lý `products`
  - quản lý `ratings` và `reviews`
- Đây là service áp dụng DDD rõ nhất trong repo, với các lớp:
  - `domain`
  - `application`
  - `infrastructure`
  - `presentation`

### 3.3. Order Service
- Cổng: `8003`
- Bounded context: `Order & Checkout`
- Chức năng:
  - quản lý `cart` và `cart_item`
  - checkout
  - tạo `order` và `order_item`
  - quản lý `payment`
  - quản lý `shipping`
  - quản lý `refund`

Lưu ý:
- Trong project hiện tại, `cart`, `payment` và `shipping` vẫn nằm trong `order_service`
- Đây là lựa chọn thực dụng vì chúng thuộc cùng flow nghiệp vụ checkout

### 3.4. Customer Service
- Cổng: `8004`
- Bounded context: `Customer Profile`
- Chức năng:
  - quản lý hồ sơ khách hàng
  - quản lý địa chỉ nhận hàng
  - wishlist
  - newsletter
  - customer preferences

### 3.5. Staff Service
- Cổng: `8005`
- Bounded context: `Staff / Admin`
- Chức năng:
  - phòng ban
  - thông tin nhân sự nội bộ

### 3.6. Marketing Service
- Cổng: `8006`
- Bounded context: `Promotions`
- Chức năng:
  - coupon
  - promotion
  - flash sale
  - membership tiers
  - referral code
  - bundle/discount logic mở rộng

### 3.7. Inventory Service
- Cổng: `8007`
- Bounded context: `Inventory & Procurement`
- Chức năng:
  - warehouse
  - supplier
  - purchase order
  - inventory log
  - inventory alert

### 3.8. Content Service
- Cổng: `8008`
- Bounded context: `Content / CMS`
- Chức năng:
  - banner
  - collection
  - blog post
  - nội dung marketing hiển thị trên frontend

### 3.9. Interaction Service
- Cổng: `8009`
- Bounded context: `Interaction / Loyalty`
- Chức năng:
  - gift card
  - loyalty-related flows
  - subscription-related flows

### 3.10. Analytics Service
- Cổng: `8010`
- Bounded context: `Analytics`
- Chức năng:
  - daily sales summary
  - search history
  - recently viewed

### 3.11. Notification Service
- Cổng: `8011`
- Bounded context: `Notification`
- Chức năng:
  - notification
  - email template
  - các tác vụ giao tiếp nội bộ hoặc gửi thông báo

### 3.12. AI Chat Service
- Cổng: `8012`
- Bounded context: `AI Assistant`
- Chức năng:
  - trả lời câu hỏi của người dùng
  - recommend sản phẩm
  - dùng `knowledge base`
  - dùng `RAG`
  - dùng snapshot từ các service khác để cá nhân hóa

Đặc điểm:
- Không sở hữu database nghiệp vụ riêng
- Đóng vai trò orchestrator và inference layer

### 3.13. Behavior Service
- Cổng: `8013`
- Bounded context: `Behavior Intelligence`
- Chức năng:
  - lưu raw behavior events
  - aggregate thành behavior profile
  - cung cấp feature snapshot cho AI

Các API chính:
- `POST /events`
- `GET /events/{customer_id}`
- `GET /profiles/{customer_id}`
- `POST /profiles/{customer_id}/refresh`
- `GET /features/{customer_id}`

Các event điển hình:
- `search_performed`
- `product_viewed`
- `wishlist_added`
- `cart_added`
- `checkout_started`
- `order_completed`

Các output chính:
- `persona`
- `price_sensitivity`
- `purchase_intent`
- `preferred_categories`
- `next_best_action`
- `feature_values`

## 4. Catalog hiện tại

Hệ thống hiện seed sẵn 10 nhóm sản phẩm:
- `Sách`
- `Dụng cụ học tập`
- `Đồ chơi`
- `Gói quà`
- `Ba lô`
- `Bình nước`
- `Đồ điện tử học tập`
- `Mỹ thuật`
- `Đồ trang trí bàn học`
- `Đồ lưu niệm`

Catalog demo có 10 sản phẩm mẫu tương ứng, phục vụ cho:
- frontend demo
- AI recommendation
- behavior tracking
- marketing seed

## 5. Giao tiếp giữa các service

### 5.1. Synchronous communication

Các service giao tiếp đồng bộ qua `REST API` khi cần đọc dữ liệu tức thời hoặc xử lý đồng bộ:
- Frontend gọi `api_gateway`
- `api_gateway` chuyển tiếp đến các service nội bộ
- `ai_chat_service` gọi:
  - `product_service`
  - `order_service`
  - `customer_service`
  - `analytics_service`
  - `marketing_service`
  - `behavior_service`

Ví dụ:
- lấy danh sách sản phẩm
- lấy cart summary
- lấy recent views
- lấy behavior features
- lấy promotions/coupons

### 5.2. Asynchronous communication

`RabbitMQ` được dùng cho các luồng bất đồng bộ và event-driven:
- `order_service` có thể phát event khi order được tạo
- `inventory_service` và `notification_service` có thể subscribe để phản ứng
- mô hình này phù hợp với Saga hoặc eventual consistency trong các bước checkout

## 6. Luồng AI recommendation hiện tại

Luồng AI hiện tại hoạt động theo hướng:

1. User gửi câu hỏi từ frontend
2. `ai_chat_service` lấy dữ liệu từ:
   - `product_service`
   - `customer_service`
   - `order_service`
   - `analytics_service`
   - `marketing_service`
   - `behavior_service`
3. `ai_chat_service` tạo `user snapshot`
4. Snapshot được bổ sung bởi:
   - lịch sử xem gần đây
   - wishlist
   - cart summary
   - order history
   - search history
   - behavior profile
5. `ai_chat_service` dùng:
   - `behavior_model`
   - `knowledge base`
   - `RAG chunk retrieval`
6. Kết quả trả về gồm:
   - câu trả lời
   - top product recommendations
   - reasoning context phù hợp với hành vi người dùng

## 7. Knowledge Base và RAG

`ai_chat_service` hiện dùng knowledge base dạng markdown trong thư mục `kb_docs`.

Nội dung chính của KB:
- nguyên tắc recommendation
- coupon và promotion
- cart, checkout, payment, shipping

RAG hiện tại:
- không vectorize nguyên file thô như trước
- chia tài liệu theo `heading` và `paragraph chunk`
- retrieval chính xác hơn cho câu hỏi policy và recommendation

## 8. Behavior-driven personalization

`behavior_service` là phần mở rộng mới giúp hệ thống AI phù hợp hơn với marketplace hiện tại.

Thay vì chỉ dựa vào search history và recently viewed, AI giờ có thêm:
- persona của khách hàng
- mức nhạy cảm giá
- tín hiệu mua hàng
- nhóm sản phẩm ưa thích
- hành động gợi ý tiếp theo

Ví dụ:
- `deal_hunter` -> ưu tiên coupon, flash sale
- `high_intent_buyer` -> ưu tiên bundle hoặc sản phẩm liên quan
- `loyal_member` -> gợi ý membership hoặc ưu đãi cao cấp

## 9. Nguyên tắc kiến trúc đang áp dụng

- `Database per service`
- `Soft reference by ID`
- `API Gateway pattern`
- `Microservices with bounded contexts`
- `DDD cho Product Service`
- `Stateless AI orchestration`
- `Behavior intelligence` tách khỏi `ai_chat_service`

## 10. Ghi chú tương thích

- Một số service cũ vẫn còn tên trường nội bộ như `book_id` trong model/database
- Ở API layer, project đã map sang `product_id` để giữ giao diện nhất quán theo marketplace
- Vì vậy hệ thống hiện là `product marketplace` ở mức API và frontend, dù bên trong vẫn còn một số legacy naming

## 11. Kết luận

Kiến trúc hiện tại của LearnMart đã vượt ra khỏi mô hình bookstore ban đầu và trở thành một marketplace đa sản phẩm có hỗ trợ AI cá nhân hóa. Trọng tâm hiện nay của hệ thống là:
- catalog đa sản phẩm
- checkout flow đầy đủ
- marketing và analytics
- AI recommendation theo behavior

Đây là một kiến trúc phù hợp cho bài toán assignment theo hướng DDD + Microservices, đồng thời đủ linh hoạt để mở rộng thêm payment gateway, shipping integration, recommendation pipeline hoặc event-driven saga phức tạp hơn trong tương lai.
