from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from advisor import MarketplaceAdvisor
from auth import get_current_user

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="AI Chat Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

advisor = MarketplaceAdvisor(str(BASE_DIR))
_metrics = {"chat_requests": 0, "started_at": datetime.utcnow().isoformat()}


class ChatRequest(BaseModel):
    question: str


@app.on_event("startup")
def startup() -> None:
    advisor.behavior_model.ensure_ready()
    advisor.sequence_behavior_model.ensure_ready()
    advisor.kb.ensure_ready()
    advisor.graph.ensure_ready()
    advisor.graph.sync_catalog()
    advisor.graph.sync_marketing()


@app.get("/")
def root() -> dict:
    return {
        "service": "ai_chat_service",
        "version": "1.0.0",
        "capabilities": [
            "behavior-based recommendation",
            "knowledge base retrieval",
            "graph-based knowledge retrieval",
            "RAG chatbot for marketplace",
            "personalized recommendations",
        ],
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ai_chat_service", "timestamp": datetime.utcnow().isoformat()}


@app.get("/metrics")
def metrics() -> dict:
    return _metrics


@app.post("/chat/ask")
def ask_chat(body: ChatRequest, user: dict = Depends(get_current_user)) -> dict:
    _metrics["chat_requests"] += 1
    return advisor.answer(customer_id=user["user_id"], question=body.question, user_name=user.get("name", "Khách hàng"))


@app.get("/recommendations")
def recommendations(limit: int = 6, user: dict = Depends(get_current_user)) -> dict:
    return advisor.recommend(customer_id=user["user_id"], user_name=user.get("name", "Khách hàng"), limit=limit)


@app.get("/debug/profile")
def debug_profile(user: dict = Depends(get_current_user)) -> dict:
    snapshot = advisor.services.get_user_snapshot(user["user_id"])
    fallback_behavior = advisor.behavior_model.predict(snapshot.get("feature_values", {}))
    sequence_behavior = advisor.sequence_behavior_model.predict(snapshot)
    return {"snapshot": snapshot, "behavior": fallback_behavior.__dict__, "sequence_behavior": sequence_behavior.__dict__}
