# Kiến Thức AI Được Sử Dụng Trong `ai_chat_service`

Tài liệu này mô tả ngắn gọn các thành phần AI đang được dùng thật trong project hiện tại, tập trung vào 3 phần:

- `Model`
- `Knowledge Base`
- `RAG`

## 1. Tổng Quan

`ai_chat_service` là service chịu trách nhiệm:

- trả lời câu hỏi của người dùng qua chatbot
- gợi ý sản phẩm cá nhân hóa
- dùng dữ liệu hành vi để điều chỉnh recommendation
- dùng knowledge base để hỗ trợ trả lời các câu hỏi chính sách và mua sắm

Điểm quan trọng:

- service này hiện **không dùng LLM cloud** như OpenAI hay Gemini
- logic AI trong project hiện tại là sự kết hợp giữa:
  - mô hình ML cục bộ cho hành vi người dùng
  - knowledge base viết bằng file Markdown
  - cơ chế retrieval đơn giản kiểu RAG dựa trên `TF-IDF + cosine similarity`
  - rule-based response generation trong [ai_chat_service/advisor.py](D:/This%20Semester/Analysis%20and%20Design/assignment_6_ddd_marketplace/ai_chat_service/advisor.py)

## 2. Model

Phần model chính nằm ở [ai_chat_service/behavior_model.py](D:/This%20Semester/Analysis%20and%20Design/assignment_6_ddd_marketplace/ai_chat_service/behavior_model.py).

### 2.1. Mục đích của model

Model này dùng để suy ra hồ sơ hành vi của người dùng nhằm phục vụ:

- recommendation
- ưu tiên coupon hay membership
- xác định người dùng đang ở trạng thái mua sớm hay chỉ đang tham khảo
- hỗ trợ chatbot trả lời phù hợp hơn với hành vi hiện tại

### 2.2. Input feature

Model sử dụng các feature hành vi như:

- `search_count`
- `view_count`
- `wishlist_count`
- `cart_item_count`
- `order_count`
- `avg_order_value`
- `total_spent`
- `promo_keyword_count`
- `membership_points`
- `preferred_genre_count`

Các feature này được tổng hợp từ nhiều service trong [ai_chat_service/data_fetcher.py](D:/This%20Semester/Analysis%20and%20Design/assignment_6_ddd_marketplace/ai_chat_service/data_fetcher.py), gồm:

- `analytics_service`
- `customer_service`
- `order_service`
- `marketing_service`
- `behavior_service`

### 2.3. Output của model

Model trả về 4 đầu ra chính qua class `BehaviorOutputs`:

- `persona`
- `price_sensitivity`
- `next_best_action`
- `purchase_intent`

Ví dụ:

- `persona = deal_hunter`
- `price_sensitivity = high`
- `next_best_action = push_coupon`
- `purchase_intent = 0.78`

### 2.4. Thuật toán đang dùng

Project hiện tại dùng các mô hình `scikit-learn`:

- `MLPClassifier` cho:
  - `persona`
  - `price_sensitivity`
  - `next_best_action`
- `MLPRegressor` cho:
  - `purchase_intent`

Các model đều được bọc trong `Pipeline` với:

- `StandardScaler`
- rồi đến `MLPClassifier` hoặc `MLPRegressor`

### 2.5. Dữ liệu train

Hiện tại model không train từ dữ liệu production thật, mà dùng dữ liệu mô phỏng được sinh trong code:

- hàm `_sample_row(...)`
- file output mock: [ai_chat_service/data/mock_behavior_training.csv](D:/This%20Semester/Analysis%20and%20Design/assignment_6_ddd_marketplace/ai_chat_service/data/mock_behavior_training.csv)

Khi service khởi động:

- nếu đã có model bundle thì load từ [ai_chat_service/models/behavior_bundle.joblib](D:/This%20Semester/Analysis%20and%20Design/assignment_6_ddd_marketplace/ai_chat_service/models/behavior_bundle.joblib)
- nếu chưa có thì tự train và lưu lại

### 2.6. Heuristic bổ sung

Ngoài output từ neural network, project còn thêm heuristic rule để ổn định kết quả.

Ví dụ:

