from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx
from neo4j import GraphDatabase


class GraphKBStore:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "learnmart_graph_password")
        self.product_url = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8002")
        self.timeout = float(os.getenv("AI_HTTP_TIMEOUT", "5.0"))
        self.driver = None

    def _connect(self):
        if self.driver is None:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        return self.driver

    def ensure_ready(self) -> None:
        driver = self._connect()
        with driver.session() as session:
            session.run("CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE")
            session.run("CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE")
            session.run("CREATE CONSTRAINT category_name IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE")
            session.run("CREATE CONSTRAINT query_text IF NOT EXISTS FOR (q:Query) REQUIRE q.text IS UNIQUE")
            session.run("CREATE CONSTRAINT brand_name IF NOT EXISTS FOR (b:Brand) REQUIRE b.name IS UNIQUE")
            session.run("CREATE CONSTRAINT product_type_name IF NOT EXISTS FOR (t:ProductType) REQUIRE t.name IS UNIQUE")
            session.run("CREATE CONSTRAINT coupon_code IF NOT EXISTS FOR (c:Coupon) REQUIRE c.code IS UNIQUE")
            session.run("CREATE CONSTRAINT promotion_name IF NOT EXISTS FOR (p:Promotion) REQUIRE p.name IS UNIQUE")
            session.run("CREATE CONSTRAINT flash_sale_id IF NOT EXISTS FOR (f:FlashSale) REQUIRE f.id IS UNIQUE")
            session.run("CREATE CONSTRAINT tier_name IF NOT EXISTS FOR (t:MembershipTier) REQUIRE t.name IS UNIQUE")

    def _get_json(self, url: str, default: Any) -> Any:
        try:
            with httpx.Client(timeout=httpx.Timeout(self.timeout, connect=self.timeout)) as client:
                response = client.get(url)
                if response.is_success:
                    return response.json()
        except Exception:
            pass
        return default

    def sync_catalog(self) -> None:
        driver = self._connect()
        categories = self._get_json(f"{self.product_url}/categories", [])
        brands = self._get_json(f"{self.product_url}/brands", [])
        product_types = self._get_json(f"{self.product_url}/product-types", [])
        products = self._get_json(f"{self.product_url}/products?limit=200", [])
        category_lookup = {item.get("id"): item.get("name") for item in categories if item.get("id") is not None}
        brand_lookup = {item.get("id"): item.get("name") for item in brands if item.get("id") is not None}
        type_lookup = {item.get("id"): item.get("name") for item in product_types if item.get("id") is not None}

        with driver.session() as session:
            for category in categories:
                session.run(
                    "MERGE (c:Category {name: $name}) SET c.category_id = $category_id",
                    name=category.get("name"),
                    category_id=category.get("id"),
                )
            for brand in brands:
                session.run(
                    "MERGE (b:Brand {name: $name}) SET b.brand_id = $brand_id",
                    name=brand.get("name"),
                    brand_id=brand.get("id"),
                )
            for product_type in product_types:
                session.run(
                    "MERGE (t:ProductType {name: $name}) SET t.product_type_id = $product_type_id",
                    name=product_type.get("name"),
                    product_type_id=product_type.get("id"),
                )

            for product in products:
                product_id = product.get("id")
                if product_id is None:
                    continue
                category_name = product.get("category_name") or category_lookup.get(product.get("category_id"))
                brand_name = product.get("brand_name") or brand_lookup.get(product.get("brand_id"))
                product_type_name = product.get("product_type_name") or type_lookup.get(product.get("product_type_id"))
                session.run(
                    """
                    MERGE (p:Product {id: $product_id})
                    SET p.title = $title,
                        p.price = $price,
                        p.stock_quantity = $stock_quantity,
                        p.description = $description,
                        p.category_name = $category_name,
                        p.brand_name = $brand_name,
                        p.product_type_name = $product_type_name
                    WITH p
                    FOREACH (_ IN CASE WHEN $category_name IS NULL THEN [] ELSE [1] END |
                        MERGE (c:Category {name: $category_name})
                        MERGE (p)-[:BELONGS_TO]->(c)
                    )
                    FOREACH (_ IN CASE WHEN $brand_name IS NULL THEN [] ELSE [1] END |
                        MERGE (b:Brand {name: $brand_name})
                        MERGE (p)-[:HAS_BRAND]->(b)
                    )
                    FOREACH (_ IN CASE WHEN $product_type_name IS NULL THEN [] ELSE [1] END |
                        MERGE (t:ProductType {name: $product_type_name})
                        MERGE (p)-[:HAS_TYPE]->(t)
                    )
                    """,
                    product_id=product_id,
                    title=product.get("title") or product.get("name"),
                    price=float(product.get("price", 0) or 0),
                    stock_quantity=int(product.get("stock_quantity", 0) or 0),
                    description=product.get("description"),
                    category_name=category_name,
                    brand_name=brand_name,
                    product_type_name=product_type_name,
                )

    def sync_marketing(self) -> None:
        driver = self._connect()
        marketing_url = os.getenv("MARKETING_SERVICE_URL", "http://localhost:8006")
        coupons = self._get_json(f"{marketing_url}/coupons", [])
        promotions = self._get_json(f"{marketing_url}/promotions", [])
        flash_sales = self._get_json(f"{marketing_url}/flash-sales", [])
        tiers = self._get_json(f"{marketing_url}/tiers", [])

        with driver.session() as session:
            for coupon in coupons:
                session.run(
                    """
                    MERGE (c:Coupon {code: $code})
                    SET c.coupon_id = $coupon_id,
                        c.discount_percent = $discount_percent,
                        c.discount_amount = $discount_amount,
                        c.min_order_value = $min_order_value,
                        c.active = $active
                    """,
                    code=coupon.get("code"),
                    coupon_id=coupon.get("id"),
                    discount_percent=coupon.get("discount_percent"),
                    discount_amount=coupon.get("discount_amount"),
                    min_order_value=float(coupon.get("min_order_value", 0) or 0),
                    active=bool(coupon.get("active", True)),
                )

            for promotion in promotions:
                session.run(
                    """
                    MERGE (p:Promotion {name: $name})
                    SET p.promotion_id = $promotion_id,
                        p.description = $description,
                        p.discount_percent = $discount_percent,
                        p.is_active = $is_active
                    """,
                    name=promotion.get("name"),
                    promotion_id=promotion.get("id"),
                    description=promotion.get("description"),
                    discount_percent=promotion.get("discount_percent"),
                    is_active=bool(promotion.get("is_active", True)),
                )

            for flash_sale in flash_sales:
                product_id = flash_sale.get("product_id")
                session.run(
                    """
                    MERGE (f:FlashSale {id: $flash_sale_id})
                    SET f.name = $name,
                        f.discount_percent = $discount_percent,
                        f.start_at = $start_at,
                        f.end_at = $end_at,
                        f.is_active = $is_active
                    WITH f
                    FOREACH (_ IN CASE WHEN $product_id IS NULL THEN [] ELSE [1] END |
                        MERGE (p:Product {id: $product_id})
                        MERGE (f)-[:APPLIES_TO]->(p)
                    )
                    """,
                    flash_sale_id=flash_sale.get("id"),
                    name=flash_sale.get("name"),
                    discount_percent=flash_sale.get("discount_percent"),
                    start_at=str(flash_sale.get("start_at") or ""),
                    end_at=str(flash_sale.get("end_at") or ""),
                    is_active=bool(flash_sale.get("is_active", True)),
                    product_id=product_id,
                )

            for tier in tiers:
                session.run(
                    """
                    MERGE (t:MembershipTier {name: $name})
                    SET t.tier_id = $tier_id,
                        t.min_points = $min_points,
                        t.discount_percent = $discount_percent,
                        t.free_shipping = $free_shipping
                    """,
                    name=tier.get("name"),
                    tier_id=tier.get("id"),
                    min_points=int(tier.get("min_points", 0) or 0),
                    discount_percent=float(tier.get("discount_percent", 0) or 0),
                    free_shipping=bool(tier.get("free_shipping", False)),
                )

    def get_context(self, customer_id: int, question: str, top_k: int = 5) -> dict[str, Any]:
        driver = self._connect()
        query_text = " ".join((question or "").lower().split())
        with driver.session() as session:
            preferred_categories = [
                record["name"]
                for record in session.run(
                    """
                    MATCH (:User {id: $customer_id})-[r:INTERESTED_IN]->(c:Category)
                    RETURN c.name AS name
                    ORDER BY r.weight DESC, c.name ASC
                    LIMIT 5
                    """,
                    customer_id=customer_id,
                )
            ]
            recent_products = [
                record["product_id"]
                for record in session.run(
                    """
                    MATCH (:User {id: $customer_id})-[r:INTERACTED_WITH]->(p:Product)
                    RETURN p.id AS product_id
                    ORDER BY r.weight DESC, p.id ASC
                    LIMIT $top_k
                    """,
                    customer_id=customer_id,
                    top_k=top_k,
                )
            ]
            query_products = [
                record["product_id"]
                for record in session.run(
                    """
                    MATCH (q:Query)-[:MATCHES]->(p:Product)
                    WHERE q.text CONTAINS $query_text OR $query_text CONTAINS q.text
                    RETURN DISTINCT p.id AS product_id
                    LIMIT $top_k
                    """,
                    query_text=query_text,
                    top_k=top_k,
                )
            ] if query_text else []
            graph_brands = [
                record["name"]
                for record in session.run(
                    """
                    MATCH (:User {id: $customer_id})-[:INTERACTED_WITH]->(:Product)-[:HAS_BRAND]->(b:Brand)
                    RETURN b.name AS name, count(*) AS c
                    ORDER BY c DESC, b.name ASC
                    LIMIT 5
                    """,
                    customer_id=customer_id,
                )
            ]
            graph_types = [
                record["name"]
                for record in session.run(
                    """
                    MATCH (:User {id: $customer_id})-[:INTERACTED_WITH]->(:Product)-[:HAS_TYPE]->(t:ProductType)
                    RETURN t.name AS name, count(*) AS c
                    ORDER BY c DESC, t.name ASC
                    LIMIT 5
                    """,
                    customer_id=customer_id,
                )
            ]
            promo_names = [
                record["name"]
                for record in session.run(
                    """
                    MATCH (f:FlashSale)-[:APPLIES_TO]->(p:Product)<-[:INTERACTED_WITH]-(:User {id: $customer_id})
                    RETURN DISTINCT f.name AS name
                    LIMIT 5
                    """,
                    customer_id=customer_id,
                )
            ]

        return {
            "preferred_categories": preferred_categories,
            "recent_product_ids": recent_products,
            "query_product_ids": query_products,
            "preferred_brands": graph_brands,
            "preferred_product_types": graph_types,
            "active_promotions": promo_names,
        }
