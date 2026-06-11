# Nhung Thu Can Bo Sung Khi Clone Project Sang May Khac

File nay tong hop nhung thu may moi can co de chay project sau khi pull/clone tu GitHub. Ket qua duoc kiem tra dua tren `.gitignore`, `docker-compose.yml`, Dockerfile, cac script seed va cac cho doc bien moi truong trong source code.

## 1. Ket luan nhanh

Neu ban chay theo Docker Compose, project hien tai **khong can API key ben ngoai** de khoi dong demo.

May moi can bo sung/cai dat:

- Docker va Docker Compose v2
- Python 3.10+ hoac 3.11+
- Git
- Python package `requests` tren may host de chay seed script
- Du lieu demo bang cach chay `seed_data.py` va `seed_ai_demo.py`

Khong can copy tu may cu:

- `venv/`, `.venv/`, `ai_pipeline/.venv/`
- `__pycache__/`
- `.idea/`, `.vscode/`
- Docker volumes local cua MySQL/Neo4j
- File log/cache local

## 2. File bi ignore va y nghia

`.gitignore` dang bo qua cac nhom sau:

| Nhom | Vi du | May moi can lam gi |
| --- | --- | --- |
| Virtual environment | `venv/`, `.venv/`, `ai_pipeline/.venv/` | Tao lai neu can chay script Python tu host |
| Cache Python | `__pycache__/`, `*.pyc` | Khong can bo sung |
| Secret/env local | `.env`, `.env.*` | Hien project chua bat buoc `.env`; chi can tao neu muon override config |
| IDE | `.idea/`, `.vscode/` | Khong can bo sung |
| Log/runtime | `*.log`, `logs/` | Khong can bo sung |
| Docker override | `docker-compose.override.yml` | Chi tao neu may moi can override port/password |
| Notebook cache | `.ipynb_checkpoints/` | Khong can bo sung |

## 3. Credential/config dang co san trong project

Cac credential demo sau dang nam trong source/compose, nen neu da push code moi thi may khac clone ve se co:

| Thanh phan | Gia tri |
| --- | --- |
| MySQL user | `root` |
| MySQL password | `trungduc` |
| MySQL host port | `3307` |
| RabbitMQ user/password | `guest` / `guest` |
| RabbitMQ UI | `http://localhost:15672` |
| Neo4j user/password | `neo4j` / `learnmart_graph_password` |
| Neo4j UI | `http://localhost:7474` |
| JWT secret demo | `learnmart-secret-key-2024-very-secure` |

Luu y: day la credential demo/development. Neu dua project len public repo hoac dung production, nen doi sang bien moi truong va khong commit secret that.

## 4. Bien moi truong co the can override

Project co doc cac bien moi truong sau. Khi chay bang `docker-compose.yml` hien tai, phan lon da duoc set san.

| Bien | Dung o dau | Mac dinh/hien tai |
| --- | --- | --- |
| `DATABASE_URL` | Cac service dung MySQL | `mysql+pymysql://root:trungduc@mysql:3306/<db_name>` |
| `RABBITMQ_URL` | `api_gateway`, `order_service`, `inventory_service`, `notification_service` | `amqp://guest:guest@rabbitmq:5672/` |
| `NEO4J_URI` | `behavior_service`, `ai_chat_service` | `bolt://neo4j:7687` trong Docker |
| `NEO4J_USER` | `behavior_service`, `ai_chat_service` | `neo4j` |
| `NEO4J_PASSWORD` | `behavior_service`, `ai_chat_service` | `learnmart_graph_password` |
| `NEO4J_ENABLED` | `behavior_service/graph_sync.py` | `true` |
| `AI_HTTP_TIMEOUT` | `ai_chat_service` | `5.0` |
| `PRODUCT_SERVICE_URL` | `ai_chat_service` | Set trong Docker Compose |
| `ORDER_SERVICE_URL` | `ai_chat_service` | Set trong Docker Compose |
| `CUSTOMER_SERVICE_URL` | `ai_chat_service` | Set trong Docker Compose |
| `MARKETING_SERVICE_URL` | `ai_chat_service` | Set trong Docker Compose |
| `ANALYTICS_SERVICE_URL` | `ai_chat_service` | Set trong Docker Compose |
| `BEHAVIOR_SERVICE_URL` | `ai_chat_service` | Set trong Docker Compose |

