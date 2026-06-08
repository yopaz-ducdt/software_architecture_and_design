# Huong Dan Chay Project Tren macOS va Ubuntu

Project nay nen chay bang Docker Compose. Cach nay tu dong dung MySQL, RabbitMQ, Neo4j, API Gateway, frontend va cac microservice FastAPI, tranh phai cai tung service Python tren may.

## 1. Yeu cau chung

- Docker va Docker Compose v2
- Python 3.10+ de chay seed data tu may host
- Git
- May con trong cac cong: `3307`, `4000`, `5672`, `7474`, `7687`, `8000-8013`, `15672`

Thong tin database mac dinh trong project:

- MySQL host port: `3307`
- MySQL user: `root`
- MySQL password: `trungduc`
- Neo4j user/password: `neo4j` / `learnmart_graph_password`
- RabbitMQ user/password: `guest` / `guest`

## 2. Cai dat tren macOS

### 2.1. Cai Docker Desktop

1. Tai va cai Docker Desktop for Mac.
2. Mo Docker Desktop va doi den khi Docker bao dang running.
3. Kiem tra trong Terminal:

```bash
docker --version
docker compose version
```

Neu dung chip Apple Silicon, Docker Desktop van chay duoc project nay binh thuong. Lan build dau tien co the lau hon.

### 2.2. Cai Python va Git neu chua co

Neu da cai Homebrew:

```bash
brew install python git
python3 --version
git --version
```

Neu khong dung Homebrew, co the cai Python tu python.org va Git tu installer chinh thuc.

## 3. Cai dat tren Ubuntu

### 3.1. Cap nhat he thong va cai cong cu co ban

```bash
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv curl
```

### 3.2. Cai Docker

Neu may chua co Docker, cai Docker Engine theo bo lenh co ban:

```bash
sudo apt install -y docker.io docker-compose-v2
sudo systemctl enable docker
sudo systemctl start docker
```

Cho phep user hien tai chay Docker khong can `sudo`:

```bash
sudo usermod -aG docker $USER
```

Sau lenh nay, dang xuat/dang nhap lai hoac restart terminal, roi kiem tra:

```bash
docker --version
docker compose version
docker ps
```

Neu `docker ps` van bao permission denied, chay tam bang `sudo docker ps` hoac dang nhap lai may.

## 4. Lay source code va vao thu muc project

Neu da co source tren may, chi can `cd` vao thu muc project:

```bash
cd marketplace_with_ai_service
```

Neu lay tu Git:

```bash
git clone <repo-url>
cd marketplace_with_ai_service
```

Kiem tra phai thay file `docker-compose.yml`:

```bash
ls docker-compose.yml
```

## 5. Chay toan bo he thong bang Docker Compose

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

## 6. Seed du lieu demo

Sau khi cac container da chay, tao virtual environment tren may host de chay seed script:

### macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install requests
```

### Ubuntu

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

## 7. Truy cap ung dung

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

## 8. Lenh dung, restart va reset

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

## 9. Troubleshooting

### 9.1. Port bi trung

Neu gap loi dang `port is already allocated`, kiem tra process dang chiem port.

macOS:

```bash
lsof -i :4000
lsof -i :8000
lsof -i :3307
```

Ubuntu:

```bash
sudo lsof -i :4000
sudo lsof -i :8000
sudo lsof -i :3307
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

### 9.4. Ubuntu chay Docker bi permission denied

Them user vao group docker:

```bash
sudo usermod -aG docker $USER
```

Dang xuat/dang nhap lai, sau do kiem tra:

```bash
docker ps
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
