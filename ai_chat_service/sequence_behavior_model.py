from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from torch import nn

ACTIONS = ["search", "view", "click", "add_to_cart", "wishlist", "coupon_view", "checkout", "purchase"]
PERSONAS = ["new_explorer", "category_browser", "deal_hunter", "loyal_member", "high_intent_buyer"]
NEXT_ACTIONS = ["recommend_entry_products", "push_coupon", "bundle_related_products", "upsell_membership", "reengage_catalog"]
ACTION_TO_ID = {name: idx + 1 for idx, name in enumerate(ACTIONS)}


def _price_sensitivity_from_features(features: dict[str, Any]) -> str:
    promo = int(features.get("promo_keyword_count", 0) or 0)
    avg = float(features.get("avg_order_value", 0) or 0)
    total = float(features.get("total_spent", 0) or 0)
    if promo >= 2 or (avg and avg < 120000):
        return "high"
    if avg < 260000 or total < 800000:
        return "medium"
    return "low"


def _purchase_intent_from_sequence(action_ids: list[int], features: dict[str, Any]) -> float:
    if not action_ids:
        return 0.1
    weights = {ACTION_TO_ID["search"]: 0.04, ACTION_TO_ID["view"]: 0.06, ACTION_TO_ID["click"]: 0.08, ACTION_TO_ID["wishlist"]: 0.1, ACTION_TO_ID["coupon_view"]: 0.07, ACTION_TO_ID["add_to_cart"]: 0.14, ACTION_TO_ID["checkout"]: 0.18, ACTION_TO_ID["purchase"]: 0.16}
    base = sum(weights.get(item, 0.02) for item in action_ids[-12:])
    base += 0.02 * float(features.get("order_count", 0) or 0)
    base += 0.01 * float(features.get("cart_item_count", 0) or 0)
    return round(max(0.05, min(0.95, base)), 3)


class SequenceClassifier(nn.Module):
    def __init__(self, cell_type: str, vocab_size: int, emb_dim: int = 24, hidden_dim: int = 32):
        super().__init__()
        self.cell_type = cell_type
        self.embedding = nn.Embedding(vocab_size, emb_dim, padding_idx=0)
        bidirectional = cell_type == "bilstm"
        if cell_type == "rnn":
            self.encoder = nn.RNN(emb_dim, hidden_dim, batch_first=True, nonlinearity="tanh")
        else:
            self.encoder = nn.LSTM(emb_dim, hidden_dim, batch_first=True, bidirectional=bidirectional)
        out_dim = hidden_dim * (2 if bidirectional else 1)
        self.persona_head = nn.Linear(out_dim, len(PERSONAS))
        self.nba_head = nn.Linear(out_dim, len(NEXT_ACTIONS))

    def forward(self, sequences: torch.Tensor, lengths: torch.Tensor):
        embedded = self.embedding(sequences)
        if self.cell_type == "rnn":
            _, hidden = self.encoder(embedded)
            features = hidden[-1]
        else:
            _, hidden = self.encoder(embedded)
            hidden_state = hidden[0]
            features = torch.cat([hidden_state[-2], hidden_state[-1]], dim=1) if self.cell_type == "bilstm" else hidden_state[-1]
        return self.persona_head(features), self.nba_head(features)


@dataclass
class SequencePrediction:
    persona: str
    next_best_action: str
    price_sensitivity: str
    purchase_intent: float
    used_sequence_model: bool
    sequence_actions: list[str]


class SequenceBehaviorModel:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.model_path = self.base_dir / "models" / "model_best.pt"
        self.meta_path = self.base_dir / "models" / "model_best_meta.json"
        self.model: SequenceClassifier | None = None
        self.device = torch.device("cpu")
        self.meta: dict[str, Any] = {}

    def ensure_ready(self) -> None:
        if self.model is not None:
            return
        if not self.model_path.exists():
            return
        bundle = torch.load(self.model_path, map_location="cpu")
        model_name = bundle.get("model_name", "bilstm")
        model = SequenceClassifier(model_name, vocab_size=len(ACTION_TO_ID) + 1)
        model.load_state_dict(bundle["state_dict"])
        model.eval()
        self.model = model
        if self.meta_path.exists():
            self.meta = json.loads(self.meta_path.read_text(encoding="utf-8"))

    def is_available(self) -> bool:
        self.ensure_ready()
        return self.model is not None

    def build_sequence(self, snapshot: dict[str, Any]) -> list[str]:
        actions: list[str] = []
        searches = snapshot.get("searches", []) or []
        recent_views = snapshot.get("recent_views", []) or []
        wishlist = (snapshot.get("wishlist") or {}).get("items", []) or []
        cart_items = (snapshot.get("cart") or {}).get("items", []) or []
        orders = snapshot.get("orders", []) or []
        for item in searches[-6:]:
            actions.append("search")
            query = str(item.get("query") or item.get("search_term") or "").lower()
            if any(keyword in query for keyword in ["sale", "voucher", "coupon", "giảm", "khuyến mãi"]):
                actions.append("coupon_view")
        for _ in recent_views[-6:]:
            actions.extend(["view", "click"])
        for _ in wishlist[-4:]:
            actions.append("wishlist")
        for item in cart_items[-4:]:
            quantity = int(item.get("quantity", 1) or 1)
            actions.extend(["add_to_cart"] * max(1, min(quantity, 2)))
        if cart_items:
            actions.append("checkout")
        for _ in orders[-4:]:
            actions.extend(["checkout", "purchase"])
        return actions[-32:] or ["search", "view"]

    def predict(self, snapshot: dict[str, Any]) -> SequencePrediction:
        self.ensure_ready()
        features = snapshot.get("feature_values", {}) or {}
        actions = self.build_sequence(snapshot)
        action_ids = [ACTION_TO_ID.get(item, 0) for item in actions if ACTION_TO_ID.get(item, 0)]
        if self.model is None or not action_ids:
            return SequencePrediction(
                persona=str(snapshot.get("behavior_context", {}).get("persona") or "new_explorer"),
                next_best_action=str(snapshot.get("behavior_context", {}).get("next_best_action") or "recommend_entry_products"),
                price_sensitivity=_price_sensitivity_from_features(features),
                purchase_intent=float(snapshot.get("behavior_context", {}).get("purchase_intent") or 0.1),
                used_sequence_model=False,
                sequence_actions=actions,
            )
        sequence_tensor = torch.tensor([action_ids], dtype=torch.long)
        lengths = torch.tensor([len(action_ids)], dtype=torch.long)
        with torch.no_grad():
            persona_logits, nba_logits = self.model(sequence_tensor, lengths)
        persona = PERSONAS[int(torch.argmax(persona_logits, dim=1).item())]
        next_action = NEXT_ACTIONS[int(torch.argmax(nba_logits, dim=1).item())]
        return SequencePrediction(
            persona=persona,
            next_best_action=next_action,
            price_sensitivity=_price_sensitivity_from_features(features),
            purchase_intent=_purchase_intent_from_sequence(action_ids, features),
            used_sequence_model=True,
            sequence_actions=actions,
        )
