# Huong Dan Chay Project Tren macOS

Project nay nen chay bang Docker Compose. Cach nay tu dong dung MySQL, RabbitMQ, Neo4j, API Gateway, frontend va cac microservice FastAPI, tranh phai cai tung service Python tren may.

Tren macOS, khuyen nghi dung `colima` thay cho Docker Desktop de giam RAM va CPU. Tat ca lenh docker compose trong tai lieu van giu nguyen.

## 1. Yeu cau chung

- Docker Engine (Colima tren macOS)
- Docker Compose v2
- Python 3.10+ de chay seed data tu may host
- Git
- May con trong cac cong: `3307`, `4000`, `5672`, `7474`, `7687`, `8000-8013`, `15672`

Thong tin database mac dinh trong project:

- MySQL host port: `3307`
- MySQL user: `root`
- MySQL password: `trungduc`
- Neo4j user/password: `neo4j` / `learnmart_graph_password`
- RabbitMQ user/password: `guest` / `guest`

docker compose version
docker ps
docker context use colima
git --version

## 2. Cai dat tren macOS (ưu tiên cho MacBook Air M1/M2/M3/M4)

Trên macOS (đặc biệt MacBook Air có chip Apple Silicon như M4), khuyến nghị dùng `colima` thay cho Docker Desktop để tiết kiệm tài nguyên và tránh một số vấn đề tương thích.

### 2.1. Cài Colima & Docker CLI (khuyến nghị cho M-series)

1. Cài Homebrew nếu chưa có:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

2. Cài Docker CLI và Colima:

```bash
brew install docker colima
```

3. Khởi động Colima với cấu hình khuyến nghị cho MacBook Air M4 (tùy máy, chỉnh `--cpu`/`--memory` nếu cần):

```bash
# Thông thường: 4 CPU, 6GB RAM, 50GB disk
colima start --cpu 4 --memory 6 --disk 50

# Nếu gặp lỗi do image chỉ hỗ trợ amd64, khởi động lại với kiến trúc x86_64 (chậm hơn):
colima stop
colima start --arch x86_64 --cpu 4 --memory 6 --disk 50
```

4. Chuyển Docker context sang Colima và kiểm tra:

```bash
docker context ls
docker context use colima
docker --version
docker compose version
docker ps
```

5. Ghi chú về Apple Silicon:

- Nên ưu tiên các image đa kiến trúc hoặc arm64-native vì nhanh và tiết kiệm tài nguyên.
- Chỉ dùng `--arch x86_64` khi thực sự cần (một số image cũ chỉ có amd64). Colima sẽ chạy slow hơn khi bắt chước kiến trúc khác.

6. Tối ưu tài nguyên (nếu máy chậm):

```bash
# Tăng/giảm CPU & RAM khi cần
colima stop
colima start --cpu 2 --memory 4096 --disk 50
```

### 2.2. (Tùy chọn) Cài Rosetta 2

Một vài công cụ hoặc binary Intel cần Rosetta trên Apple Silicon. Cài khi cần:

```bash
softwareupdate --install-rosetta --agree-to-license
```

### 2.3. Cài Python & Git (nếu cần để chạy seed scripts)

Nếu đã cài Homebrew:

```bash
brew install python git
python3 --version
git --version
```

Nếu không dùng Homebrew, có thể cài Python từ python.org và Git từ installer chính thức.

## 3. Lay source code va vao thu muc project

`cd` vao thu muc project:

## 4. Chay toan bo he thong bang Docker Compose

Tai thu muc goc cua project, chay:

```bash
docker compose up --build -d
```

Lenh nay se build va start:

- MySQL 8.0
- RabbitMQ
- Neo4j
- API Gateway
- Frontend
- `auth_service`, `product_service`, `order_service`, `customer_service`
- `staff_service`, `marketing_service`, `inventory_service`, `content_service`
- `interaction_service`, `analytics_service`, `notification_service`
- `ai_chat_service`, `behavior_service`

Cho khoang 30-60 giay de MySQL va Neo4j khoi dong xong healthcheck.

Kiem tra container:

