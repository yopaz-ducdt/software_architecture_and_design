"""
setup_and_migrate.py
Tạo 11 MySQL databases và migrate (tạo tables) cho tất cả microservices
"""
import sys, os
import pymysql
from sqlalchemy.engine import URL
from sqlalchemy import create_engine, text

# ── Config ────────────────────────────────────────────────
MYSQL_USER     = "root"
MYSQL_PASSWORD = "Duyanh090@"
MYSQL_HOST     = "localhost"
MYSQL_PORT     = 3306

DATABASES = [
    "auth_db", "book_db", "order_db", "customer_db",
    "staff_db", "marketing_db", "inventory_db",
    "content_db", "interaction_db", "analytics_db", "notification_db"
]

SERVICE_DIRS = [
    "auth_service", "book_service", "order_service", "customer_service",
    "staff_service", "marketing_service", "inventory_service",
    "content_service", "interaction_service", "analytics_service", "notification_service"
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Step 1: Create databases ──────────────────────────────
print("=" * 60)
print("STEP 1: Creating MySQL databases...")
print("=" * 60)

conn = pymysql.connect(
    host=MYSQL_HOST, port=MYSQL_PORT,
    user=MYSQL_USER, password=MYSQL_PASSWORD
)
cursor = conn.cursor()

for db in DATABASES:
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    print(f"  ✓ Database '{db}' ready")

conn.commit()
cursor.close()
conn.close()
print()

# ── Step 2: Migrate each service ─────────────────────
print("=" * 60)
print("STEP 2: Creating tables (migrate) for each service...")
print("=" * 60)

errors = []
for db_name, svc_dir in zip(DATABASES, SERVICE_DIRS):
    svc_path = os.path.join(BASE_DIR, svc_dir)
    sys.path.insert(0, svc_path)

    try:
        connection_url = URL.create(
            "mysql+pymysql",
            username=MYSQL_USER, password=MYSQL_PASSWORD,
            host=MYSQL_HOST, port=MYSQL_PORT, database=db_name
        )
        engine = create_engine(connection_url)

        # Import Base (different location per service)
        if svc_dir in ("auth_service", "book_service", "order_service", "customer_service"):
            import importlib
            models_mod = importlib.import_module("models")
            Base = models_mod.Base
        else:
            # Inline services: import main to get Base
            import importlib
            main_mod = importlib.import_module("main")
            Base = main_mod.Base

        Base.metadata.create_all(bind=engine)
        print(f"  ✓ [{svc_dir}] → {db_name} — tables created OK")

    except Exception as e:
        print(f"  ✗ [{svc_dir}] ERROR: {e}")
        errors.append((svc_dir, str(e)))
    finally:
        sys.path.pop(0)
        # Unload imported modules to avoid conflicts between services
        for mod_name in list(sys.modules.keys()):
            if mod_name in ("models", "schemas", "database", "main"):
                del sys.modules[mod_name]

print()
if errors:
    print(f"⚠  {len(errors)} service(s) had errors:")
    for svc, err in errors:
        print(f"   - {svc}: {err}")
else:
    print("✅ All migrations completed successfully!")

print()
print("=" * 60)
print("Databases available in MySQL:")
for db in DATABASES:
    print(f"  mysql> USE {db};")
print("=" * 60)
