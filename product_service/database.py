from __future__ import annotations
import os, time
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+pymysql://root:Duyanh090%40@mysql:3306/product_db')
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def wait_for_db(retries: int = 30, delay: int = 2) -> None:
    last = None
    for _ in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            return
        except OperationalError as exc:
            last = exc
            time.sleep(delay)
    if last: raise last

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()
