# LearnMart

LearnMart là project marketplace theo hướng `DDD + Microservices`, được mở rộng từ mô hình bookstore cũ sang catalog đa sản phẩm.

Hệ thống được thiết kế bao gồm nhiều vi dịch vụ (microservices) chuyên biệt nhằm xử lý toàn diện các nghiệp vụ e-commerce và AI. Các điểm nhấn nổi bật của dự án bao gồm:

- **E-commerce cốt lõi:** Các dịch vụ như `product_service` và `order_service` đảm nhiệm việc quản lý danh mục sản phẩm, giỏ hàng, quy trình thanh toán (checkout) và vận chuyển.
- **Phân tích hành vi:** `behavior_service` thu thập và tổng hợp dữ liệu tương tác của người dùng theo thời gian thực.
- **AI & Trợ lý thông minh:** Tích hợp hoàn chỉnh pipeline AI (huấn luyện các mô hình `RNN/LSTM/biLSTM` từ tập dữ liệu và triển khai suy luận trực tiếp với model `biLSTM`). Đồng thời, `ai_chat_service` kết hợp Knowledge Base, RAG và hồ sơ hành vi người dùng (behavior profile) để tạo ra các đề xuất mua sắm mang tính cá nhân hoá cao.

Đi kèm với hệ thống là bộ dữ liệu (Catalog) mẫu đã được mở rộng lên **10 nhóm sản phẩm** cùng dữ liệu hàng hoá phong phú, sẵn sàng phục vụ cho việc kiểm thử các luồng nghiệp vụ và AI.

## Services

Các service chính:
- `auth_service` on `8001`
- `product_service` on `8002`
- `order_service` on `8003`
- `customer_service` on `8004`
- `staff_service` on `8005`
- `marketing_service` on `8006`
- `inventory_service` on `8007`
- `content_service` on `8008`
- `interaction_service` on `8009`
- `analytics_service` on `8010`
- `notification_service` on `8011`
- `ai_chat_service` on `8012`
- `behavior_service` on `8013`
- `api_gateway` on `8000`
- `frontend` on `4000`

Infrastructure:
- `MySQL` on host port `3307`
- `RabbitMQ` on `5672`
- `RabbitMQ Management UI` on `15672`

## Catalog Demo

10 nhóm sản phẩm mẫu:
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

## Run Project

Yêu cầu:
- `Docker Desktop`
- `docker compose`
- nếu muốn chạy seed từ host: cần có `python` và package `requests`

Chạy toàn bộ hệ thống:

```bash
docker compose up --build
```

Chạy nền:

```bash
docker compose up -d --build
```

Dừng hệ thống:

```bash
docker compose down
```

## Seed Data

Project hiện có 4 nguồn seed chính:
- [seed_catalog.py](./seed_catalog.py): dữ liệu catalog dùng chung
- [seed_data.py](./seed_data.py): seed đầy đủ dữ liệu demo toàn hệ thống
- [seed_ai_demo.py](./seed_ai_demo.py): seed nhanh cho flow AI/behavior
- [seed_products_bulk.py](./seed_products_bulk.py): seed số lượng lớn sản phẩm vào database

Seed đầy đủ:

```bash
python seed_data.py
```

Seed thêm dữ liệu AI demo:

```bash
python seed_ai_demo.py
```

`seed_data.py` hiện sẽ seed các phần:
- account customer và staff
- categories, product types, brands, products
- ratings và reviews
- coupon, promotion, flash sale, membership tiers
- customer profile, address, wishlist
- warehouse, supplier, banner, blog, gift card
- analytics search history và recently viewed
- behavior events và behavior profile

## URLs

Truy cập chính:
- Frontend: `http://localhost:4000`
- API Gateway: `http://localhost:8000`
- RabbitMQ UI: `http://localhost:15672`

Swagger docs:
- `http://localhost:8001/docs`
- `http://localhost:8002/docs`
- `http://localhost:8003/docs`
- `http://localhost:8004/docs`
- `http://localhost:8005/docs`
- `http://localhost:8006/docs`
- `http://localhost:8007/docs`
- `http://localhost:8008/docs`
- `http://localhost:8009/docs`
- `http://localhost:8010/docs`
- `http://localhost:8011/docs`
- `http://localhost:8012/docs`
- `http://localhost:8013/docs`

## Demo Accounts

Customer:
- email: `demo@learnmart.vn`
- password: `demo123`

Staff:
- username: `admin`
- password: `admin123`

## Notes

- Nên dùng [docker-compose.yml](./docker-compose.yml) thay cho [start_all.bat](./start_all.bat) (Windows) hoặc [start_all.sh](./start_all.sh) (macOS/Linux). File batch/shell này đang cũ và còn tham chiếu `BookStore`.
- Một số service vẫn còn tên trường nội bộ như `book_id` ở database/model cũ. API layer đã map tương thích sang `product_id`.
- `behavior_service` là nguồn dữ liệu hành vi cho AI recommendation và personalization.
- `ai_chat_service` hiện dùng catalog hiện tại, knowledge base và behavior snapshot để trả lời.

## Tài liệu (Documentation)

Dự án đi kèm nhiều tài liệu chi tiết, vui lòng xem thêm:
- [HUONG_DAN_CHI_TIET.md](./HUONG_DAN_CHI_TIET.md) - Hướng dẫn chi tiết tổng thể
- [HUONG_DAN_CHAY_MACOS.md](./HUONG_DAN_CHAY_MACOS.md) - Dành riêng cho người dùng macOS
- [ONBOARDING_GUIDE.md](./ONBOARDING_GUIDE.md) - Hướng dẫn onboarding cho developer mới
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Kiến trúc hệ thống
- [AI_CHATBOT_GUIDE.md](./AI_CHATBOT_GUIDE.md) - Hướng dẫn về dịch vụ AI Chatbot
- [SEQUENCE_DIAGRAMS_VP.md](./SEQUENCE_DIAGRAMS_VP.md) - Các biểu đồ tuần tự


## AI Service Assignment

Xem thêm tài liệu triển khai chi tiết: `AI_SERVICE_ASSIGNMENT_REPORT.md`
