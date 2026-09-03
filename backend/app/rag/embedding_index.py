"""
EmbeddingIndexManager — Persistent vector index for ShikshaSetu RAG.

Design:
- Embeddings are stored in MongoDB (document_chunks.embedding field) as float
  lists so they survive server restarts.
- A process-local numpy array is built lazily per material and cached in memory
  for fast cosine-similarity search without needing Atlas Vector Search.
- Each worker rebuilds its own in-memory index on first access (or at startup
  via load_all_ready_materials). This avoids the old `_vector_stores` dict being
  silently lost after a restart.
- Embedding vectors are NEVER SHA-256 hash placeholders. If the embedding API
  fails the chunk is left with embedding_status=PENDING and excluded from vector
  search. Keyword search still works for un-embedded chunks.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np
from pymongo.database import Database

from app.ai.models import DocumentChunk
from app.ai.repository import DocumentChunkRepository, LearningMaterialRepository

logger = logging.getLogger(__name__)


# ── Per-material numpy index ──────────────────────────────────────────────────

@dataclass
class MaterialIndex:
    """
    In-memory vector index for a single learning material.

    Attributes:
        material_id: The material this index belongs to.
        chunks:      All embedded chunks (in index order).
        matrix:      float32 numpy array of shape (N, dim) — pre-normalised rows.
        built_at:    Unix timestamp of last build (for freshness checks).
    """
    material_id: str
    chunks: List[DocumentChunk] = field(default_factory=list)
    matrix: Optional[np.ndarray] = None   # shape (N, dim), L2-normalised
    built_at: float = 0.0

    def search(
        self,
        query_vec: np.ndarray,
        top_k: int = 15,
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Cosine similarity search. query_vec must already be L2-normalised.

        Returns list of (chunk, score) sorted descending by score.
        """
        if self.matrix is None or len(self.chunks) == 0:
            return []

        scores = self.matrix @ query_vec          # shape (N,)
        top_k_clamped = min(top_k, len(self.chunks))
        top_idx = np.argpartition(scores, -top_k_clamped)[-top_k_clamped:]
        top_idx = top_idx[np.argsort(scores[top_idx])[::-1]]

        return [(self.chunks[i], float(scores[i])) for i in top_idx]


# ── Singleton manager ─────────────────────────────────────────────────────────

