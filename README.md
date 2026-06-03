# LearnMart Marketplace

LearnMart là project marketplace theo hướng `DDD + Microservices`, được mở rộng từ mô hình bookstore cũ sang catalog đa sản phẩm.

Hiện tại hệ thống có:
- `product_service` cho catalog chung
- `order_service` cho cart, checkout, payment, shipping, order
- `behavior_service` để lưu và aggregate hành vi người dùng
- `ai_chat_service` dùng catalog, knowledge base, RAG và behavior profile để recommend
- đã tích hợp pipeline AI Service gồm `data_user500.csv`, huấn luyện `RNN/LSTM/biLSTM`, chọn `model_best=biLSTM` và suy luận trực tiếp trong flow e-commerce

Catalog mẫu đã được mở rộng lên `10 nhóm sản phẩm` và `10 sản phẩm demo`.

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

Project hiện có 3 nguồn seed chính:
- [seed_catalog.py](/D:/This%20Semester/Analysis%20and%20Design/assignment_6_ddd_marketplace/seed_catalog.py): dữ liệu catalog dùng chung
- [seed_data.py](/D:/This%20Semester/Analysis%20and%20Design/assignment_6_ddd_marketplace/seed_data.py): seed đầy đủ dữ liệu demo toàn hệ thống
- [seed_ai_demo.py](/D:/This%20Semester/Analysis%20and%20Design/assignment_6_ddd_marketplace/seed_ai_demo.py): seed nhanh cho flow AI/behavior

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

- Nên dùng [docker-compose.yml](/D:/This%20Semester/Analysis%20and%20Design/assignment_6_ddd_marketplace/docker-compose.yml) thay cho [start_all.bat](/D:/This%20Semester/Analysis%20and%20Design/assignment_6_ddd_marketplace/start_all.bat), vì file batch này đang cũ và còn tham chiếu `BookStore`.
- Một số service vẫn còn tên trường nội bộ như `book_id` ở database/model cũ. API layer đã map tương thích sang `product_id`.
- `behavior_service` là nguồn dữ liệu hành vi cho AI recommendation và personalization.
- `ai_chat_service` hiện dùng catalog hiện tại, knowledge base và behavior snapshot để trả lời.


## AI Service Assignment

Xem thêm tài liệu triển khai chi tiết: `AI_SERVICE_ASSIGNMENT_REPORT.md`