- ít tương tác và chưa có đơn hàng thì ép về `new_explorer`
- có nhiều từ khóa khuyến mãi thì ưu tiên `deal_hunter`
- đã có cart hoặc wishlist mạnh thì đẩy lên `high_intent_buyer`

Nghĩa là system hiện tại là kiểu:

- `ML model + rule-based adjustment`

thay vì phụ thuộc hoàn toàn vào model học máy.

## 3. Knowledge Base

Knowledge base nằm trong thư mục [ai_chat_service/kb_docs](D:/This%20Semester/Analysis%20and%20Design/assignment_6_ddd_marketplace/ai_chat_service/kb_docs).

Các file hiện có gồm:

- [recommendation_principles.md](D:/This%20Semester/Analysis%20and%20Design/assignment_6_ddd_marketplace/ai_chat_service/kb_docs/recommendation_principles.md)
- [coupon_and_promotion.md](D:/This%20Semester/Analysis%20and%20Design/assignment_6_ddd_marketplace/ai_chat_service/kb_docs/coupon_and_promotion.md)
- [membership_faq.md](D:/This%20Semester/Analysis%20and%20Design/assignment_6_ddd_marketplace/ai_chat_service/kb_docs/membership_faq.md)
- [return_policy.md](D:/This%20Semester/Analysis%20and%20Design/assignment_6_ddd_marketplace/ai_chat_service/kb_docs/return_policy.md)
- [shipping_policy.md](D:/This%20Semester/Analysis%20and%20Design/assignment_6_ddd_marketplace/ai_chat_service/kb_docs/shipping_policy.md)
- [cart_checkout_payment.md](D:/This%20Semester/Analysis%20and%20Design/assignment_6_ddd_marketplace/ai_chat_service/kb_docs/cart_checkout_payment.md)

### 3.1. Vai trò của knowledge base

Knowledge base dùng để chứa kiến thức tĩnh hoặc bán tĩnh, ví dụ:

- nguyên tắc tư vấn sản phẩm
- coupon và khuyến mãi
- membership
- vận chuyển
- đổi trả
- cart, checkout, payment

Phần này giúp chatbot:

- trả lời nhất quán hơn
- không phụ thuộc hoàn toàn vào hard-code
- dễ cập nhật bằng cách sửa file `.md`

### 3.2. Đặc điểm hiện tại

Knowledge base của project hiện tại:

- được lưu cục bộ dưới dạng Markdown
- dễ đọc, dễ sửa
- không cần database vector riêng
- phù hợp với đồ án hoặc hệ thống nhỏ

## 4. RAG

Phần RAG nằm ở [ai_chat_service/kb_store.py](D:/This%20Semester/Analysis%20and%20Design/assignment_6_ddd_marketplace/ai_chat_service/kb_store.py).

Ở đây, RAG được hiểu theo nghĩa:

- `Retrieve`: tìm các đoạn knowledge liên quan
- `Augment`: đưa kiến thức đó vào logic trả lời
- `Generate`: tạo câu trả lời cuối cùng

Project hiện tại dùng một phiên bản RAG nhẹ, không dùng embedding model lớn.

### 4.1. Retrieve

Quá trình retrieve gồm các bước:

1. đọc tất cả file Markdown trong `kb_docs`
2. chia nội dung thành các chunk nhỏ
3. vector hóa các chunk bằng `TfidfVectorizer`
4. khi có câu hỏi, vector hóa câu hỏi
5. tính độ tương đồng bằng `cosine_similarity`
6. lấy ra `top_k` chunk phù hợp nhất

### 4.2. Chunking

Project không vectorize nguyên file thô mà chia nhỏ theo:

- section Markdown
- paragraph
- giới hạn độ dài chunk

Điều này giúp:

- retrieval chính xác hơn
- tránh lấy cả file quá dài
- tăng khả năng match đúng đoạn liên quan

### 4.3. Vector hóa

Hiện tại KB dùng:

- `TfidfVectorizer`
- `ngram_range=(1, 2)`

Ưu điểm:

- nhẹ
- chạy local
- không cần GPU
- không cần external API

Hạn chế:

- không hiểu ngữ nghĩa sâu như embedding model hiện đại
- nhạy với từ khóa
- chưa mạnh khi câu hỏi paraphrase quá xa nội dung gốc

