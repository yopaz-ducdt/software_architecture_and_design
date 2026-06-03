from sqlalchemy.orm import Session
from modules.catalog.infrastructure.models.product_model import ProductModel, CategoryModel, BrandModel, ProductTypeModel, RatingModel, ProductReviewModel
from modules.catalog.infrastructure.querysets.product_queryset import apply_filters

def _product_to_dict(product: ProductModel) -> dict:
    rating_count = len(product.ratings)
    rating_avg = round(sum(r.score for r in product.ratings) / rating_count, 2) if rating_count else 0.0
    attrs = product.attributes or {}
    return {
        'id': product.id, 'name': product.name, 'title': product.name, 'sku': product.sku,
        'description': product.description, 'price': product.price, 'stock_quantity': product.stock_quantity,
        'image_url': product.image_url, 'cover_image_url': product.image_url, 'attributes': attrs,
        'category_id': product.category_id, 'category_name': product.category.name if product.category else None,
        'brand_id': product.brand_id, 'brand_name': product.brand.name if product.brand else None,
        'product_type_id': product.product_type_id, 'product_type_name': product.product_type.name if product.product_type else None,
        'language': attrs.get('language'), 'author_name': attrs.get('author'),
        'rating_avg': rating_avg, 'rating_count': rating_count, 'is_active': product.is_active,
    }
class ProductRepositoryImpl:
    def __init__(self, db: Session): self.db = db
    def create(self, data: dict) -> dict:
        o = ProductModel(**data); self.db.add(o); self.db.commit(); self.db.refresh(o); return _product_to_dict(o)
    def get(self, product_id: int):
        o = self.db.query(ProductModel).filter(ProductModel.id == product_id).first(); return _product_to_dict(o) if o else None
    def list(self, **filters):
        q = apply_filters(self.db.query(ProductModel), filters.get('q'), filters.get('category_id'), filters.get('product_type_id'))
        items = q.order_by(ProductModel.id.desc()).offset(filters.get('skip',0)).limit(filters.get('limit',20)).all(); return [_product_to_dict(i) for i in items]
    def update(self, product_id: int, data: dict):
        o = self.db.query(ProductModel).filter(ProductModel.id == product_id).first()
        if not o: return None
        for k,v in data.items(): setattr(o,k,v)
        self.db.commit(); self.db.refresh(o); return _product_to_dict(o)
    def delete(self, product_id: int) -> bool:
        o = self.db.query(ProductModel).filter(ProductModel.id == product_id).first()
        if not o: return False
        self.db.delete(o); self.db.commit(); return True
    def create_category(self, data): o=CategoryModel(**data); self.db.add(o); self.db.commit(); self.db.refresh(o); return o
    def list_categories(self): return self.db.query(CategoryModel).order_by(CategoryModel.name.asc()).all()
    def create_brand(self, data): o=BrandModel(**data); self.db.add(o); self.db.commit(); self.db.refresh(o); return o
    def list_brands(self): return self.db.query(BrandModel).order_by(BrandModel.name.asc()).all()
    def create_product_type(self, data): o=ProductTypeModel(**data); self.db.add(o); self.db.commit(); self.db.refresh(o); return o
    def list_product_types(self): return self.db.query(ProductTypeModel).order_by(ProductTypeModel.name.asc()).all()
    def create_rating(self, data): o=RatingModel(**data); self.db.add(o); self.db.commit(); self.db.refresh(o); return o
    def list_ratings(self, product_id:int): return self.db.query(RatingModel).filter(RatingModel.product_id==product_id).order_by(RatingModel.created_at.desc()).all()
    def create_review(self, data): o=ProductReviewModel(**data); self.db.add(o); self.db.commit(); self.db.refresh(o); return o
    def list_reviews(self, product_id:int): return self.db.query(ProductReviewModel).filter(ProductReviewModel.product_id==product_id).order_by(ProductReviewModel.created_at.desc()).all()
