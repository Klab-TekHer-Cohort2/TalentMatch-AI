import json
import logging
import math
import threading
from pathlib import Path
from typing import Any

from ..config import settings

logger = logging.getLogger(__name__)


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class CourseVectorStore:
    """ChromaDB-backed course index with a JSON fallback for offline/dev use."""

    def __init__(self) -> None:
        self._collection = None
        self._backend: str | None = None
        self._fallback: dict[str, list] = {"ids": [], "documents": [], "metadatas": [], "embeddings": []}
        self._lock = threading.Lock()
        self._fallback_path = Path(settings.chroma_dir) / "fallback_courses.json"

    def _init(self) -> None:
        if self._backend is not None:
            return
        with self._lock:
            if self._backend is not None:
                return
            try:
                import chromadb

                Path(settings.chroma_dir).mkdir(parents=True, exist_ok=True)
                client = chromadb.PersistentClient(path=settings.chroma_dir)
                self._collection = client.get_or_create_collection(
                    name=settings.vector_collection,
                    metadata={"hnsw:space": "cosine"},
                )
                self._backend = "chromadb"
                logger.info("Using ChromaDB collection '%s'", settings.vector_collection)
                return
            except Exception as exc:
                logger.warning("ChromaDB unavailable (%s); using JSON vector fallback", exc)
                self._backend = "json"
                self._load_fallback()

    def _load_fallback(self) -> None:
        if not self._fallback_path.exists():
            return
        try:
            data = json.loads(self._fallback_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self._fallback = {
                    "ids": data.get("ids", []),
                    "documents": data.get("documents", []),
                    "metadatas": data.get("metadatas", []),
                    "embeddings": data.get("embeddings", []),
                }
        except Exception as exc:
            logger.warning("Could not load fallback vector index: %s", exc)

    def _save_fallback(self) -> None:
        self._fallback_path.parent.mkdir(parents=True, exist_ok=True)
        self._fallback_path.write_text(json.dumps(self._fallback), encoding="utf-8")

    @property
    def backend(self) -> str:
        self._init()
        return self._backend or "json"

    def reset(self) -> None:
        self._init()
        if self._backend == "chromadb":
            try:
                self._collection.delete(where={"course_id": {"$gte": 0}})
            except Exception:
                pass
            self._collection = None
            self._backend = None
            self._init()
        else:
            self._fallback = {"ids": [], "documents": [], "metadatas": [], "embeddings": []}
            self._save_fallback()

    def upsert(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        self._init()
        if not ids:
            return
        if self._backend == "chromadb":
            self._collection.upsert(
                ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas
            )
            return
        by_id = {existing: index for index, existing in enumerate(self._fallback["ids"])}
        for index, item_id in enumerate(ids):
            payload = {
                "documents": documents[index],
                "metadatas": metadatas[index],
                "embeddings": embeddings[index],
            }
            if item_id in by_id:
                position = by_id[item_id]
                self._fallback["documents"][position] = payload["documents"]
                self._fallback["metadatas"][position] = payload["metadatas"]
                self._fallback["embeddings"][position] = payload["embeddings"]
            else:
                by_id[item_id] = len(self._fallback["ids"])
                self._fallback["ids"].append(item_id)
                self._fallback["documents"].append(payload["documents"])
                self._fallback["metadatas"].append(payload["metadatas"])
                self._fallback["embeddings"].append(payload["embeddings"])
        self._save_fallback()

    def query(self, embedding: list[float], n_results: int = 6) -> list[dict[str, Any]]:
        self._init()
        if self._backend == "chromadb":
            total = self._collection.count()
            if total == 0:
                return []
            result = self._collection.query(
                query_embeddings=[embedding],
                n_results=min(max(n_results, 1), total),
                include=["documents", "metadatas", "distances"],
            )
            items: list[dict[str, Any]] = []
            ids = (result.get("ids") or [[]])[0]
            documents = (result.get("documents") or [[]])[0]
            metadatas = (result.get("metadatas") or [[]])[0]
            distances = (result.get("distances") or [[]])[0]
            for index, item_id in enumerate(ids):
                distance = distances[index] if index < len(distances) else 1.0
                items.append(
                    {
                        "id": item_id,
                        "document": documents[index] if index < len(documents) else "",
                        "metadata": metadatas[index] if index < len(metadatas) else {},
                        "score": max(0.0, min(1.0, 1.0 - float(distance))),
                    }
                )
            return items

        scored = [
            {
                "id": item_id,
                "document": self._fallback["documents"][index],
                "metadata": self._fallback["metadatas"][index],
                "score": max(0.0, _cosine(embedding, self._fallback["embeddings"][index])),
            }
            for index, item_id in enumerate(self._fallback["ids"])
        ]
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:n_results]

    def count(self) -> int:
        self._init()
        if self._backend == "chromadb":
            return self._collection.count()
        return len(self._fallback["ids"])


course_store = CourseVectorStore()
