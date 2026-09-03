"""
Groundedness scoring and structured citation builder for ShikshaSetu RAG.

Groundedness
------------
A simple, fast, lexical groundedness score is computed by measuring how much
of the LLM answer is "anchored" in the retrieved source chunks:

  groundedness = |answer_tokens ∩ source_tokens| / |answer_tokens|

Tokens shorter than 3 characters are excluded (stop words, articles).
The score is in [0.0, 1.0].  0.0 means no words from the answer appear in the
retrieved chunks; 1.0 means every meaningful answer word is present in sources.

Threshold behaviour (RAG_GROUNDEDNESS_THRESHOLD, default 0.25):
  - score >= threshold → return the answer as-is
  - score < threshold  → replace the answer with a transparent "insufficient
    evidence" stub that tells the user to consult official sources.

This is intentionally conservative: we prefer a helpful "I don't have enough
indexed material" message over a hallucinated confident answer.

Structured Citations
--------------------
Citations are built from the reranked chunks (not just from whatever the LLM
mentioned).  Each citation carries:
  - source_id:    chunk._id (or material_id for learning resources)
  - title:        section title or material original filename
  - source_type:  CURRICULUM_DOCUMENT | IGOT_COURSE | NSSTA_PROGRAMME | COMPETENCY_FRAMEWORK
  - page / slide: when available
  - section:      when available
  - url:          when available (learning resources)
  - excerpt:      first 120 characters of the chunk

The frontend can render these as "Source: Sampling Methods — Page 14".
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from app.ai.models import DocumentChunk

# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class StructuredCitation:
    """A fully structured source reference returned alongside an answer."""
    source_id: str
    title: str
    source_type: str               # CURRICULUM_DOCUMENT | IGOT_COURSE | NSSTA_PROGRAMME | COMPETENCY_FRAMEWORK
    page: Optional[int] = None
    slide: Optional[int] = None
    section: Optional[str] = None
    url: Optional[str] = None
    excerpt: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def display_label(self) -> str:
        """Human-readable label for frontend rendering."""
        parts = [self.title]
        if self.page:
            parts.append(f"Page {self.page}")
        if self.slide:
            parts.append(f"Slide {self.slide}")
        if self.section:
            parts.append(self.section)
        return " — ".join(parts)


@dataclass
class GroundednessResult:
    """Output of groundedness analysis for one LLM answer."""
    score: float                                # [0.0, 1.0]
    is_grounded: bool                           # score >= threshold
    answer_tokens: int                          # content words in answer
    matched_tokens: int                         # answer tokens found in sources
    threshold_used: float
    citations: List[StructuredCitation] = field(default_factory=list)


# ── Groundedness scorer ───────────────────────────────────────────────────────

def score_groundedness(
    answer: str,
    retrieved_chunks: List[Tuple[DocumentChunk, float]],
    threshold: float = 0.25,
) -> GroundednessResult:
    """
    Compute groundedness score for an LLM answer against retrieved chunks.

    Args:
        answer:           LLM-generated answer text.
        retrieved_chunks: List of (chunk, score) from MMR reranker.
        threshold:        Minimum score to consider the answer grounded.

    Returns:
        GroundednessResult with score, grounded flag, and citations.
    """
    # Build source token set from all retrieved chunks
    source_text = " ".join(c.text for c, _ in retrieved_chunks)
    source_tokens = _content_tokens(source_text)

    # Build answer token set
    answer_tokens = _content_tokens(answer)

    if not answer_tokens:
        # Empty answer is vacuously grounded (won't be shown anyway)
        return GroundednessResult(
            score=1.0,
            is_grounded=True,
            answer_tokens=0,
            matched_tokens=0,
            threshold_used=threshold,
            citations=build_citations(retrieved_chunks),
        )

    matched = answer_tokens & source_tokens
    score = len(matched) / len(answer_tokens)

    citations = build_citations(retrieved_chunks)

    return GroundednessResult(
        score=round(score, 4),
        is_grounded=score >= threshold,
        answer_tokens=len(answer_tokens),
        matched_tokens=len(matched),
        threshold_used=threshold,
        citations=citations,
    )


def insufficient_evidence_response(query: str) -> str:
    """
    Standard stub returned when groundedness is below threshold.
    Transparent, factual, and guides the user to official sources.
    """
    return (
        "The indexed curriculum materials do not contain enough reliable "
        "information to answer this question confidently.\n\n"
        "Please refer to:\n"
        "- The official **iGOT Karmayogi portal** (igotkarmayogi.gov.in)\n"
        "- **NSSTA** training calendar (nssta.nic.in)\n"
        "- Official **MoSPI** publications (mospi.gov.in)\n"
        "- The **National Civil Services Competency Framework** documentation\n\n"
        "If you have uploaded relevant training materials, try running a "
        "Capability Assessment first to generate more indexed content."
    )


# ── Citation builder ──────────────────────────────────────────────────────────

def build_citations(
    retrieved_chunks: List[Tuple[DocumentChunk, float]],
    max_citations: int = 5,
) -> List[StructuredCitation]:
    """
    Build structured citations from reranked chunks.

    Always includes the National Competency Framework as a base citation.
    Adds per-chunk citations for the top-max_citations chunks.
    Deduplicates by source_id.
    """
    citations: List[StructuredCitation] = []
    seen: set = set()

    # Static framework citation — always present
    fw_id = "SRC-01"
    citations.append(StructuredCitation(
        source_id=fw_id,
        title="National Civil Services Competency Framework",
        source_type="COMPETENCY_FRAMEWORK",
        excerpt=(
            "42-competency taxonomy across Statistical, Technical, "
            "Governance, and Behavioral domains."
        ),
    ))
    seen.add(fw_id)

    for chunk, _ in retrieved_chunks[:max_citations]:
        cid = str(chunk.id or chunk.material_id)
        if cid in seen:
            continue
        seen.add(cid)

        # Determine source type
        if chunk.document_type:
            source_type = chunk.document_type
        elif chunk.material_id.startswith("learning_resource:"):
            source_type = "IGOT_COURSE"
        else:
            source_type = "CURRICULUM_DOCUMENT"

        # Build a readable title
        if chunk.source_section:
            title = chunk.source_section
        elif chunk.material_id.startswith("learning_resource:"):
            # Text is "Course: <title>. Provider: ..." — extract title
            m = re.match(r"Course:\s*([^.]+)", chunk.text or "")
            title = m.group(1).strip() if m else "Learning Resource"
        else:
            title = f"Curriculum Document — Chunk {chunk.sequence}"

        # Extract URL if this is a learning resource synthetic chunk
        url: Optional[str] = None
        if chunk.material_id.startswith("learning_resource:"):
            # The URL is not in the chunk text; mark as None (frontend fetches separately)
            url = None

        excerpt = (chunk.text or "")[:120]
        if len(chunk.text or "") > 120:
            excerpt += "…"

        citations.append(StructuredCitation(
            source_id=cid,
            title=title,
            source_type=source_type,
            page=chunk.source_page,
            slide=chunk.source_slide,
            section=chunk.source_section,
            url=url,
            excerpt=excerpt,
        ))

    return citations


# ── Utility ───────────────────────────────────────────────────────────────────

def _content_tokens(text: str) -> frozenset:
    """
    Normalise and tokenise text, keeping only words of length >= 3.
    Strips markdown formatting before tokenising.
    """
    # Strip markdown syntax
    text = re.sub(r"\*\*|\*|__|\[.*?\]\(.*?\)|`+", " ", text)
    tokens = re.split(r"\W+", text.lower())
    return frozenset(t for t in tokens if len(t) >= 3)