```bash
docker compose ps
```

Xem log neu can:

```bash
docker compose logs -f
```

Xem log rieng mot service:

```bash
docker compose logs -f api_gateway
docker compose logs -f product_service
docker compose logs -f frontend
```

## 5. Seed du lieu demo

Sau khi cac container da chay, tao virtual environment tren may host de chay seed script:

### macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install requests
```

Chay seed:

```bash
python seed_data.py
python seed_ai_demo.py
```

Neu chi muon seed catalog co ban:

```bash
python seed_catalog.py
```

## 6. Truy cap ung dung

- Frontend: `http://localhost:4000`
- API Gateway: `http://localhost:8000`
- RabbitMQ UI: `http://localhost:15672`
- Neo4j Browser: `http://localhost:7474`

Swagger docs cua tung service:

- API Gateway: `http://localhost:8000/docs`
- Auth: `http://localhost:8001/docs`
- Product/Catalog: `http://localhost:8002/docs`
- Order: `http://localhost:8003/docs`
- Customer: `http://localhost:8004/docs`
- Staff: `http://localhost:8005/docs`
- Marketing: `http://localhost:8006/docs`
- Inventory: `http://localhost:8007/docs`
- Content: `http://localhost:8008/docs`
- Interaction: `http://localhost:8009/docs`
- Analytics: `http://localhost:8010/docs`
- Notification: `http://localhost:8011/docs`
- AI Chat: `http://localhost:8012/docs`
- Behavior: `http://localhost:8013/docs`

Tai khoan demo sau khi seed:

- Customer email: `demo@learnmart.vn`
- Customer password: `demo123`
- Staff username: `admin`
- Staff password: `admin123`

## 7. Lenh dung, restart va reset

Dung container nhung giu database volume:

```bash
docker compose down
```

Start lai:

```bash
docker compose up -d
```

Build lai sau khi sua code hoac Dockerfile:

```bash
docker compose up --build -d
```

Reset sach database va container:

```bash
docker compose down -v
docker compose up --build -d
python seed_data.py
python seed_ai_demo.py
```

Luu y: `docker compose down -v` se xoa volume MySQL va Neo4j, mat toan bo du lieu da seed.

## 8. Troubleshooting

### 9.1. Port bi trung

Neu gap loi dang `port is already allocated`, kiem tra process dang chiem port.

macOS:

```bash
lsof -i :4000
lsof -i :8000
lsof -i :3307
```

Dung process dang chiem port, hoac sua mapping port trong `docker-compose.yml`.

### 9.2. MySQL khong ready

Kiem tra log:

```bash
docker compose logs -f mysql
```

Neu MySQL loi do volume cu dang dung password khac, reset volume:

```bash
docker compose down -v
docker compose up --build -d
```

Sau do chay lai seed.

### 9.3. Seed script bao connection refused

Thu cac buoc sau:

```bash
docker compose ps
curl http://localhost:8000
curl http://localhost:8002/docs
```

Neu service chua len, xem log:

```bash
docker compose logs -f api_gateway
docker compose logs -f product_service
```

Sau khi service ready, chay lai:

```bash
python seed_data.py
python seed_ai_demo.py
```

### 9.5. Frontend khong load duoc API

Kiem tra API Gateway:

```bash
curl http://localhost:8000
docker compose logs -f api_gateway
```

Kiem tra frontend:

```bash
docker compose logs -f frontend
```

Neu moi build lan dau, doi them vai chuc giay roi refresh `http://localhost:4000`.

### Docker khong ket noi duoc tren macOS

```bash
colima status
colima start
docker context ls
docker context use colima
docker ps
```

## 10. Cach chay khuyen nghi khi demo

Chay theo thu tu nay de it loi nhat:

```bash
docker compose down
docker compose up --build -d
docker compose ps
python seed_data.py
python seed_ai_demo.py
```

Sau do mo:

- `http://localhost:4000` de demo frontend
- `http://localhost:8000/docs` de demo API Gateway
- `http://localhost:8012/docs` de demo AI Chat Service
- `http://localhost:8013/docs` de demo Behavior Service
