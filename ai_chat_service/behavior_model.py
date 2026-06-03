from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np

FEATURES = [
    "search_count",
    "view_count",
    "wishlist_count",
    "cart_item_count",
    "order_count",
    "avg_order_value",
    "total_spent",
    "promo_keyword_count",
    "membership_points",
    "preferred_genre_count",
]
PERSONAS = ["new_explorer", "category_browser", "deal_hunter", "loyal_member", "high_intent_buyer"]
PRICE_LEVELS = ["low", "medium", "high"]
ACTIONS = ["recommend_entry_products", "push_coupon", "bundle_related_products", "upsell_membership", "reengage_catalog"]
MODEL_KIND = "deep_numpy_v1"


@dataclass
class BehaviorOutputs:
    persona: str
    price_sensitivity: str
    next_best_action: str
    purchase_intent: float


def _relu(x: np.ndarray) -> np.ndarray:
    return np.maximum(0.0, x)


def _relu_grad(x: np.ndarray) -> np.ndarray:
    return (x > 0).astype(np.float64)


def _softmax(x: np.ndarray) -> np.ndarray:
    shifted = x - np.max(x, axis=1, keepdims=True)
    exp_scores = np.exp(shifted)
    return exp_scores / np.sum(exp_scores, axis=1, keepdims=True)


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -35, 35)))


class DeepClassifier:
    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        hidden_dims: tuple[int, ...] = (64, 32, 16),
        learning_rate: float = 0.008,
        epochs: int = 180,
        batch_size: int = 64,
        seed: int = 42,
    ) -> None:
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.hidden_dims = hidden_dims
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size
        self.seed = seed
        self.mean_: np.ndarray | None = None
        self.std_: np.ndarray | None = None
        self.weights: list[np.ndarray] = []
        self.biases: list[np.ndarray] = []

    def _init_params(self) -> None:
        rng = np.random.default_rng(self.seed)
        dims = [self.input_dim, *self.hidden_dims, self.output_dim]
        self.weights = []
        self.biases = []
        for in_dim, out_dim in zip(dims[:-1], dims[1:]):
            scale = np.sqrt(2.0 / max(1, in_dim))
            self.weights.append(rng.normal(0.0, scale, size=(in_dim, out_dim)))
            self.biases.append(np.zeros((1, out_dim), dtype=np.float64))

    def _standardize_fit(self, x: np.ndarray) -> np.ndarray:
        self.mean_ = x.mean(axis=0, keepdims=True)
        self.std_ = x.std(axis=0, keepdims=True) + 1e-6
        return (x - self.mean_) / self.std_

    def _standardize(self, x: np.ndarray) -> np.ndarray:
        assert self.mean_ is not None and self.std_ is not None
        return (x - self.mean_) / self.std_

    def _forward(self, x: np.ndarray) -> tuple[list[np.ndarray], list[np.ndarray]]:
        activations = [x]
        pre_activations: list[np.ndarray] = []
        current = x
        for idx, (weights, bias) in enumerate(zip(self.weights, self.biases)):
            z = current @ weights + bias
            pre_activations.append(z)
            if idx == len(self.weights) - 1:
                current = _softmax(z)
            else:
                current = _relu(z)
            activations.append(current)
        return activations, pre_activations

    def fit(self, x_train: np.ndarray, y_train: np.ndarray) -> None:
        x_norm = self._standardize_fit(x_train.astype(np.float64))
        self._init_params()
        sample_count = len(x_norm)

        for epoch in range(self.epochs):
            rng = np.random.default_rng(self.seed + epoch)
            indices = rng.permutation(sample_count)
            for start in range(0, sample_count, self.batch_size):
                batch_idx = indices[start : start + self.batch_size]
                batch_x = x_norm[batch_idx]
                batch_y = y_train[batch_idx]

                activations, pre_activations = self._forward(batch_x)
                probs = activations[-1]
                grad = (probs - batch_y) / max(1, len(batch_x))

                for layer in reversed(range(len(self.weights))):
                    grad_w = activations[layer].T @ grad
                    grad_b = np.sum(grad, axis=0, keepdims=True)
                    self.weights[layer] -= self.learning_rate * grad_w
                    self.biases[layer] -= self.learning_rate * grad_b
                    if layer > 0:
                        grad = (grad @ self.weights[layer].T) * _relu_grad(pre_activations[layer - 1])

    def predict_proba(self, x_pred: np.ndarray) -> np.ndarray:
        x_norm = self._standardize(x_pred.astype(np.float64))
        activations, _ = self._forward(x_norm)
        return activations[-1]

    def predict(self, x_pred: np.ndarray, labels: list[str]) -> list[str]:
        probs = self.predict_proba(x_pred)
        indices = np.argmax(probs, axis=1)
        return [labels[int(idx)] for idx in indices]


