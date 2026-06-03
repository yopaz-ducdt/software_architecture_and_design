from sqlalchemy import or_
from modules.catalog.infrastructure.models.product_model import ProductModel, CategoryModel, BrandModel

def apply_filters(query, q=None, category_id=None, product_type_id=None):
    if q:
        query = query.join(CategoryModel, isouter=True).join(BrandModel, isouter=True).filter(or_(ProductModel.name.ilike(f'%{q}%'), ProductModel.description.ilike(f'%{q}%'), CategoryModel.name.ilike(f'%{q}%'), BrandModel.name.ilike(f'%{q}%')))
    if category_id: query = query.filter(ProductModel.category_id == category_id)
    if product_type_id: query = query.filter(ProductModel.product_type_id == product_type_id)
    return query
