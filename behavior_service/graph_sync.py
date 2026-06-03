from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from neo4j import GraphDatabase


class BehaviorGraphSync:
    def __init__(self) -> None:
        self.enabled = os.getenv("NEO4J_ENABLED", "true").lower() == "true"
        self.uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "learnmart_graph_password")
        self.driver = None

    def _connect(self):
        if not self.enabled:
            return None
        if self.driver is None:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        return self.driver

    def ensure_ready(self) -> None:
        driver = self._connect()
        if driver is None:
            return
        with driver.session() as session:
            session.run("CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE")
            session.run("CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE")
            session.run("CREATE CONSTRAINT category_name IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE")
            session.run("CREATE CONSTRAINT query_text IF NOT EXISTS FOR (q:Query) REQUIRE q.text IS UNIQUE")
            session.run("CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:BehaviorEvent) REQUIRE e.id IS UNIQUE")

    def _event_weight(self, event_type: str, quantity: int) -> float:
        base = {
            "product_viewed": 1.0,
            "recent_view": 1.0,
            "product_clicked_from_listing": 1.2,
            "wishlist_added": 3.0,
            "wishlist_toggled": 2.0,
            "cart_added": 5.0,
            "checkout_started": 6.0,
            "order_completed": 8.0,
            "search_performed": 1.5,
            "search": 1.5,
        }.get(event_type, 1.0)
        return base * max(1, quantity)

    def sync_event(self, event: dict[str, Any]) -> None:
        driver = self._connect()
        if driver is None:
            return

        customer_id = event.get("customer_id")
        event_type = event.get("event_type") or "unknown"
        product_id = event.get("product_id")
        category_name = event.get("category_name")
        query = " ".join(str(event.get("query") or "").lower().split()) or None
        quantity = int(event.get("quantity", 1) or 1)
        weight = self._event_weight(event_type, quantity)
        occurred_at = event.get("occurred_at") or datetime.utcnow().isoformat()
        event_id = event.get("id") or f"{customer_id}:{event_type}:{occurred_at}:{product_id or 'none'}:{query or 'none'}"

        with driver.session() as session:
            session.run("MERGE (u:User {id: $customer_id})", customer_id=customer_id)
            session.run(
                """
                MERGE (e:BehaviorEvent {id: $event_id})
                SET e.event_type = $event_type,
                    e.occurred_at = $occurred_at,
                    e.quantity = $quantity,
                    e.weight = $weight
                WITH e
                MERGE (u:User {id: $customer_id})
                MERGE (u)-[:PERFORMED]->(e)
                """,
                event_id=event_id,
                event_type=event_type,
                occurred_at=occurred_at,
                quantity=quantity,
                weight=weight,
                customer_id=customer_id,
            )

            if category_name:
                session.run(
                    """
                    MERGE (u:User {id: $customer_id})
                    MERGE (c:Category {name: $category_name})
                    MERGE (u)-[r:INTERESTED_IN]->(c)
                    ON CREATE SET r.weight = $weight, r.last_event_at = $occurred_at
                    ON MATCH SET r.weight = coalesce(r.weight, 0) + $weight, r.last_event_at = $occurred_at
                    """,
                    customer_id=customer_id,
                    category_name=category_name,
                    weight=weight,
                    occurred_at=occurred_at,
                )
                session.run(
                    """
                    MERGE (e:BehaviorEvent {id: $event_id})
                    MERGE (c:Category {name: $category_name})
                    MERGE (e)-[:ABOUT_CATEGORY]->(c)
                    """,
                    event_id=event_id,
                    category_name=category_name,
                )

            if product_id:
                session.run(
                    """
                    MERGE (u:User {id: $customer_id})
                    MERGE (p:Product {id: $product_id})
                    MERGE (u)-[r:INTERACTED_WITH]->(p)
                    ON CREATE SET r.weight = $weight, r.last_event_at = $occurred_at, r.last_event_type = $event_type
                    ON MATCH SET r.weight = coalesce(r.weight, 0) + $weight,
                                  r.last_event_at = $occurred_at,
                                  r.last_event_type = $event_type
                    """,
                    customer_id=customer_id,
                    product_id=product_id,
                    weight=weight,
                    occurred_at=occurred_at,
                    event_type=event_type,
                )
                session.run(
                    """
                    MERGE (e:BehaviorEvent {id: $event_id})
                    MERGE (p:Product {id: $product_id})
                    MERGE (e)-[:ABOUT_PRODUCT]->(p)
                    """,
                    event_id=event_id,
                    product_id=product_id,
                )

                if category_name:
                    session.run(
                        """
                        MERGE (p:Product {id: $product_id})
                        MERGE (c:Category {name: $category_name})
                        MERGE (p)-[:BELONGS_TO]->(c)
                        """,
                        product_id=product_id,
                        category_name=category_name,
                    )

            if query:
                session.run(
                    """
                    MERGE (u:User {id: $customer_id})
                    MERGE (q:Query {text: $query})
                    MERGE (u)-[r:SEARCHED]->(q)
                    ON CREATE SET r.weight = $weight, r.last_event_at = $occurred_at
                    ON MATCH SET r.weight = coalesce(r.weight, 0) + $weight, r.last_event_at = $occurred_at
                    """,
                    customer_id=customer_id,
                    query=query,
                    weight=weight,
                    occurred_at=occurred_at,
                )
                session.run(
                    """
                    MERGE (e:BehaviorEvent {id: $event_id})
                    MERGE (q:Query {text: $query})
                    MERGE (e)-[:ABOUT_QUERY]->(q)
                    """,
                    event_id=event_id,
                    query=query,
                )

                if product_id:
                    session.run(
                        """
                        MERGE (q:Query {text: $query})
                        MERGE (p:Product {id: $product_id})
                        MERGE (q)-[r:MATCHES]->(p)
                        ON CREATE SET r.weight = $weight
                        ON MATCH SET r.weight = coalesce(r.weight, 0) + $weight
                        """,
                        query=query,
                        product_id=product_id,
                        weight=weight,
                    )
