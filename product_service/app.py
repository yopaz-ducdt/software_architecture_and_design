from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import wait_for_db, engine
from modules.catalog.infrastructure.models.base import Base
from modules.catalog.infrastructure.models import product_model  # noqa: F401
from modules.catalog.presentation.api.views.product_view import router as product_router
from modules.catalog.presentation.api.views.category_view import router as category_router
from modules.catalog.seeds.products_seed import seed_default_catalog
app = FastAPI(title='LearnMart Product Service', version='3.0.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
@app.on_event('startup')
def startup():
    wait_for_db(); Base.metadata.create_all(bind=engine); seed_default_catalog()
@app.get('/health')
def health(): return {'status':'ok','service':'product_service','timestamp':datetime.utcnow().isoformat()}
@app.get('/metrics')
def metrics(): return {'service':'product_service','bounded_context':'catalog'}
app.include_router(category_router)
app.include_router(product_router)
