import hashlib
import logging
import math
import re
import threading

from ..config import settings

logger = logging.getLogger(__name__)

TOKEN_RE = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9+#.]*")


class HashingEmbedder:
    """Deterministic offline fallback with the same dimensionality as MiniLM.

    Uses hashed word unigrams, word bigrams and character trigrams. It is not a
    neural model, but it provides stable lexical similarity so the full product
    pipeline works without downloading model weights.
    """

    dimension = 384

    def __init__(self) -> None:
        self._dim = self.dimension

    def _add(self, vector: list[float], token: str, weight: float) -> None:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "little") % self._dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign * weight

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self._dim
        tokens = [token.lower() for token in TOKEN_RE.findall(text or "")]
        counts: dict[str, int] = {}
        for token in tokens:
            counts[token] = counts.get(token, 0) + 1

        for token, count in counts.items():
            self._add(vector, token, 1.0 + math.log(count))
            for start in range(len(token) - 2):
                self._add(vector, f"#{token[start:start + 3]}", 0.35)
            if len(token) > 6:
                self._add(vector, f"~{token[:6]}", 0.6)

        for first, second in zip(tokens, tokens[1:]):
            self._add(vector, f"{first}_{second}", 0.5)

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]


class EmbeddingService:
    def __init__(self) -> None:
        self._model = None
        self._fallback = HashingEmbedder()
        self._backend: str | None = None
        self._lock = threading.Lock()

    def _load(self) -> None:
        if self._backend is not None:
            return
        with self._lock:
            if self._backend is not None:
                return
            if settings.embedding_backend.lower() == "hashing":
                self._backend = "hashing"
                logger.info("Embedding backend forced to deterministic hashing")
                return
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(settings.embedding_model)
                self._backend = f"sentence-transformers:{settings.embedding_model}"
                logger.info("Loaded embedding model %s", settings.embedding_model)
            except Exception as exc:  # missing package, offline download, etc.
                logger.warning("Sentence Transformers unavailable (%s); using hashing fallback", exc)
                self._backend = "hashing"

    @property
    def backend(self) -> str:
        self._load()
        return self._backend or "hashing"

    def embed(self, text: str) -> list[float]:
        self._load()
        if self._backend and self._backend.startswith("sentence-transformers"):
            vector = self._model.encode(text or "", normalize_embeddings=True)
            return [float(value) for value in vector]
        return self._fallback.embed(text)

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        self._load()
        if self._backend and self._backend.startswith("sentence-transformers"):
            vectors = self._model.encode(texts, normalize_embeddings=True, batch_size=32)
            return [[float(value) for value in vector] for vector in vectors]
        return self._fallback.embed_many(texts)


embedder = EmbeddingService()


def cv_embedding_text(skills: list[str], job_titles: list[str], summary: str, raw_text: str) -> str:
    parts = [
        "Candidate profile.",
        f"Titles: {', '.join(job_titles) or 'unspecified'}.",
        f"Skills: {', '.join(skills) or 'unspecified'}.",
        f"Summary: {summary or ''}",
        f"CV content: {(raw_text or '')[:6000]}",
    ]
    return "\n".join(parts)


def job_embedding_text(title: str, description: str, skills: list[str], location: str | None = None) -> str:
    parts = [
        f"Job title: {title}.",
        f"Location: {location or 'unspecified'}.",
        f"Required skills: {', '.join(skills) or 'unspecified'}.",
        f"Description: {description[:6000]}",
    ]
    return "\n".join(parts)
