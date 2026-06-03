# AI Service Assignment Implementation

Tài liệu này map trực tiếp với yêu cầu trong file PDF bài nộp. File PDF yêu cầu:
- sinh `data_user500.csv` với 500 users và 8 behaviors
- huấn luyện 3 mô hình `RNN`, `LSTM`, `biLSTM`
- tạo `KB_Graph` với `Neo4j`
- xây dựng `RAG + chat`
- tích hợp vào hệ e-commerce, hiển thị ở danh sách hàng khi search / add to cart và giao diện chat riêng

## 1. Dataset 500 users + 8 behaviors

Đã thêm script:
- `ai_pipeline/generate_user_behavior_data.py`

Output:
- `ai_chat_service/data/data_user500.csv`

8 behaviors trong dataset:
1. `search`
2. `view`
3. `click`
4. `add_to_cart`
5. `wishlist`
6. `coupon_view`
7. `checkout`
8. `purchase`

Mỗi dòng gồm:
- `user_id`
- `session_id`
- `step`
- `timestamp`
- `product_id`
- `category_name`
- `action`
- `price`
- `quantity`
- `query`
- `persona_label`
- `next_best_action`
- `price_sensitivity`

## 2. Huấn luyện 3 mô hình RNN / LSTM / biLSTM

Đã thêm script:
- `ai_pipeline/train_sequence_models.py`

Artifacts được tạo:
- `ai_chat_service/models/rnn_sequence_model.pt`
- `ai_chat_service/models/lstm_sequence_model.pt`
- `ai_chat_service/models/bilstm_sequence_model.pt`
- `ai_chat_service/models/model_best.pt`
- `ai_chat_service/models/model_best_meta.json`
- `ai_chat_service/reports/model_comparison.png`
- `ai_chat_service/reports/rnn_loss_curve.png`
- `ai_chat_service/reports/lstm_loss_curve.png`
- `ai_chat_service/reports/bilstm_loss_curve.png`
- `ai_chat_service/reports/sequence_model_report.json`

Kết quả hiện tại trên synthetic dataset:
- `RNN`: weighted F1 trung bình = `0.4834`
- `LSTM`: weighted F1 trung bình = `0.4858`
- `biLSTM`: weighted F1 trung bình = `0.5112`

Mô hình tốt nhất:
- `model_best = biLSTM`

Lý do chọn:
- `biLSTM` có weighted F1 trung bình cao nhất cho 2 đầu ra `persona` và `next_best_action`
- mô hình tận dụng tốt hơn ngữ cảnh hai chiều của chuỗi hành vi

## 3. Knowledge Graph với Neo4j

Project đã có sẵn hạ tầng `Neo4j` trong `docker-compose.yml`.

Phần graph được tích hợp qua:
- `ai_chat_service/graph_store.py`
- `behavior_service/graph_sync.py`

Các node / relation chính đang sync:
- `User`
- `Product`
- `Category`
- `Brand`
- `ProductType`
- `Coupon`
- `Promotion`
- `FlashSale`
- `MembershipTier`
- quan hệ hành vi và quan hệ marketing liên quan

## 4. RAG + Chat

Thành phần RAG/chat hiện có trong project:
- `ai_chat_service/kb_store.py`: TF-IDF retrieval cho KB docs
- `ai_chat_service/graph_store.py`: lấy context từ Neo4j graph
- `ai_chat_service/advisor.py`: hợp nhất behavior + KB + graph để tạo answer
- `frontend/assistant.js`: giao diện chat riêng, không dùng UI mặc định của ChatGPT

## 5. Tích hợp model_best vào hệ e-commerce

Đã thêm file mới:
- `ai_chat_service/sequence_behavior_model.py`

Logic tích hợp:
- load `model_best.pt`
- build sequence từ dữ liệu thật của customer (`searches`, `recent_views`, `wishlist`, `cart`, `orders`)
- suy luận `persona` và `next_best_action`
- nếu không có model hoặc không đủ chuỗi thì fallback về behavior model cũ

Các file đã sửa để tích hợp:
- `ai_chat_service/advisor.py`
- `ai_chat_service/main.py`
- `frontend/api.js`
- `frontend/app.js`

### 5.1. Hiển thị ở danh sách hàng khi customer search
Khi khách hàng search tại màn hình sản phẩm:
- frontend track event `search_performed`
- gọi `AI.ask(...)`
- hiển thị thêm block `AI gợi ý theo từ khóa tìm kiếm`

### 5.2. Hiển thị khi khách hàng thêm vào giỏ / xem giỏ hàng
Khi khách hàng add to cart hoặc vào cart:
- frontend track event `cart_added`
- gọi AI service để lấy cross-sell / bundle suggestion
- render block `AI gợi ý thêm trong giỏ hàng`

### 5.3. Giao diện chat riêng
Popup chatbot vẫn là giao diện custom của project:
- file `frontend/assistant.js`
- không dùng giao diện mặc định của ChatGPT

## 6. Cách chạy lại toàn bộ pipeline

### Bước 1. Generate data
```bash
python ai_pipeline/generate_user_behavior_data.py
```

### Bước 2. Train 3 models và chọn model_best
```bash
python ai_pipeline/train_sequence_models.py
```

### Bước 3. Chạy hệ thống e-commerce
```bash
docker compose up --build
```

### Bước 4. Seed demo data
```bash
python seed_data.py
python seed_ai_demo.py
```

## 7. Checklist theo đúng đề PDF

- [x] Sinh `data_user500.csv` với 500 users và 8 behaviors
- [x] Xây dựng 3 mô hình `RNN`, `LSTM`, `biLSTM`
- [x] Đánh giá 3 mô hình và chọn `model_best`
- [x] Có plots để visualize kết quả
- [x] Xây dựng `KB_Graph` với `Neo4j`
- [x] Xây dựng `RAG + chat` dựa trên `KB_Graph`
- [x] Tích hợp vào hệ e-commerce
- [x] Hiển thị ở màn hình danh sách hàng khi search / add to cart
- [x] Có giao diện chat riêng cho user
