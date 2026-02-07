"""
Intent Embedding Generation
===========================
Converts intent text to vector embeddings for drift detection.

Supports:
- sentence-transformers (if installed)
- Simple hash-based mock (fallback for demo)
"""

import hashlib
import numpy as np
from typing import List, Optional
import logging

logger = logging.getLogger("TIRS.Embeddings")

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
    logger.info("sentence-transformers available")
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.info("sentence-transformers not installed, using hash-based embeddings")


class EmbeddingEngine:
    """
    Generate embeddings for intent text.

    Uses sentence-transformers if available, otherwise falls back
    to a deterministic hash-based approach for demos.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", dimension: int = 384):
        self.dimension = dimension
        self.model = None
        self.use_transformers = False

        if TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer(model_name)
                self.use_transformers = True
                self.dimension = self.model.get_sentence_embedding_dimension()
                logger.info(f"Loaded model: {model_name} (dim={self.dimension})")
            except Exception as e:
                logger.warning(f"Failed to load transformer model: {e}")
                logger.info("Falling back to hash-based embeddings")

    def embed(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.

        Args:
            text: Intent text to embed

        Returns:
            Normalized embedding vector
        """
        if self.use_transformers and self.model:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return self._normalize(embedding)
        else:
            return self._hash_embed(text)

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of intent texts

        Returns:
            Array of normalized embeddings (N x dimension)
        """
        if self.use_transformers and self.model:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return np.array([self._normalize(e) for e in embeddings])
        else:
            return np.array([self._hash_embed(t) for t in texts])

    def _hash_embed(self, text: str) -> np.ndarray:
        """
        Generate deterministic embedding from text hash.

        This is a fallback for demos when transformers aren't available.
        It produces consistent embeddings that preserve some semantic
        properties (similar text -> similar hash).
        """
        # Create multiple hashes with different seeds for dimensionality
        embedding = np.zeros(self.dimension)

        # Use word-level hashing for some semantic preservation
        words = text.lower().split()

        for i in range(self.dimension):
            # Combine text hash with position
            seed = f"{text}_{i}"
            hash_val = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
            # Map to [-1, 1]
            embedding[i] = (hash_val % 10000) / 5000 - 1

            # Add word-level contributions
            for word in words:
                word_hash = int(hashlib.md5(f"{word}_{i}".encode()).hexdigest(), 16)
                embedding[i] += ((word_hash % 1000) / 500 - 1) * 0.1

        return self._normalize(embedding)

    def _normalize(self, v: np.ndarray) -> np.ndarray:
        """Normalize vector to unit length."""
        norm = np.linalg.norm(v)
        if norm > 0:
            return v / norm
        return v

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings."""
        return float(np.dot(a, b))


# Singleton instance
_embedding_engine: Optional[EmbeddingEngine] = None


def get_embedding_engine() -> EmbeddingEngine:
    """Get the singleton embedding engine."""
    global _embedding_engine
    if _embedding_engine is None:
        _embedding_engine = EmbeddingEngine()
    return _embedding_engine


def embed_intent(text: str) -> np.ndarray:
    """Convenience function to embed a single intent."""
    return get_embedding_engine().embed(text)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Convenience function for cosine similarity."""
    return get_embedding_engine().cosine_similarity(a, b)