### 4.4. Lưu trữ

Sau khi fit, KB được lưu tại:

- [ai_chat_service/models/kb_store.joblib](D:/This%20Semester/Analysis%20and%20Design/assignment_6_ddd_marketplace/ai_chat_service/models/kb_store.joblib)

Khi startup:

- nếu file store đã có thì load lại
- nếu chưa có thì fit mới từ thư mục `kb_docs`

## 5. Cách `ai_chat_service` Kết Hợp Model + KB + RAG

Luồng xử lý tổng quát:

1. người dùng gửi câu hỏi vào `POST /chat/ask`
2. service lấy snapshot người dùng từ nhiều microservice
3. behavior model dự đoán `persona`, `price_sensitivity`, `next_best_action`, `purchase_intent`
4. KB search retrieve các đoạn Markdown liên quan
5. `advisor.py` phân loại intent câu hỏi
6. hệ thống kết hợp:
   - behavior profile
   - dữ liệu sản phẩm thật
   - dữ liệu cart / order / marketing
   - kết quả retrieval từ KB
7. chatbot sinh câu trả lời và danh sách `top_products`

Nói ngắn gọn:

- `Model` giúp hiểu người dùng
- `KB` giúp giữ tri thức miền nghiệp vụ
- `RAG` giúp lấy đúng tri thức theo câu hỏi
- `Advisor` là nơi hợp nhất tất cả để tạo response cuối

## 6. Recommendation Trong Project

Recommendation không chỉ dựa vào model mà là cơ chế lai:

- behavior profile từ model
- search history
- recently viewed products
- recently viewed categories
- wishlist
- orders
- cart status
- marketing context

Trong [ai_chat_service/advisor.py](D:/This%20Semester/Analysis%20and%20Design/assignment_6_ddd_marketplace/ai_chat_service/advisor.py), sản phẩm được chấm điểm theo:

- danh mục quan tâm
- từ khóa tìm kiếm gần đây
- nhóm sản phẩm vừa xem
- độ nhạy giá
- purchase intent
- tình trạng tồn kho

Điều này có nghĩa recommendation hiện tại là:

- `behavior-aware`
- `context-aware`
- `rule-enhanced scoring`

chứ chưa phải collaborative filtering hay deep recommender system.

## 7. Điểm Mạnh Của Cách Làm Hiện Tại

- dễ hiểu và dễ trình bày trong đồ án
- chạy hoàn toàn local
- không phụ thuộc API AI bên ngoài
- có personalization cơ bản
- có thể giải thích được tại sao system gợi ý như vậy
- dễ mở rộng thêm dữ liệu KB hoặc feature hành vi

## 8. Hạn Chế

- behavior model đang train trên dữ liệu mô phỏng
- KB retrieval dùng TF-IDF nên chưa hiểu ngữ nghĩa sâu
- chưa dùng vector database
- chưa dùng LLM để sinh câu trả lời mềm mại hơn
- recommendation vẫn thiên về heuristic scoring hơn là mô hình recommend chuyên sâu

## 9. Hướng Mở Rộng Sau Này

Nếu muốn nâng cấp phần AI trong tương lai, có thể đi theo các hướng sau:

- thay TF-IDF bằng embedding model
- dùng vector database như FAISS hoặc pgvector
- thay rule-based response bằng LLM-based generation
- train behavior model trên dữ liệu thật từ `behavior_service`
- bổ sung feedback loop: click từ recommendation, add-to-cart từ AI, purchase after recommendation
- thêm hybrid recommender: content-based + collaborative filtering

## 10. Kết Luận

`ai_chat_service` trong project hiện tại là một kiến trúc AI nhẹ, thực dụng và phù hợp với đồ án:

- có `model` để hiểu hành vi
- có `knowledge base` để giữ tri thức nghiệp vụ
- có `RAG` để truy xuất kiến thức liên quan
- có `advisor` để kết hợp dữ liệu và sinh câu trả lời

Đây là một nền tảng tốt để trình bày ý tưởng AI trong hệ thống marketplace trước khi nâng cấp lên các mô hình lớn hơn trong tương lai.
