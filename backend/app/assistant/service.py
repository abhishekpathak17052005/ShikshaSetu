"""
ShikshaSetu Capability Assistant Service — P0 RAG upgrade.

Architecture (P0):
  User message
    → QueryIntentRouter (deterministic, no LLM)
    → OUT_OF_SCOPE  → immediate polite refusal
    → USER_DATA     → MongoDB context only  → LLM
    → RAG           → HybridRetrieval → MMR → LLM + groundedness
    → HYBRID        → MongoDB context + HybridRetrieval → MMR → LLM + groundedness
    → MCP           → MoSPI MCP (stub if not configured) → LLM

Public API is unchanged:
  AssistantService(database, settings).process_chat(user_id, request)
  → AssistantChatResponse

All schema types remain identical to pre-P0 (backward-compatible).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from pymongo.database import Database

from app.ai.models import DocumentChunk
from app.ai.providers.gemini_provider import GeminiLLMProvider
from app.ai.providers.mock_provider import MockLLMProvider
from app.core.config import Settings, get_settings
from app.rag.groundedness import (
    GroundednessResult,
    StructuredCitation,
    build_citations,
    insufficient_evidence_response,
    score_groundedness,
)
from app.rag.hybrid_retrieval import retrieve_for_chatbot
from app.rag.intent_router import QueryIntent, classify_intent
from app.rag.reranker import mmr_rerank
from .context import build_user_capability_context
from .prompts import CAPABILITY_COPILOT_SYSTEM_PROMPT, build_copilot_user_prompt
from .schemas import (
    AssistantChatRequest,
    AssistantChatResponse,
    AssistantSourceCitation,
    SuggestedAction,
)

logger = logging.getLogger(__name__)


class AssistantService:
    """
    Orchestrates query intent routing, hybrid retrieval, MMR reranking,
    user-context injection, LLM inference, and groundedness scoring.
    """

    def __init__(self, database: Database, settings: Optional[Settings] = None) -> None:
        self.db = database
        self.settings = settings or get_settings()
        self._llm_provider = self._init_llm()
        self._embedding_provider = self._init_embedding()

    # ── Provider initialisation ───────────────────────────────────────────────

    def _init_llm(self):
        provider = getattr(self.settings, "llm_provider", "gemini").lower()
        api_key  = getattr(self.settings, "llm_api_key", "")
        model    = getattr(self.settings, "llm_model", "gemini-3.5-flash-lite")
        if provider == "gemini" and api_key:
            return GeminiLLMProvider(api_key=api_key, model=model)
        return MockLLMProvider()

    def _init_embedding(self):
        """
        Initialise embedding provider for query embedding during retrieval.
        Uses embedding_api_key if set, falls back to llm_api_key.
        Returns None if no key is available (vector branch silently disabled).
        """
        provider = getattr(self.settings, "embedding_provider", "gemini").lower()
        api_key  = (
            getattr(self.settings, "embedding_api_key", "")
            or getattr(self.settings, "llm_api_key", "")
        )
        model    = getattr(self.settings, "embedding_model", "models/gemini-embedding-001")

        if provider == "gemini" and api_key:
            try:
                from app.ai.embeddings.gemini_provider import GeminiEmbeddingProvider
                return GeminiEmbeddingProvider(api_key=api_key, model=model)
            except Exception as exc:
                logger.warning("Embedding provider init failed: %s — vector branch disabled", exc)
                return None
        if provider == "mock":
            from app.ai.embeddings.mock_provider import MockEmbeddingProvider
            return MockEmbeddingProvider(dimension=getattr(self.settings, "embedding_dimension", 768))
        return None

    # ── Main entry point ──────────────────────────────────────────────────────

    def process_chat(
        self,
        user_id: str,
        request: AssistantChatRequest,
    ) -> AssistantChatResponse:
        """
        Process a chat request end-to-end.

        Returns an AssistantChatResponse with answer, structured citations,
        suggested actions, and context summary.  Schema is unchanged from pre-P0.
        """
        message = request.message

        # ── 1. Intent routing ─────────────────────────────────────────────────
        intent_result = classify_intent(message)
        logger.debug(
            "Intent: %s (confidence=%.2f) — %s",
            intent_result.intent, intent_result.confidence, intent_result.reason,
        )

        # ── 2. Immediate refusal for out-of-scope / injection ─────────────────
        if intent_result.refuse:
            refusal = (
                "I'm the Karmayogi AI Co-Pilot for ShikshaSetu, focused on your "
                "competency development. I'm not able to help with that request."
            )
            return AssistantChatResponse(
                answer=refusal,
                sources=[],
                context_summary={"intent": intent_result.intent.value, "refused": True},
                suggested_actions=self._generate_suggested_actions(message, {}),
                model_provider="rule-based-refusal",
            )

        # ── 3. User context (always fetched for personalisation) ─────────────
        context_data: Dict[str, Any] = {}
        if intent_result.use_user_data or intent_result.intent == QueryIntent.HYBRID:
            context_data = build_user_capability_context(
                self.db,
                user_id,
                request.current_competency_code,
            )

        # ── 4. Hybrid retrieval + MMR (for RAG and HYBRID paths) ──────────────
        reranked_chunks: List[Tuple[DocumentChunk, float]] = []
        if intent_result.use_rag:
            try:
                raw_candidates = retrieve_for_chatbot(
                    database=self.db,
                    query=message,
                    embedding_provider=self._embedding_provider,
                    top_k_keyword=self.settings.rag_top_k_keyword,
                    top_k_vector=self.settings.rag_top_k_vector,
                    competency_code=request.current_competency_code,
                )
                reranked_chunks = mmr_rerank(
                    candidates=raw_candidates,
                    query=message,
                    top_k=self.settings.rag_rerank_top_k,
                    mmr_lambda=self.settings.rag_mmr_lambda,
                    embedding_provider=self._embedding_provider,
                )
                logger.debug(
                    "RAG: %d raw candidates → %d after MMR",
                    len(raw_candidates), len(reranked_chunks),
                )
            except Exception as exc:
                logger.warning("Hybrid retrieval failed: %s", exc)

        # ── 5. Convert chunks to the legacy dict format for prompt builder ────
        # build_copilot_user_prompt expects List[Dict[str, str]] with keys
        # "source_id" and "text" — keep backward compatible.
        retrieved_text_chunks: List[Dict[str, Any]] = []
        for chunk, _ in reranked_chunks:
            source_id = str(chunk.id or chunk.material_id)
            # Add provenance metadata to the source_id string for prompt display
            label_parts = [source_id]
            if chunk.source_page:
                label_parts.append(f"p{chunk.source_page}")
            if chunk.source_section:
                label_parts.append(chunk.source_section[:40])
            retrieved_text_chunks.append({
                "source_id": " | ".join(label_parts),
                "text": (chunk.text or "")[:400],
            })

        # ── 6. Build prompt ───────────────────────────────────────────────────
        prompt = build_copilot_user_prompt(
            user_message=message,
            context_data=context_data,
            retrieved_text_chunks=retrieved_text_chunks,
            context_page=request.context_page,
        )

        # ── 7. LLM inference ──────────────────────────────────────────────────
        provider_name = "gemini"
        answer = ""
        try:
            if hasattr(self._llm_provider, "generate"):
                answer = self._llm_provider.generate(
                    f"{CAPABILITY_COPILOT_SYSTEM_PROMPT}\n\n{prompt}"
                )
            else:
                answer = self._generate_deterministic_fallback(message, context_data)
                provider_name = "rule-based-fallback"
        except Exception as exc:
            logger.warning("LLM inference failed: %s — using deterministic fallback", exc)
            answer = self._generate_deterministic_fallback(message, context_data)
            provider_name = "capability-fallback"

        # ── 8. Groundedness check (RAG / HYBRID paths only) ───────────────────
        if intent_result.use_rag and reranked_chunks:
            gnd: GroundednessResult = score_groundedness(
                answer=answer,
                retrieved_chunks=reranked_chunks,
                threshold=self.settings.rag_groundedness_threshold,
            )
            logger.debug(
                "Groundedness: %.3f (%d/%d tokens matched) — grounded=%s",
                gnd.score, gnd.matched_tokens, gnd.answer_tokens, gnd.is_grounded,
            )
            if not gnd.is_grounded:
                answer = insufficient_evidence_response(message)
                provider_name = "groundedness-fallback"
        else:
            gnd = None

        # ── 9. Build structured citations ─────────────────────────────────────
        structured_citations = build_citations(reranked_chunks, max_citations=5)
        # Also weave in recommendation sources for HYBRID / USER_DATA paths
        for rec in context_data.get("recommendations", [])[:2]:
            doc_id = rec.get("source_doc") or "iGOT-CATALOG"
            if not any(c.source_id == doc_id for c in structured_citations):
                structured_citations.append(StructuredCitation(
                    source_id=doc_id,
                    title=f"{rec.get('provider', 'iGOT')} — {rec.get('title', 'Course')}",
                    source_type=(
                        "IGOT_COURSE" if (rec.get("provider") or "").upper() == "IGOT"
                        else "NSSTA_PROGRAMME"
                    ),
                    url=rec.get("url"),
                    excerpt=f"Target: {rec.get('competency_code')} (Score: {rec.get('score')})",
                ))

        # Convert to legacy AssistantSourceCitation schema (unchanged)
        api_citations = [
            AssistantSourceCitation(
                source_id=c.source_id,
                title=c.title,
                source_type=c.source_type,
                url=c.url,
                excerpt=c.excerpt,
            )
            for c in structured_citations
        ]

        # ── 10. Suggested actions ─────────────────────────────────────────────
        suggested_actions = self._generate_suggested_actions(message, context_data)

        # ── 11. Context summary ───────────────────────────────────────────────
        context_summary: Dict[str, Any] = {
            "intent": intent_result.intent.value,
            "profile": context_data.get("profile"),
            "top_gap_count": len(context_data.get("top_gaps", [])),
            "supporting_evidence_count": context_data.get("supporting_evidence_count", 0),
            "authoritative_evidence_count": context_data.get("authoritative_evidence_count", 0),
            "rag_chunks_used": len(reranked_chunks),
        }
        if gnd is not None:
            context_summary["groundedness_score"] = gnd.score
            context_summary["groundedness_passed"] = gnd.is_grounded

        return AssistantChatResponse(
            answer=answer,
            sources=api_citations,
            context_summary=context_summary,
            suggested_actions=suggested_actions,
            model_provider=provider_name,
        )

    # ── Suggested actions ─────────────────────────────────────────────────────

    def _generate_suggested_actions(
        self,
        user_message: str,
        context_data: Dict[str, Any],
    ) -> List[SuggestedAction]:
        actions: List[SuggestedAction] = []
        msg_lower = user_message.lower()

        if any(w in msg_lower for w in ["gap", "deficit", "weakness", "improve", "priority"]):
            actions.append(SuggestedAction(
                action_type="VIEW_GAP",
                label="View My Skill Gaps",
                target_page="Skill Gaps",
            ))
        if any(w in msg_lower for w in ["course", "recommend", "learn", "igot", "nssta", "training"]):
            actions.append(SuggestedAction(
                action_type="START_LEARNING",
                label="Browse Recommended Courses",
                target_page="Recommendations",
            ))
        if any(w in msg_lower for w in ["quiz", "assess", "test", "exam", "validate", "competency"]):
            actions.append(SuggestedAction(
                action_type="TAKE_ASSESSMENT",
                label="Take Capability Quiz",
                target_page="Quizzes",
            ))
        if any(w in msg_lower for w in ["evidence", "proof", "score", "record"]):
            actions.append(SuggestedAction(
                action_type="NAVIGATE",
                label="Check Evidence Ledger",
                target_page="Evidence Ledger",
            ))
        if not actions:
            actions.extend([
                SuggestedAction(
                    action_type="START_LEARNING",
                    label="Browse Recommendations",
                    target_page="Recommendations",
                ),
                SuggestedAction(
                    action_type="TAKE_ASSESSMENT",
                    label="Validate Competency",
                    target_page="Assessments",
                ),
            ])
        return actions

    # ── Deterministic fallback ────────────────────────────────────────────────

    def _generate_deterministic_fallback(
        self,
        message: str,
        context_data: Dict[str, Any],
    ) -> str:
        """Used when LLM API is unavailable. Builds a structured capability summary."""
        profile   = context_data.get("profile", {})
        name      = profile.get("full_name", "Officer")
        top_gaps  = context_data.get("top_gaps", [])
        recs      = context_data.get("recommendations", [])

        gap_summary = "\n".join([
            f"- **{g.get('competency_name', g.get('competency_code'))}**: "
            f"Current {g.get('current_level')}/5.0 vs Target {g.get('required_level')}/5.0 "
            f"(Deficit: **{g.get('gap')}**, Priority: **{g.get('priority')}**)"
            for g in top_gaps[:3]
        ]) or "No critical capability deficits identified for your current role."

        rec_summary = ""
        if recs:
            rec_summary = "\n\n### 🎯 Recommended Interventions:\n" + "\n".join([
                f"- **{r.get('title')}** ({r.get('provider')}) — "
                f"Target: `{r.get('competency_code')}` (Match Score: {r.get('score')})"
                for r in recs[:2]
            ])

        return (
            f"Hello **{name}**. Here is your current capability intelligence summary:\n\n"
            f"### 📊 Your Top Skill Gaps:\n{gap_summary}"
            f"{rec_summary}\n\n"
            "> 💡 **Governance Notice**: Completing learning courses records "
            "**Supporting Evidence (0.30)** in your capability ledger. "
            "Your formal competency rating will be updated upon completing an "
            "**Authoritative Capability Assessment (0.85)**."
        )
