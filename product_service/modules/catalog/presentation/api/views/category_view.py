from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from modules.catalog.infrastructure.repositories.product_repository_impl import ProductRepositoryImpl
from modules.catalog.presentation.api.serializers.product_serializer import CategoryCreate, CategoryOut, BrandCreate, BrandOut, ProductTypeCreate, ProductTypeOut
router = APIRouter()
@router.post('/categories', response_model=CategoryOut, status_code=201)
def create_category(body: CategoryCreate, db: Session = Depends(get_db)): return ProductRepositoryImpl(db).create_category(body.model_dump())
@router.get('/categories', response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)): return ProductRepositoryImpl(db).list_categories()
@router.post('/brands', response_model=BrandOut, status_code=201)
def create_brand(body: BrandCreate, db: Session = Depends(get_db)): return ProductRepositoryImpl(db).create_brand(body.model_dump())
@router.get('/brands', response_model=list[BrandOut])
def list_brands(db: Session = Depends(get_db)): return ProductRepositoryImpl(db).list_brands()
@router.post('/product-types', response_model=ProductTypeOut, status_code=201)
def create_product_type(body: ProductTypeCreate, db: Session = Depends(get_db)): return ProductRepositoryImpl(db).create_product_type(body.model_dump())
@router.get('/product-types', response_model=list[ProductTypeOut])
def list_product_types(db: Session = Depends(get_db)): return ProductRepositoryImpl(db).list_product_types()