class DeepRegressor:
    def __init__(
        self,
        input_dim: int,
        hidden_dims: tuple[int, ...] = (64, 32, 16),
        learning_rate: float = 0.006,
        epochs: int = 200,
        batch_size: int = 64,
        seed: int = 42,
    ) -> None:
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size
        self.seed = seed
        self.mean_: np.ndarray | None = None
        self.std_: np.ndarray | None = None
        self.weights: list[np.ndarray] = []
        self.biases: list[np.ndarray] = []

    def _init_params(self) -> None:
        rng = np.random.default_rng(self.seed)
        dims = [self.input_dim, *self.hidden_dims, 1]
        self.weights = []
        self.biases = []
        for in_dim, out_dim in zip(dims[:-1], dims[1:]):
            scale = np.sqrt(2.0 / max(1, in_dim))
            self.weights.append(rng.normal(0.0, scale, size=(in_dim, out_dim)))
            self.biases.append(np.zeros((1, out_dim), dtype=np.float64))

    def _standardize_fit(self, x: np.ndarray) -> np.ndarray:
        self.mean_ = x.mean(axis=0, keepdims=True)
        self.std_ = x.std(axis=0, keepdims=True) + 1e-6
        return (x - self.mean_) / self.std_

    def _standardize(self, x: np.ndarray) -> np.ndarray:
        assert self.mean_ is not None and self.std_ is not None
        return (x - self.mean_) / self.std_

    def _forward(self, x: np.ndarray) -> tuple[list[np.ndarray], list[np.ndarray]]:
        activations = [x]
        pre_activations: list[np.ndarray] = []
        current = x
        for idx, (weights, bias) in enumerate(zip(self.weights, self.biases)):
            z = current @ weights + bias
            pre_activations.append(z)
            if idx == len(self.weights) - 1:
                current = _sigmoid(z)
            else:
                current = _relu(z)
            activations.append(current)
        return activations, pre_activations

    def fit(self, x_train: np.ndarray, y_train: np.ndarray) -> None:
        x_norm = self._standardize_fit(x_train.astype(np.float64))
        self._init_params()
        sample_count = len(x_norm)
        y_target = y_train.reshape(-1, 1).astype(np.float64)

        for epoch in range(self.epochs):
            rng = np.random.default_rng(self.seed + epoch)
            indices = rng.permutation(sample_count)
            for start in range(0, sample_count, self.batch_size):
                batch_idx = indices[start : start + self.batch_size]
                batch_x = x_norm[batch_idx]
                batch_y = y_target[batch_idx]

                activations, pre_activations = self._forward(batch_x)
                preds = activations[-1]
                grad = ((preds - batch_y) * preds * (1.0 - preds)) / max(1, len(batch_x))

                for layer in reversed(range(len(self.weights))):
                    grad_w = activations[layer].T @ grad
                    grad_b = np.sum(grad, axis=0, keepdims=True)
                    self.weights[layer] -= self.learning_rate * grad_w
                    self.biases[layer] -= self.learning_rate * grad_b
                    if layer > 0:
                        grad = (grad @ self.weights[layer].T) * _relu_grad(pre_activations[layer - 1])

    def predict(self, x_pred: np.ndarray) -> np.ndarray:
        x_norm = self._standardize(x_pred.astype(np.float64))
        activations, _ = self._forward(x_norm)
        return activations[-1].reshape(-1)


