#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Governed Knowledge API（Phase C）。

承認済みKnowledge（approved_knowledge.json）だけを参照する読み取り専用API。
- GET /health                 : 稼働確認（200）
- GET /knowledge/search?q=...  : 承認済みのみ検索。該当があれば answerable=true、
                                 無ければ answerable=false（fallback=human_review）。

検索は Embedding（Azure OpenAI）優先・テキスト類似度フォールバック。
APIキーが無い／呼び出し失敗時はテキスト類似度のみで動作する（実キー無しでも動く）。
"""

from __future__ import annotations

import os
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from fastapi import FastAPI, Query

try:  # JSON読み込みは標準ライブラリのみ
    import json
except ImportError:  # pragma: no cover - 標準ライブラリなので実質発生しない
    raise


DEFAULT_APPROVED_PATH = "data/outputs/approved_knowledge.json"
# Embedding一致のしきい値（cosine類似度）
EMBEDDING_THRESHOLD = 0.80
# テキスト類似度（SequenceMatcher）のしきい値
TEXT_THRESHOLD = 0.86


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """2ベクトルのコサイン類似度。"""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _normalize(text: str) -> str:
    """比較用に空白を畳んで小文字化する。"""
    return " ".join(str(text or "").split()).lower()


def _is_approved(item: Dict[str, Any]) -> bool:
    """API側でも承認済みステータスだけに絞る。"""
    return str(item.get("approved_status", "")).strip().lower() == "approved"


class EmbeddingBackend(Protocol):
    """Embeddingベクトル化のインターフェース（テストで差し替え可能）。"""

    def embed(self, texts: List[str]) -> Optional[List[List[float]]]:
        """テキスト群をベクトル化する。利用不可なら None を返す。"""
        ...


class AzureEmbeddingBackend:
    """Azure OpenAI Embeddingを使うバックエンド。キー未設定時は None を返す。"""

    def __init__(self) -> None:
        self._client = None
        self._model = os.getenv(
            "AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
        )

    def _get_client(self):
        if self._client is not None:
            return self._client
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT_EMBEDDING")
        api_key = os.getenv("AZURE_OPENAI_API_KEY_EMBEDDING")
        if not endpoint or not api_key:
            return None
        try:
            from openai import AzureOpenAI

            self._client = AzureOpenAI(
                api_key=api_key,
                api_version="2024-02-01",
                azure_endpoint=endpoint,
            )
            return self._client
        except Exception:  # noqa: BLE001
            return None

    def embed(self, texts: List[str]) -> Optional[List[List[float]]]:
        client = self._get_client()
        if not client or not texts:
            return None
        try:
            response = client.embeddings.create(model=self._model, input=texts)
            return [d.embedding for d in response.data]
        except Exception:  # noqa: BLE001
            return None


class GovernedKnowledgeService:
    """承認済みKnowledgeの読み込みと検索を担う。"""

    def __init__(
        self,
        approved_path: str | Path | None = None,
        embedding_backend: EmbeddingBackend | None = None,
        embedding_threshold: float = EMBEDDING_THRESHOLD,
        text_threshold: float = TEXT_THRESHOLD,
    ) -> None:
        self.approved_path = Path(
            approved_path
            or os.getenv("APPROVED_KNOWLEDGE_PATH", DEFAULT_APPROVED_PATH)
        )
        self.embedding_backend = embedding_backend or AzureEmbeddingBackend()
        self.embedding_threshold = embedding_threshold
        self.text_threshold = text_threshold
        self._items: List[Dict[str, Any]] = []
        self._signature: tuple[float, int] | None = None

    # --- データ読み込み ---------------------------------------------------
    def _load_if_needed(self) -> None:
        """approved_knowledge.json を更新検知付きで読み込む。

        mtimeの解像度が粗い環境でも取りこぼさないよう、mtimeとサイズの
        両方で変更を検知する。
        """
        if not self.approved_path.exists():
            self._items = []
            self._signature = None
            return
        stat = self.approved_path.stat()
        signature = (stat.st_mtime, stat.st_size)
        if self._signature is not None and signature == self._signature:
            return
        try:
            with self.approved_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            self._items = []
            self._signature = signature
            return
        self._items = [
            item for item in data if isinstance(item, dict) and _is_approved(item)
        ]
        self._signature = signature

    # --- 検索 -------------------------------------------------------------
    def search(self, query: str) -> Dict[str, Any]:
        """承認済みのみ検索し、answerable分岐の結果を返す。"""
        self._load_if_needed()
        normalized_query = _normalize(query)
        if not normalized_query or not self._items:
            return self._not_found()

        questions = [str(item.get("question", "")) for item in self._items]

        # 1) 完全一致（正規化後）は最優先
        for idx, question in enumerate(questions):
            if _normalize(question) == normalized_query:
                return self._answer(self._items[idx])

        # 2) Embedding一致（利用可能なとき）
        best_idx = self._search_by_embedding(query, questions)
        if best_idx is None:
            # 3) テキスト類似度フォールバック
            best_idx = self._search_by_text(normalized_query, questions)

        if best_idx is None:
            return self._not_found()
        return self._answer(self._items[best_idx])

    def _search_by_embedding(
        self, query: str, questions: List[str]
    ) -> Optional[int]:
        embeddings = self.embedding_backend.embed([query, *questions])
        if not embeddings or len(embeddings) != len(questions) + 1:
            return None
        query_vec = embeddings[0]
        best_idx: Optional[int] = None
        best_score = -1.0
        for idx, vec in enumerate(embeddings[1:]):
            score = _cosine_similarity(query_vec, vec)
            if score > best_score:
                best_score = score
                best_idx = idx
        if best_idx is not None and best_score >= self.embedding_threshold:
            return best_idx
        return None

    def _search_by_text(
        self, normalized_query: str, questions: List[str]
    ) -> Optional[int]:
        best_idx: Optional[int] = None
        best_score = -1.0
        for idx, question in enumerate(questions):
            normalized_question = _normalize(question)
            if not normalized_question:
                continue
            score = SequenceMatcher(
                None, normalized_query, normalized_question
            ).ratio()
            if score > best_score:
                best_score = score
                best_idx = idx
        if best_idx is not None and best_score >= self.text_threshold:
            return best_idx
        return None

    # --- レスポンス整形 ---------------------------------------------------
    @staticmethod
    def _answer(item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "answerable": True,
            "knowledge_id": str(item.get("knowledge_id", "")),
            "question": str(item.get("question", "")),
            "answer": str(item.get("answer", "")),
            "source": "approved_knowledge",
        }

    @staticmethod
    def _not_found() -> Dict[str, Any]:
        return {
            "answerable": False,
            "reason": "No approved knowledge found",
            "fallback": "human_review",
        }


def create_app(service: GovernedKnowledgeService | None = None) -> FastAPI:
    """FastAPIアプリを生成する。serviceを渡せばテストで差し替え可能。"""
    app = FastAPI(title="Governed Knowledge API", version="1.0.0")
    knowledge_service = service or GovernedKnowledgeService()

    @app.get("/health")
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.get("/knowledge/search")
    def knowledge_search(
        q: str = Query(..., description="検索したい質問文")
    ) -> Dict[str, Any]:
        return knowledge_service.search(q)

    return app


app = create_app()
