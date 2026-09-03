"""
Hybrid Retrieval with Reciprocal Rank Fusion (RRF) for ShikshaSetu.

Architecture
------------
Two parallel retrieval branches are executed:

  1. KEYWORD BRANCH — MongoDB $text search on document_chunks + title/description
     regex search on learning_resources.  Requires the text index created in
     framework_indexes.py.  Degrades gracefully to regex on 'text' field if the
     text index is not yet ready.

  2. VECTOR BRANCH — cosine similarity via EmbeddingIndexManager (in-memory numpy
     index backed by MongoDB-persisted embeddings).  Skipped if no embedding
     provider is available or if no embedded chunks exist yet.

Results from both branches are merged using Reciprocal Rank Fusion (RRF):

    rrf_score(d) = Σ  1 / (k + rank_in_list_i)
                   i

where k=60 (standard RRF constant).  This avoids the need to normalise scores
from heterogeneous retrieval systems.

The merged list is returned as a flat list of (DocumentChunk, rrf_score) tuples
sorted descending for downstream MMR reranking.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from pymongo.database import Database

from app.ai.models import DocumentChunk

logger = logging.getLogger(__name__)

# RRF rank-smoothing constant (60 is the standard choice from the original paper)
_RRF_K: int = 60

# ── Public API ────────────────────────────────────────────────────────────────


def hybrid_retrieve(
    database: Database,
    query: str,
    embedding_provider,
    top_k_keyword: int = 15,
    top_k_vector: int = 15,
    material_id: Optional[str] = None,
    competency_code: Optional[str] = None,
) -> List[Tuple[DocumentChunk, float]]:
    """
    Execute keyword + vector retrieval and merge results with RRF.

    Args:
        database:           MongoDB connection.
        query:              Raw user query string.
        embedding_provider: Provider with .embed_text() and .is_available().
                            If None or unavailable, only keyword retrieval runs.
        top_k_keyword:      Max candidates from keyword branch.
        top_k_vector:       Max candidates from vector branch.
        material_id:        Optional — restrict search to one material.
        competency_code:    Optional — metadata filter applied to both branches.

    Returns:
        RRF-merged list of (DocumentChunk, rrf_score) sorted descending.
        Returns empty list on total failure (never raises).
    """
    keyword_results: List[DocumentChunk] = []
    vector_results: List[Tuple[DocumentChunk, float]] = []

    # ── Keyword branch ────────────────────────────────────────────────────────
    try:
        keyword_results = _keyword_search(
            database=database,
            query=query,
            limit=top_k_keyword,
            material_id=material_id,
            competency_code=competency_code,
        )
        logger.debug("Keyword branch: %d candidates", len(keyword_results))
    except Exception as exc:
        logger.warning("Keyword retrieval failed: %s", exc)

    # ── Vector branch ─────────────────────────────────────────────────────────
    try:
        if embedding_provider is not None and embedding_provider.is_available():
            from app.rag.embedding_index import EmbeddingIndexManager
            vector_results = EmbeddingIndexManager.get_instance().search(
                database=database,
                embedding_provider=embedding_provider,
                query=query,
                top_k=top_k_vector,
                material_id=material_id,
                competency_code=competency_code,
            )
            logger.debug("Vector branch: %d candidates", len(vector_results))
        else:
            logger.debug("Vector branch skipped: embedding provider unavailable")
    except Exception as exc:
        logger.warning("Vector retrieval failed: %s", exc)

    # ── Merge with RRF ────────────────────────────────────────────────────────
    merged = _reciprocal_rank_fusion(
        keyword_list=keyword_results,
        vector_list=[chunk for chunk, _ in vector_results],
        k=_RRF_K,
    )

    return merged


def retrieve_for_chatbot(
    database: Database,
    query: str,
    embedding_provider,
    top_k_keyword: int = 15,
    top_k_vector: int = 15,
    competency_code: Optional[str] = None,
) -> List[Tuple[DocumentChunk, float]]:
    """
    Chatbot-specific retrieval: searches across ALL materials and also
    searches learning_resources for course-level context.

    Returns merged list enriched with learning resource chunks (as synthetic
    DocumentChunk objects from resource metadata).
    """
    # Document chunks from hybrid search
    chunk_results = hybrid_retrieve(
        database=database,
        query=query,
        embedding_provider=embedding_provider,
        top_k_keyword=top_k_keyword,
        top_k_vector=top_k_vector,
        competency_code=competency_code,
    )

    # Augment with learning_resource metadata (course titles, providers, competencies)
    resource_chunks = _learning_resource_search(database, query, limit=6, competency_code=competency_code)
    resource_scores = [(rc, 0.4) for rc in resource_chunks]  # fixed relevance weight

    # Merge: chunk results first (they have real content), resource chunks appended
    seen_ids = {str(c.id) for c, _ in chunk_results}
    for rc, score in resource_scores:
        if str(rc.id) not in seen_ids:
            chunk_results.append((rc, score))
            seen_ids.add(str(rc.id))

    return chunk_results


# ── Keyword retrieval ─────────────────────────────────────────────────────────

def _keyword_search(
    database: Database,
    query: str,
    limit: int,
    material_id: Optional[str],
    competency_code: Optional[str],
) -> List[DocumentChunk]:
    """
    MongoDB text search on document_chunks.
    Falls back to case-insensitive substring match on 'text' field if the text
    index doesn't exist yet (avoids the old single-word-prefix regex problem).
    """
    collection = database["document_chunks"]

    # Build base filter
    base_filter: Dict[str, Any] = {}
    if material_id:
        base_filter["material_id"] = material_id
    if competency_code:
        base_filter["competency_code"] = competency_code

    # Attempt $text search (requires text index created by framework_indexes)
    try:
        text_filter = {**base_filter, "$text": {"$search": query}}
        cursor = collection.find(
            text_filter,
            {"score": {"$meta": "textScore"}},
        ).sort([("score", {"$meta": "textScore"})]).limit(limit)
        chunks = _cursor_to_chunks(cursor)
        if chunks:
            return chunks
        # Text search returned nothing — fall through to regex
    except Exception:
        pass  # Text index not ready — fall through

    # Fallback: multi-word regex on the 'text' field
    # Build a regex that requires ALL words (min 3 chars) to be present
    words = [w for w in re.split(r"\W+", query.lower()) if len(w) >= 3]
    if not words:
        return []

    # Require each word to appear in the text
    word_filters = [{"text": {"$regex": w, "$options": "i"}} for w in words[:5]]
    regex_filter = {**base_filter, "$and": word_filters} if word_filters else base_filter

    try:
        cursor = collection.find(regex_filter).limit(limit)
        return _cursor_to_chunks(cursor)
    except Exception as exc:
        logger.warning("Keyword fallback regex failed: %s", exc)
        return []


def _learning_resource_search(
    database: Database,
    query: str,
    limit: int,
    competency_code: Optional[str],
) -> List[DocumentChunk]:
    """
    Search learning_resources collection for course-level context.
    Returns synthetic DocumentChunk objects built from resource metadata.
    """
    words = [w for w in re.split(r"\W+", query.lower()) if len(w) >= 3]
    if not words:
        return []

    search_filter: Dict[str, Any] = {}
    if competency_code:
        search_filter["competencies"] = competency_code
    else:
        keyword = words[0]
        search_filter["$or"] = [
            {"title": {"$regex": keyword, "$options": "i"}},
            {"description": {"$regex": keyword, "$options": "i"}},
        ]

    try:
        cursor = database["learning_resources"].find(search_filter).limit(limit)
        chunks: List[DocumentChunk] = []
        for r in cursor:
            resource_id = str(r.get("_id", ""))
            title = r.get("title", "")
            provider = r.get("provider", "")
            comps = ", ".join(r.get("competencies", []))
            description = r.get("description", "") or r.get("overview", "")
            text = (
                f"Course: {title}. Provider: {provider}. "
                f"Target Competencies: {comps}. "
                f"{description[:300] if description else ''}"
            ).strip()
            source_doc = r.get("source", {}).get("source_document", "SRC-01") if isinstance(r.get("source"), dict) else "SRC-01"
            chunk = DocumentChunk(
                material_id=f"learning_resource:{resource_id}",
                sequence=0,
                text=text,
                source_section=f"Learning Resource — {provider}",
                competency_code=comps or None,
                document_type="IGOT_COURSE" if "igot" in provider.lower() else "NSSTA_PROGRAMME",
                embedding_status="PENDING",  # not embedded — keyword only
            )
            chunk.id = f"lr:{resource_id}"
            chunks.append(chunk)
        return chunks
    except Exception as exc:
        logger.warning("Learning resource search failed: %s", exc)
        return []


# ── Reciprocal Rank Fusion ────────────────────────────────────────────────────

def _reciprocal_rank_fusion(
    keyword_list: List[DocumentChunk],
    vector_list: List[DocumentChunk],
    k: int = 60,
) -> List[Tuple[DocumentChunk, float]]:
    """
    Merge two ranked lists using Reciprocal Rank Fusion.

    Each document's fused score is the sum of 1/(k + rank) across every list
    it appears in.  Documents not in a list get no contribution from that list.

    Deduplication is by chunk_id (str(chunk.id)).

    Returns:
        List of (DocumentChunk, rrf_score) sorted descending.
    """
    scores: Dict[str, float] = {}
    chunks_by_id: Dict[str, DocumentChunk] = {}

    for rank, chunk in enumerate(keyword_list, start=1):
        cid = str(chunk.id or f"kw_{rank}")
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
        if cid not in chunks_by_id:
            chunks_by_id[cid] = chunk

    for rank, chunk in enumerate(vector_list, start=1):
        cid = str(chunk.id or f"vec_{rank}")
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
        if cid not in chunks_by_id:
            chunks_by_id[cid] = chunk

    sorted_ids = sorted(scores, key=lambda cid: scores[cid], reverse=True)
    return [(chunks_by_id[cid], scores[cid]) for cid in sorted_ids]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _cursor_to_chunks(cursor) -> List[DocumentChunk]:
    chunks: List[DocumentChunk] = []
    for doc in cursor:
        try:
            doc["_id"] = str(doc["_id"])
            doc["id"] = doc["_id"]
            doc.pop("score", None)          # remove textScore meta field
            chunks.append(DocumentChunk(**doc))
        except Exception:
            pass  # skip malformed documents
    return chunks
