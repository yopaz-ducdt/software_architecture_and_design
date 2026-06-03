from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.utils.validation import check_is_fitted


@dataclass
class KBHit:
    title: str
    content: str
    score: float


class KBStore:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.docs_dir = self.base_dir / "kb_docs"
        self.models_dir = self.base_dir / "models"
        self.models_dir.mkdir(exist_ok=True)
        self.store_path = self.models_dir / "kb_store.joblib"
        self.vectorizer: TfidfVectorizer | None = None
        self.matrix = None
        self.docs: list[dict] = []

    def _split_markdown_chunks(self, title: str, text: str) -> list[dict]:
        normalized = text.replace("\r\n", "\n").strip()
        if not normalized:
            return [{"title": title, "content": ""}]

        sections = re.split(r"\n(?=#)", normalized)
        chunks: list[dict] = []
        for section in sections:
            section = section.strip()
            if not section:
                continue
            lines = section.splitlines()
            heading = title
            body = section
            if lines and lines[0].startswith("#"):
                heading = f"{title} - {lines[0].lstrip('#').strip()}"
                body = "\n".join(lines[1:]).strip() or section

            paragraphs = [part.strip() for part in re.split(r"\n\s*\n", body) if part.strip()]
            if not paragraphs:
                paragraphs = [body]

            current = ""
            chunk_index = 1
            for paragraph in paragraphs:
                candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
                if len(candidate) > 700 and current:
                    chunks.append({"title": f"{heading} ({chunk_index})", "content": current.strip()})
                    chunk_index += 1
                    current = paragraph
                else:
                    current = candidate
            if current:
                chunks.append({"title": f"{heading} ({chunk_index})", "content": current.strip()})
        return chunks or [{"title": title, "content": normalized}]

    def _iter_docs(self) -> Iterable[dict]:
        for path in sorted(self.docs_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            title = path.stem.replace("_", " ")
            for chunk in self._split_markdown_chunks(title, text):
                yield chunk

    def _fit(self) -> None:
        self.docs = list(self._iter_docs())
        self.vectorizer = TfidfVectorizer(stop_words=None, ngram_range=(1, 2))
        corpus = [f"{doc['title']}\n{doc['content']}" for doc in self.docs] or [""]
        self.matrix = self.vectorizer.fit_transform(corpus)
        joblib.dump({"vectorizer": self.vectorizer, "matrix": self.matrix, "docs": self.docs}, self.store_path)

    def ensure_ready(self) -> None:
        if self.vectorizer is not None and self.matrix is not None and self.docs:
            return
        if self.store_path.exists():
            try:
                bundle = joblib.load(self.store_path)
                self.vectorizer = bundle.get("vectorizer")
                self.matrix = bundle.get("matrix")
                self.docs = bundle.get("docs", [])
                check_is_fitted(self.vectorizer, attributes=["idf_"])
                return
            except Exception:
                pass
        self._fit()

    def search(self, query: str, top_k: int = 3) -> list[KBHit]:
        self.ensure_ready()
        assert self.vectorizer is not None and self.matrix is not None
        try:
            q_vector = self.vectorizer.transform([query])
        except Exception:
            self._fit()
            q_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(q_vector, self.matrix).flatten()
        order = np.argsort(-similarities)[:top_k]
        hits: list[KBHit] = []
        for idx in order:
            if idx < len(self.docs):
                doc = self.docs[int(idx)]
                hits.append(KBHit(title=doc["title"], content=doc["content"], score=float(similarities[idx])))
        return hits
