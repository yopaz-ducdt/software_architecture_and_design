"""
migrate.py  –  Create MySQL databases + apply SQLAlchemy migrations
Run from: assignment_5 folder
"""
import sys
import os
import importlib

import pymysql
from sqlalchemy.engine import URL
from sqlalchemy import create_engine

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

# Services that have a separate models.py
HAS_MODELS_FILE = {"auth_service", "book_service", "order_service", "customer_service"}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Step 1: Create databases ─────────────────────────────────
print("--- Step 1: Creating databases ---")
conn = pymysql.connect(
    host=MYSQL_HOST, port=MYSQL_PORT,
    user=MYSQL_USER, password=MYSQL_PASSWORD,
    charset="utf8mb4"
)
cur = conn.cursor()
for db in DATABASES:
    sql = "CREATE DATABASE IF NOT EXISTS {} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci".format(db)
    cur.execute(sql)
    print("  DB ready: {}".format(db))
conn.commit()
cur.close()
conn.close()
print()

# ── Step 2: Create tables per service ────────────────────────
print("--- Step 2: Creating tables ---")
errors = []

for db_name, svc_dir in zip(DATABASES, SERVICE_DIRS):
    svc_path = os.path.join(BASE_DIR, svc_dir)
    sys.path.insert(0, svc_path)
    try:
        url = URL.create(
            "mysql+pymysql",
            username=MYSQL_USER,
            password=MYSQL_PASSWORD,
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            database=db_name
        )
        engine = create_engine(url)

        # Load the correct module
        if svc_dir in HAS_MODELS_FILE:
            mod = importlib.import_module("models")
        else:
            mod = importlib.import_module("main")

        mod.Base.metadata.create_all(bind=engine)
        print("  OK: {} -> {}".format(svc_dir, db_name))

    except Exception as exc:
        msg = str(exc)
        print("  ERR: {}: {}".format(svc_dir, msg))
        errors.append((svc_dir, msg))

    finally:
        sys.path.pop(0)
        # Unload modules to avoid conflicts between services
        for mod_name in list(sys.modules.keys()):
            if mod_name in ("models", "schemas", "database", "main"):
                del sys.modules[mod_name]

print()
if errors:
    print("FAILED services:")
    for svc, err in errors:
        print("  - {}: {}".format(svc, err[:200]))
    sys.exit(1)
else:
    print("All migrations completed successfully!")
