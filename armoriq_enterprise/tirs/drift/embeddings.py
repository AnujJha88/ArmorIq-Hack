"""
Intent Embedding Engine
=======================
Semantic embeddings for intent analysis using sentence-transformers.
"""

import numpy as np
import logging
from typing import List, Optional
from dataclasses import dataclass
import hashlib

logger = logging.getLogger("TIRS.Embeddings")

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available, using fallback embeddings")


@dataclass
class EmbeddingConfig:
    """Configuration for embedding engine."""
    model_name: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384
    normalize: bool = True
    cache_size: int = 1000


class EmbeddingEngine:
    """
    Intent embedding engine using sentence-transformers.

    Falls back to hash-based embeddings if transformers unavailable.
    """

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
        self.model = None
        self._cache = {}

        if TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer(self.config.model_name)
                logger.info(f"Loaded embedding model: {self.config.model_name}")
            except Exception as e:
                logger.warning(f"Failed to load model: {e}")

        if not self.model:
            logger.info("Using fallback hash-based embeddings")

    def embed(self, text: str) -> np.ndarray:
        """
        Generate embedding for text.

        Args:
            text: Input text to embed

        Returns:
            Normalized embedding vector
        """
        # Check cache
        cache_key = hashlib.md5(text.encode()).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]

        if self.model:
            embedding = self.model.encode(text, convert_to_numpy=True)
        else:
            embedding = self._fallback_embed(text)

        # Normalize
        if self.config.normalize:
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm

        # Cache
        if len(self._cache) < self.config.cache_size:
            self._cache[cache_key] = embedding

        return embedding

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Embed multiple texts at once."""
        if self.model:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            if self.config.normalize:
                norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                norms[norms == 0] = 1
                embeddings = embeddings / norms
            return embeddings
        else:
            return np.array([self.embed(t) for t in texts])

    def _fallback_embed(self, text: str) -> np.ndarray:
        """
        Fallback embedding using deterministic hash.

        Creates a pseudo-random but deterministic embedding
        based on the text hash.
        """
        # Create deterministic seed from text
        text_hash = hashlib.sha256(text.encode()).digest()
        seed = int.from_bytes(text_hash[:4], 'big')
        rng = np.random.RandomState(seed)

        # Generate embedding
        embedding = rng.randn(self.config.embedding_dim).astype(np.float32)

        # Incorporate word-level features
        words = text.lower().split()
        for i, word in enumerate(words[:self.config.embedding_dim]):
            word_hash = hashlib.md5(word.encode()).digest()
            idx = int.from_bytes(word_hash[:2], 'big') % self.config.embedding_dim
            embedding[idx] += 0.5 * (1 if i % 2 == 0 else -1)

        return embedding

    def similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        return float(np.dot(vec1, vec2))

    def distance(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine distance (1 - similarity)."""
        return 1.0 - self.similarity(vec1, vec2)


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot / (norm1 * norm2))


# Singleton
_embedding_engine: Optional[EmbeddingEngine] = None


def get_embedding_engine() -> EmbeddingEngine:
    """Get singleton embedding engine."""
    global _embedding_engine
    if _embedding_engine is None:
        _embedding_engine = EmbeddingEngine()
    return _embedding_engine