Neu may moi chi chay Docker Compose, khong can tao `.env`.

## 5. Du lieu/model AI

Cac file AI quan trong dang duoc Git track, nen neu push len GitHub thanh cong thi may moi clone ve se co:

- `ai_chat_service/data/data_user500.csv`
- `ai_chat_service/data/mock_behavior_training.csv`
- `ai_chat_service/models/model_best.pt`
- `ai_chat_service/models/model_best_meta.json`
- `ai_chat_service/models/rnn_sequence_model.pt`
- `ai_chat_service/models/lstm_sequence_model.pt`
- `ai_chat_service/models/bilstm_sequence_model.pt`
- `ai_chat_service/models/behavior_bundle.joblib`
- `ai_chat_service/models/kb_store.joblib`
- `ai_chat_service/kb_docs/*.md`

Cac model nay khong lon, hien khoang vai tram KB. Neu sau nay ban them model lon hon va GitHub khong cho push, co 2 cach:

1. Dung Git LFS cho file `.pt`, `.joblib`, `.csv` lon.
2. Khong push model, nhung may moi phai chay lai:

```bash
python ai_pipeline/generate_user_behavior_data.py
python ai_pipeline/train_sequence_models.py
```

Sau khi train, can dam bao output model dung duong dan ma `ai_chat_service` doc:

- `ai_chat_service/models/model_best.pt`
- `ai_chat_service/models/model_best_meta.json`

## 6. Docker volumes khong duoc push

Du lieu MySQL va Neo4j khi chay Docker nam trong Docker volumes local:

- `mysql_data`
- `neo4j_data`

GitHub khong push cac volume nay. Tren may moi, khi chay:

```bash
docker compose up --build -d
```

MySQL/Neo4j se tao volume moi. Sau do can seed lai du lieu:

```bash
python seed_data.py
python seed_ai_demo.py
```

Neu muon reset sach tren may moi:

```bash
docker compose down -v
docker compose up --build -d
python seed_data.py
python seed_ai_demo.py
```

## 7. Goi Python can cai tren host

Neu chi chay Docker Compose, dependencies cua service duoc cai trong container tu cac file `requirements.txt`.

May host chi can package de chay seed:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install requests
```

Neu muon chay pipeline AI tren host, cai them:

```bash
python -m pip install numpy pandas scikit-learn torch matplotlib seaborn
```

Neu muon chay migration script local, cai them:

```bash
python -m pip install sqlalchemy pymysql cryptography
```

## 8. Checklist cho may moi

Chay nhanh theo thu tu:

```bash
git clone <repo-url>
cd marketplace_with_ai_service

docker compose up --build -d
docker compose ps

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install requests

python seed_data.py
python seed_ai_demo.py
```

Mo cac URL:

- Frontend: `http://localhost:4000`
- API Gateway: `http://localhost:8000`
- AI Chat Service: `http://localhost:8012/docs`
- Behavior Service: `http://localhost:8013/docs`
- RabbitMQ UI: `http://localhost:15672`
- Neo4j UI: `http://localhost:7474`

## 9. Nhung thu nen can nhac truoc khi push GitHub

- Commit file huong dan: `HUONG_DAN_CHAY_MACOS_UBUNTU.md` va file nay.
- Khong commit `venv/`, `.venv/`, `.idea/`, `__pycache__/`, log.
- Neu repo public, khong nen de password/JWT secret that trong source. Credential hien tai la demo.
- Neu GitHub tu choi push file lon, kiem tra `ai_pipeline/data`, `ai_pipeline/models`, `ai_pipeline/reports`; co the dung Git LFS hoac de script tao lai.
- Neu muon nguoi khac cau hinh de hon, co the tao them `.env.example` va sua `docker-compose.yml` doc bien tu `.env`.
