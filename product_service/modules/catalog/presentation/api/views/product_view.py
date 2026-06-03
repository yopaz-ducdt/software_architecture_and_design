from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from modules.catalog.infrastructure.repositories.product_repository_impl import ProductRepositoryImpl
from modules.catalog.presentation.api.serializers.product_serializer import ProductCreate, ProductOut, ProductUpdate, RatingCreate, RatingOut, ProductReviewCreate, ProductReviewOut
router = APIRouter()
@router.post('/products', response_model=ProductOut, status_code=201)
def create_product(body: ProductCreate, db: Session = Depends(get_db)): return ProductRepositoryImpl(db).create(body.model_dump())
@router.get('/products', response_model=list[ProductOut])
def list_products(q: str|None = Query(default=None), category_id: int|None=None, product_type_id: int|None=None, skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return ProductRepositoryImpl(db).list(q=q, category_id=category_id, product_type_id=product_type_id, skip=skip, limit=limit)
@router.get('/products/{product_id}', response_model=ProductOut)
def get_product(product_id:int, db: Session = Depends(get_db)):
    item = ProductRepositoryImpl(db).get(product_id)
    if not item: raise HTTPException(404, 'Không tìm thấy sản phẩm')
    return item
@router.put('/products/{product_id}', response_model=ProductOut)
def update_product(product_id:int, body: ProductUpdate, db: Session = Depends(get_db)):
    item = ProductRepositoryImpl(db).update(product_id, {k:v for k,v in body.model_dump().items() if v is not None})
    if not item: raise HTTPException(404, 'Không tìm thấy sản phẩm')
    return item
@router.delete('/products/{product_id}', status_code=204)
def delete_product(product_id:int, db: Session = Depends(get_db)):
    ok = ProductRepositoryImpl(db).delete(product_id)
    if not ok: raise HTTPException(404, 'Không tìm thấy sản phẩm')
@router.patch('/products/{product_id}/stock')
def update_stock(product_id:int, quantity:int, db: Session = Depends(get_db)):
    item = ProductRepositoryImpl(db).update(product_id, {'stock_quantity': quantity})
    if not item: raise HTTPException(404, 'Không tìm thấy sản phẩm')
    return {'message':'Đã cập nhật tồn kho','product_id':product_id,'quantity':quantity}
@router.post('/ratings', response_model=RatingOut, status_code=201)
def create_rating(body: RatingCreate, db: Session = Depends(get_db)): return ProductRepositoryImpl(db).create_rating(body.model_dump())
@router.get('/products/{product_id}/ratings', response_model=list[RatingOut])
def list_ratings(product_id:int, db: Session = Depends(get_db)): return ProductRepositoryImpl(db).list_ratings(product_id)
@router.post('/reviews', response_model=ProductReviewOut, status_code=201)
def create_review(body: ProductReviewCreate, db: Session = Depends(get_db)): return ProductRepositoryImpl(db).create_review(body.model_dump())
@router.get('/products/{product_id}/reviews', response_model=list[ProductReviewOut])
def list_reviews(product_id:int, db: Session = Depends(get_db)): return ProductRepositoryImpl(db).list_reviews(product_id)
