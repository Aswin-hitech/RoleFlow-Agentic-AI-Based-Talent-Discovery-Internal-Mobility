"""Embedding service — BGE-base / Sentence-BERT with fast normalized fallback."""

import hashlib
import logging
import math
import os
from functools import lru_cache

from ..config import Config

logger = logging.getLogger(__name__)


_MODEL_INITIALIZED = False
_CACHED_MODEL = None


def get_embedding_model():
    global _MODEL_INITIALIZED, _CACHED_MODEL
    if _MODEL_INITIALIZED:
        return _CACHED_MODEL

    _MODEL_INITIALIZED = True
    use_st = os.getenv("USE_SENTENCE_TRANSFORMERS", "false").lower() in ("1", "true", "yes")
    if not use_st:
        _CACHED_MODEL = None
        return None

    try:
        from sentence_transformers import SentenceTransformer
        try:
            _CACHED_MODEL = SentenceTransformer(
                Config.EMBEDDING_MODEL,
                device=Config.EMBEDDING_DEVICE,
                local_files_only=True,
            )
        except Exception:
            if os.getenv("ENABLE_HF_DOWNLOAD", "false").lower() in ("1", "true", "yes"):
                _CACHED_MODEL = SentenceTransformer(Config.EMBEDDING_MODEL, device=Config.EMBEDDING_DEVICE)
            else:
                _CACHED_MODEL = None
    except Exception as exc:
        logger.info("SentenceTransformer not loaded (%s), using fast semantic hashing embedder", exc)
        _CACHED_MODEL = None

    return _CACHED_MODEL


def _fallback_embed(text: str, dim: int = 768) -> list[float]:
    """Deterministic, normalized pseudo-embedding based on word n-grams and hashing."""
    vec = [0.0] * dim
    words = text.lower().split()
    if not words:
        return vec
    for word in words:
        # Hash into coordinates
        h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if ((h >> 8) & 1) else -1.0
        vec[idx] += sign
    # Normalize vector to unit length
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [round(x / norm, 5) for x in vec]


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Normalized embeddings, cosine-similarity ready."""
    model = get_embedding_model()
    if model:
        try:
            vectors = model.encode(texts, normalize_embeddings=True)
            return [vector.tolist() for vector in vectors]
        except Exception as exc:
            logger.warning("Embedding encode failed: %s, falling back", exc)

    return [_fallback_embed(t, Config.EMBEDDING_DIM) for t in texts]


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    if not vec_a or not vec_b:
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a)) or 1.0
    norm_b = math.sqrt(sum(b * b for b in vec_b)) or 1.0
    return max(0.0, min(1.0, dot / (norm_a * norm_b)))