class EmbeddingIndexManager:
    """
    Process-singleton that manages per-material numpy indexes backed by MongoDB.

    Usage:
        manager = EmbeddingIndexManager.get_instance()
        manager.load_all_ready_materials(database)     # called once at startup
        results = manager.search(database, embedding_provider, material_id, query, top_k)
    """

    _instance: Optional["EmbeddingIndexManager"] = None

    def __init__(self) -> None:
        self._indexes: dict[str, MaterialIndex] = {}  # material_id → MaterialIndex

    @classmethod
    def get_instance(cls) -> "EmbeddingIndexManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── Startup loading ───────────────────────────────────────────────────────

    def load_all_ready_materials(self, database: Database) -> int:
        """
        Called once during app lifespan startup.
        Loads embeddings for all READY materials from MongoDB and builds numpy indexes.

        Returns the number of materials indexed.
        """
        try:
            materials = LearningMaterialRepository.get_by_status(database, "READY")
        except Exception as exc:
            logger.warning("Could not list READY materials at startup: %s", exc)
            return 0

        loaded = 0
        for mat in materials:
            try:
                self._build_index(database, mat.id)
                loaded += 1
            except Exception as exc:
                logger.warning("Failed to build index for material %s: %s", mat.id, exc)

        logger.info("EmbeddingIndexManager: loaded %d material indexes at startup", loaded)
        return loaded

    # ── Search ────────────────────────────────────────────────────────────────

    def search(
        self,
        database: Database,
        embedding_provider,
        query: str,
        top_k: int = 15,
        material_id: Optional[str] = None,
        competency_code: Optional[str] = None,
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Vector search across all indexed materials (or a specific one).

        Args:
            database:           MongoDB connection.
            embedding_provider: Provider with .embed_text() and .is_available().
            query:              Raw query string.
            top_k:              Maximum results to return.
            material_id:        Restrict search to one material (None = all).
            competency_code:    Post-filter by competency (None = no filter).

        Returns:
            List of (DocumentChunk, cosine_score) sorted descending.
        """
        if not embedding_provider.is_available():
            return []

        # Embed the query
        try:
            raw_vec = embedding_provider.embed_text(query)
        except Exception as exc:
            logger.warning("Query embedding failed, skipping vector search: %s", exc)
            return []

        q_vec = _normalise(np.array(raw_vec, dtype=np.float32))

        # Determine which materials to search
        if material_id:
            # Ensure index is loaded (lazy load)
            if material_id not in self._indexes:
                try:
                    self._build_index(database, material_id)
                except Exception as exc:
                    logger.warning("Could not build index for %s: %s", material_id, exc)
                    return []
            indexes_to_search = [self._indexes[material_id]] if material_id in self._indexes else []
        else:
            indexes_to_search = list(self._indexes.values())

        if not indexes_to_search:
            return []

        # Gather candidates from all target indexes
        all_candidates: List[Tuple[DocumentChunk, float]] = []
        for idx in indexes_to_search:
            all_candidates.extend(idx.search(q_vec, top_k=top_k))

        # Apply competency filter
        if competency_code:
            all_candidates = [
                (c, s) for c, s in all_candidates
                if c.competency_code is None or c.competency_code == competency_code
            ]

        # Re-sort after merging multiple indexes and return top_k
        all_candidates.sort(key=lambda x: x[1], reverse=True)
        return all_candidates[:top_k]

    # ── Index management ──────────────────────────────────────────────────────

    def invalidate(self, material_id: str) -> None:
        """Remove a material's index (call after re-embedding)."""
        self._indexes.pop(material_id, None)

    def rebuild(self, database: Database, material_id: str) -> bool:
        """Force-rebuild index for a material (after new embeddings are written)."""
        self.invalidate(material_id)
        try:
            self._build_index(database, material_id)
            return True
        except Exception as exc:
            logger.warning("rebuild failed for %s: %s", material_id, exc)
            return False

    # ── Internal ──────────────────────────────────────────────────────────────

    def _build_index(self, database: Database, material_id: str) -> MaterialIndex:
        """
        Load embedded chunks from MongoDB and build a MaterialIndex.
        Only chunks with embedding_status == EMBEDDED are included.
        """
        chunks = DocumentChunkRepository.get_chunks_with_embeddings(database, material_id)

        if not chunks:
            # No embedded chunks yet — create an empty placeholder
            idx = MaterialIndex(material_id=material_id, built_at=time.time())
            self._indexes[material_id] = idx
            return idx

        # Build normalised matrix
        vecs = []
        valid_chunks = []
        for chunk in chunks:
            if chunk.embedding and len(chunk.embedding) > 0:
                v = np.array(chunk.embedding, dtype=np.float32)
                norm = np.linalg.norm(v)
                if norm > 1e-9:
                    vecs.append(v / norm)
                    valid_chunks.append(chunk)

        matrix = np.stack(vecs, axis=0) if vecs else None  # shape (N, dim)

        idx = MaterialIndex(
            material_id=material_id,
            chunks=valid_chunks,
            matrix=matrix,
            built_at=time.time(),
        )
        self._indexes[material_id] = idx
        logger.debug(
            "Built index for material %s: %d vectors, dim=%d",
            material_id,
            len(valid_chunks),
            matrix.shape[1] if matrix is not None else 0,
        )
        return idx


# ── Embedding pipeline helpers ─────────────────────────────────────────────────

def embed_and_persist_chunks(
    database: Database,
    chunks: List[DocumentChunk],
    embedding_provider,
    model_name: str,
) -> Tuple[int, int]:
    """
    Embed a list of chunks using the provider and persist each vector to MongoDB.
    This replaces the old 'store in VectorStore in-memory only' approach.

    - On success: writes embedding + sets embedding_status=EMBEDDED.
    - On failure for a specific chunk: sets embedding_status=FAILED (no hash fallback).
    - Chunks without an ID are skipped with a warning.

    Returns:
        (embedded_count, failed_count)
    """
    embedded = 0
    failed = 0

    for chunk in chunks:
        if not chunk.id:
            logger.warning("Chunk has no ID, cannot persist embedding — skipping")
            failed += 1
            continue

        try:
            vec = embedding_provider.embed_text(chunk.text)
            # Validate it's a real float vector (not a hash placeholder)
            if not vec or len(vec) < 8:
                raise ValueError(f"Embedding too short: {len(vec) if vec else 0} dims")
            DocumentChunkRepository.update_embedding(database, chunk.id, vec, model_name)
            chunk.embedding = vec
            chunk.embedding_status = "EMBEDDED"
            embedded += 1
        except Exception as exc:
            logger.warning(
                "Embedding failed for chunk %s (seq %d): %s",
                chunk.id,
                chunk.sequence,
                exc,
            )
            DocumentChunkRepository.mark_embedding_failed(database, chunk.id)
            chunk.embedding_status = "FAILED"
            failed += 1

    return embedded, failed


# ── Utility ───────────────────────────────────────────────────────────────────

def _normalise(v: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(v)
    return v / norm if norm > 1e-9 else v
