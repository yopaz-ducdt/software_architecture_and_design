from database import SessionLocal
from modules.catalog.infrastructure.models.product_model import (
    BrandModel,
    CategoryModel,
    ProductModel,
    ProductTypeModel,
)
from modules.catalog.seeds.default_catalog import (
    DEFAULT_BRANDS,
    DEFAULT_CATEGORIES,
    DEFAULT_PRODUCT_TYPES,
    DEFAULT_PRODUCTS,
)


def _upsert_entities(db, model, items):
    existing = {item.slug: item for item in db.query(model).all()}
    for payload in items:
        current = existing.get(payload["slug"])
        if current:
            for key, value in payload.items():
                setattr(current, key, value)
        else:
            db.add(model(**payload))
    db.commit()


def seed_default_catalog():
    db = SessionLocal()
    try:
        _upsert_entities(db, CategoryModel, DEFAULT_CATEGORIES)
        _upsert_entities(db, ProductTypeModel, DEFAULT_PRODUCT_TYPES)
        _upsert_entities(db, BrandModel, DEFAULT_BRANDS)

        categories = {c.slug: c.id for c in db.query(CategoryModel).all()}
        types = {t.slug: t.id for t in db.query(ProductTypeModel).all()}
        brands = {b.slug: b.id for b in db.query(BrandModel).all()}
        existing_products = {p.sku: p for p in db.query(ProductModel).all()}

        for payload in DEFAULT_PRODUCTS:
            data = dict(payload)
            data["category_id"] = categories[data.pop("category_slug")]
            data["product_type_id"] = types[data.pop("product_type_slug")]
            data["brand_id"] = brands[data.pop("brand_slug")]

            current = existing_products.get(data["sku"])
            if current:
                for key, value in data.items():
                    setattr(current, key, value)
            else:
                db.add(ProductModel(**data))

        db.commit()
    finally:
        db.close()
