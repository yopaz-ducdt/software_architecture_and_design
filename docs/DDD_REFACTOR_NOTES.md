# DDD Refactor Notes

## Nguyên tắc áp dụng
- Một `product_service` duy nhất cho toàn bộ catalog.
- Không tách service theo category.
- Category chỉ là dữ liệu.
- `product_service` được tổ chức theo các lớp `domain`, `application`, `infrastructure`, `presentation`.

## Danh mục mới
- Sách
- Dụng cụ học tập
- Đồ chơi
- Gói quà

## Thay đổi chính
- `book_service` được thay bằng `product_service` trong `docker-compose.yml`.
- API gateway map `/products/*` vào `product_service`.
- Frontend chuyển route chính sang `#/products`.
- AI chatbot chuyển từ gợi ý sách sang gợi ý sản phẩm marketplace.
- Seed dữ liệu demo dùng tài khoản `demo@learnmart.vn / demo123`.

## Product service structure
```text
product_service/
  app.py
  database.py
  modules/catalog/
    domain/
    application/
    infrastructure/
      models/
      repositories/
      querysets/
    presentation/api/
      serializers/
      views/
    seeds/
```
