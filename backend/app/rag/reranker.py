"""
MMR (Maximal Marginal Relevance) Reranker for ShikshaSetu RAG.

MMR selects a diverse, relevant subset from a larger candidate pool by
trading off between:
  - Relevance: similarity to the query
  - Diversity: dissimilarity to already-selected chunks

Formula (Carbonell & Goldstein, 1998):
  MMR = argmax_{{d in R\\S}} [ lam*sim(d, query) - (1-lam)*max_{{s in S}} sim(d, s) ]

where:
  R = candidate pool
  S = already-selected set
  lam = trade-off parameter (0=pure diversity, 1=pure relevance)
  sim = cosine similarity

Since some candidates may not have real embeddings (embedding_status != EMBEDDED),
the reranker has two modes:
  - SEMANTIC: uses real embedding vectors for sim() — preferred
  - LEXICAL: falls back to token-overlap Jaccard similarity when embeddings are
    unavailable — sufficient for diversity filtering even without vectors

The reranker always returns at most `top_k` chunks.  If the candidate pool is
smaller than top_k, all candidates are returned in their original order.
"""

from __future__ import annotations

import math
import re
from typing import List, Optional, Tuple

import numpy as np

from app.ai.models import DocumentChunk

# ── Public API ────────────────────────────────────────────────────────────────


def mmr_rerank(
    candidates: List[Tuple[DocumentChunk, float]],
    query: str,
    top_k: int = 6,
    mmr_lambda: float = 0.6,
    embedding_provider=None,
) -> List[Tuple[DocumentChunk, float]]:
    """
    Apply MMR to a list of (chunk, retrieval_score) candidates.

    Args:
        candidates:         Ranked list from hybrid retrieval (RRF scores).
        query:              Original user query (used for semantic mode).
        top_k:              Number of chunks to select.
        mmr_lambda:         λ — relevance vs diversity trade-off (default 0.6).
        embedding_provider: Optional provider for semantic similarity.
                            If None or unavailable, lexical fallback is used.

    Returns:
        Top-k (chunk, score) pairs selected by MMR, ordered by selection priority.
    """
    if not candidates:
        return []

    if len(candidates) <= top_k:
        return candidates

    # Attempt semantic MMR if embeddings are available
    if embedding_provider is not None and embedding_provider.is_available():
        try:
            return _mmr_semantic(candidates, query, top_k, mmr_lambda, embedding_provider)
        except Exception:
            pass  # fall through to lexical

    # Fallback: lexical MMR using token-overlap Jaccard
    return _mmr_lexical(candidates, top_k, mmr_lambda)


# ── Semantic MMR ──────────────────────────────────────────────────────────────

def _mmr_semantic(
    candidates: List[Tuple[DocumentChunk, float]],
    query: str,
    top_k: int,
    lam: float,
    embedding_provider,
) -> List[Tuple[DocumentChunk, float]]:
    """
    MMR using real embedding cosine similarities.

    Chunks without a real embedding (embedding_status != EMBEDDED) use
    their RRF relevance score as a proxy and a zero diversity penalty —
    they are treated as orthogonal to everything else.
    """
    n = len(candidates)

    # Gather embeddings: use stored vector if EMBEDDED, else None
    chunk_vecs: List[Optional[np.ndarray]] = []
    for chunk, _ in candidates:
        if chunk.embedding and chunk.embedding_status == "EMBEDDED":
            v = np.array(chunk.embedding, dtype=np.float32)
            norm = np.linalg.norm(v)
            chunk_vecs.append(v / norm if norm > 1e-9 else None)
        else:
            chunk_vecs.append(None)

    # Query vector
    q_raw = embedding_provider.embed_text(query)
    q_norm = np.array(q_raw, dtype=np.float32)
    qn = np.linalg.norm(q_norm)
    q_vec: Optional[np.ndarray] = q_norm / qn if qn > 1e-9 else None

    # Pre-compute query relevance scores
    rel_scores: List[float] = []
    for i, (_, rrf_score) in enumerate(candidates):
        if q_vec is not None and chunk_vecs[i] is not None:
            rel_scores.append(float(np.dot(q_vec, chunk_vecs[i])))
        else:
            rel_scores.append(rrf_score)  # use RRF score as proxy

    selected_indices: List[int] = []
    remaining = list(range(n))

    for _ in range(top_k):
        if not remaining:
            break

        best_idx = -1
        best_score = -math.inf

        for i in remaining:
            # Relevance component
            r = lam * rel_scores[i]

            # Diversity component — max similarity to any already-selected chunk
            if selected_indices:
                max_sim = 0.0
                for s in selected_indices:
                    if chunk_vecs[i] is not None and chunk_vecs[s] is not None:
                        sim = float(np.dot(chunk_vecs[i], chunk_vecs[s]))
                    else:
                        sim = 0.0  # treat as orthogonal
                    max_sim = max(max_sim, sim)
                d = (1.0 - lam) * max_sim
            else:
                d = 0.0

            mmr_score = r - d
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = i

        if best_idx >= 0:
            selected_indices.append(best_idx)
            remaining.remove(best_idx)

    return [candidates[i] for i in selected_indices]


# ── Lexical MMR (fallback) ────────────────────────────────────────────────────

def _mmr_lexical(
    candidates: List[Tuple[DocumentChunk, float]],
    top_k: int,
    lam: float,
) -> List[Tuple[DocumentChunk, float]]:
    """
    MMR using token-overlap Jaccard similarity as a diversity measure.

    rel(d) = normalised RRF rank score
    sim(d, s) = Jaccard(tokens(d), tokens(s))
    """
    n = len(candidates)

    # Normalise RRF scores to [0, 1]
    scores = [s for _, s in candidates]
    max_s = max(scores) if scores else 1.0
    rel = [s / max_s for s in scores]

    # Tokenise chunks once
    token_sets = [_tokenise(chunk.text) for chunk, _ in candidates]

    selected_indices: List[int] = []
    remaining = list(range(n))

    for _ in range(top_k):
        if not remaining:
            break

        best_idx = -1
        best_score = -math.inf

        for i in remaining:
            r = lam * rel[i]
            if selected_indices:
                max_sim = max(_jaccard(token_sets[i], token_sets[s]) for s in selected_indices)
                d = (1.0 - lam) * max_sim
            else:
                d = 0.0
            score = r - d
            if score > best_score:
                best_score = score
                best_idx = i

        if best_idx >= 0:
            selected_indices.append(best_idx)
            remaining.remove(best_idx)

    return [candidates[i] for i in selected_indices]


# ── Utility ───────────────────────────────────────────────────────────────────

def _tokenise(text: str) -> frozenset:
    """Split text into normalised tokens (len ≥ 3) for Jaccard overlap."""
    tokens = re.split(r"\W+", text.lower())
    return frozenset(t for t in tokens if len(t) >= 3)


def _jaccard(a: frozenset, b: frozenset) -> float:
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union > 0 else 0.0