class BehaviorModel:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.model_dir = self.base_dir / "models"
        self.data_dir = self.base_dir / "data"
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.bundle_path = self.model_dir / "behavior_bundle.joblib"
        self.csv_path = self.data_dir / "mock_behavior_training.csv"
        self.bundle: dict[str, Any] | None = None

    def ensure_ready(self) -> None:
        if self.bundle is not None:
            return
        if self.bundle_path.exists():
            loaded = joblib.load(self.bundle_path)
            if isinstance(loaded, dict) and loaded.get("model_kind") == MODEL_KIND:
                self.bundle = loaded
                return
        self.train_and_save()

    def _sample_row(self, rng: np.random.Generator) -> tuple[list[float], str, str, str, float]:
        search = int(rng.integers(0, 12))
        views = int(rng.integers(0, 20))
        wishlist = int(rng.integers(0, 8))
        cart = int(rng.integers(0, 6))
        orders = int(rng.integers(0, 15))
        avg_value = float(rng.normal(150000 + orders * 5000, 55000))
        avg_value = max(45000.0, min(avg_value, 850000.0))
        total_spent = max(0.0, float(avg_value * orders + rng.normal(0, 160000)))
        promo = int(rng.integers(0, 7))
        points = max(0, int(total_spent // 8000 + rng.integers(-80, 80)))
        pref_categories = int(rng.integers(0, 5))

        score = (
            0.18 * min(search, 8)
            + 0.25 * min(views, 10)
            + 0.45 * min(wishlist, 5)
            + 0.9 * min(cart, 4)
            + 0.6 * min(orders, 6)
            + 0.0000015 * total_spent
            - 0.18 * promo
        )
        purchase_intent = float(1 / (1 + np.exp(-(score - 3.4))))
        purchase_intent = float(np.clip(purchase_intent + rng.normal(0, 0.04), 0.02, 0.99))

        if orders == 0 and views <= 3 and wishlist == 0:
            persona = "new_explorer"
        elif promo >= 3 and total_spent < 500000:
            persona = "deal_hunter"
        elif orders >= 5 and total_spent > 1200000:
            persona = "loyal_member"
        elif cart >= 2 or purchase_intent > 0.72:
            persona = "high_intent_buyer"
        else:
            persona = "category_browser"

        if promo >= 3 or avg_value < 120000:
            price = "high"
        elif avg_value < 280000:
            price = "medium"
        else:
            price = "low"

        if persona == "deal_hunter":
            action = "push_coupon"
        elif persona == "loyal_member" and points >= 500:
            action = "upsell_membership"
        elif persona == "high_intent_buyer":
            action = "bundle_related_products"
        elif persona == "new_explorer":
            action = "recommend_entry_products"
        else:
            action = "reengage_catalog"

        feats = [search, views, wishlist, cart, orders, avg_value, total_spent, promo, points, pref_categories]
        return feats, persona, price, action, purchase_intent

    def train_and_save(self, n_samples: int = 1200, seed: int = 42) -> None:
        rng = np.random.default_rng(seed)
        rows = [self._sample_row(rng) for _ in range(n_samples)]
        x_train = np.array([row[0] for row in rows], dtype=np.float64)
        y_persona = [row[1] for row in rows]
        y_price = [row[2] for row in rows]
        y_action = [row[3] for row in rows]
        y_intent = np.array([row[4] for row in rows], dtype=np.float64)

        persona_targets = np.eye(len(PERSONAS), dtype=np.float64)[[PERSONAS.index(label) for label in y_persona]]
        price_targets = np.eye(len(PRICE_LEVELS), dtype=np.float64)[[PRICE_LEVELS.index(label) for label in y_price]]
        action_targets = np.eye(len(ACTIONS), dtype=np.float64)[[ACTIONS.index(label) for label in y_action]]

        persona_model = DeepClassifier(len(FEATURES), len(PERSONAS), hidden_dims=(64, 32, 16), learning_rate=0.0075, epochs=190, seed=seed)
        price_model = DeepClassifier(len(FEATURES), len(PRICE_LEVELS), hidden_dims=(48, 24, 12), learning_rate=0.007, epochs=170, seed=seed + 1)
        action_model = DeepClassifier(len(FEATURES), len(ACTIONS), hidden_dims=(64, 32, 16), learning_rate=0.0075, epochs=190, seed=seed + 2)
        intent_model = DeepRegressor(len(FEATURES), hidden_dims=(64, 32, 16), learning_rate=0.0055, epochs=220, seed=seed + 3)

        persona_model.fit(x_train, persona_targets)
        price_model.fit(x_train, price_targets)
        action_model.fit(x_train, action_targets)
        intent_model.fit(x_train, y_intent)

        self.bundle = {
            "model_kind": MODEL_KIND,
            "persona_model": persona_model,
            "price_model": price_model,
            "action_model": action_model,
            "intent_model": intent_model,
            "features": FEATURES,
        }
        joblib.dump(self.bundle, self.bundle_path)
        self._write_mock_csv(rows)

    def _write_mock_csv(self, rows: list[tuple[list[float], str, str, str, float]]) -> None:
        with self.csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(FEATURES + ["persona", "price_sensitivity", "next_best_action", "purchase_intent"])
            for features, persona, price, action, intent in rows:
                writer.writerow(features + [persona, price, action, round(intent, 4)])

    def predict(self, feature_values: dict[str, Any]) -> BehaviorOutputs:
        self.ensure_ready()
        assert self.bundle is not None

        x_pred = np.array([[float(feature_values.get(name, 0) or 0) for name in FEATURES]], dtype=np.float64)
        persona = self.bundle["persona_model"].predict(x_pred, PERSONAS)[0]
        price = self.bundle["price_model"].predict(x_pred, PRICE_LEVELS)[0]
        action = self.bundle["action_model"].predict(x_pred, ACTIONS)[0]
        intent = float(np.clip(self.bundle["intent_model"].predict(x_pred)[0], 0.01, 0.99))

        search_count = float(feature_values.get("search_count", 0) or 0)
        view_count = float(feature_values.get("view_count", 0) or 0)
        wishlist_count = float(feature_values.get("wishlist_count", 0) or 0)
        cart_item_count = float(feature_values.get("cart_item_count", 0) or 0)
        order_count = float(feature_values.get("order_count", 0) or 0)
        avg_order_value = float(feature_values.get("avg_order_value", 0) or 0)
        total_spent = float(feature_values.get("total_spent", 0) or 0)
        promo_keyword_count = float(feature_values.get("promo_keyword_count", 0) or 0)
        membership_points = float(feature_values.get("membership_points", 0) or 0)

        engagement = search_count + view_count + wishlist_count * 2 + cart_item_count * 3 + order_count * 2
        heuristic_intent = min(
            0.95,
            max(
                0.05,
                0.04 * search_count
                + 0.05 * view_count
                + 0.12 * wishlist_count
                + 0.18 * cart_item_count
                + 0.08 * order_count,
            ),
        )
        intent = round(float(np.clip((intent + heuristic_intent) / 2, 0.05, 0.95)), 3)

        if order_count == 0 and engagement <= 2:
            persona = "new_explorer"
            action = "recommend_entry_products"
            intent = min(intent, 0.22)
        elif promo_keyword_count >= 2 and total_spent < 500000:
            persona = "deal_hunter"
            action = "push_coupon"
        elif order_count >= 5 and total_spent > 1200000:
            persona = "loyal_member"
            action = "upsell_membership" if membership_points >= 500 else "bundle_related_products"
        elif cart_item_count >= 1 or wishlist_count >= 2:
            persona = "high_intent_buyer"
            action = "bundle_related_products"
            intent = max(intent, 0.68)
        elif engagement >= 4:
            persona = "category_browser"
            action = "reengage_catalog"

        if promo_keyword_count >= 2 or avg_order_value < 120000:
            price = "high"
        elif avg_order_value < 280000 or total_spent < 900000:
            price = "medium"
        else:
            price = "low"

        return BehaviorOutputs(persona=persona, price_sensitivity=price, next_best_action=action, purchase_intent=intent)
