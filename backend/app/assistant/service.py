"""Service orchestrator for the ShikshaSetu Capability Assistant."""

import logging
from typing import List, Dict, Any, Optional
from pymongo.database import Database

from app.core.config import Settings, get_settings
from app.ai.providers.gemini_provider import GeminiLLMProvider
from app.ai.providers.mock_provider import MockLLMProvider
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
    """Orchestrates capability context retrieval, RAG, and LLM inference."""

    def __init__(self, database: Database, settings: Optional[Settings] = None):
        self.db = database
        self.settings = settings or get_settings()
        self._llm_provider = self._init_llm()

    def _init_llm(self):
        provider_name = getattr(self.settings, "llm_provider", "gemini").lower()
        api_key = getattr(self.settings, "llm_api_key", "")
        model_name = getattr(self.settings, "llm_model", "models/gemini-3.6-flash")

        if provider_name == "gemini" and api_key:
            return GeminiLLMProvider(api_key=api_key, model=model_name)
        return MockLLMProvider()

    def _retrieve_curriculum_chunks(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Retrieves relevant text snippets from indexed learning materials or catalog."""
        chunks = []
        try:
            # Query learning materials / document chunks
            cursor = self.db.document_chunks.find(
                {"$text": {"$search": query}} if "text" in self.db.document_chunks.index_information()
                else {"text": {"$regex": query[:20], "$options": "i"}}
            ).limit(limit)
            for doc in cursor:
                chunks.append({
                    "source_id": doc.get("source_id", "CURRICULUM_DOC"),
                    "text": doc.get("text", "")[:400],
                })
        except Exception:
            pass

        # Also search indexed learning resources if empty
        if not chunks:
            try:
                words = query.strip().split()
                keyword = words[0] if words else "Statistical"
                res_cursor = self.db.learning_resources.find(
                    {"title": {"$regex": keyword, "$options": "i"}}
                ).limit(limit)
                for r in res_cursor:
                    chunks.append({
                        "source_id": r.get("source", {}).get("source_document", "SRC-01"),
                        "text": f"Course: {r.get('title')}. Provider: {r.get('provider')}. Target Competencies: {', '.join(r.get('competencies', []))}.",
                    })
            except Exception:
                pass

        return chunks

    def _generate_suggested_actions(
        self,
        user_message: str,
        context_data: Dict[str, Any],
    ) -> List[SuggestedAction]:
        """Generates dynamic, clickable navigation actions based on user intent."""
        actions = []
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

        # Default fallback action if none matched
        if not actions:
            actions.append(SuggestedAction(
                action_type="START_LEARNING",
                label="Browse Recommendations",
                target_page="Recommendations",
            ))
            actions.append(SuggestedAction(
                action_type="TAKE_ASSESSMENT",
                label="Validate Competency",
                target_page="Assessments",
            ))

        return actions

    def _extract_citations(
        self,
        context_data: Dict[str, Any],
        retrieved_chunks: List[Dict[str, Any]],
    ) -> List[AssistantSourceCitation]:
        """Collects verified sources from context and RAG chunks."""
        citations = []
        seen = set()

        # Add framework citation
        citations.append(AssistantSourceCitation(
            source_id="SRC-01",
            title="National Civil Services Competency Framework",
            source_type="COMPETENCY_FRAMEWORK",
            excerpt="Official 42-competency taxonomy across Statistical, Technical, Governance, and Behavioral domains.",
        ))
        seen.add("SRC-01")

        # Add recommended resource citations
        for rec in context_data.get("recommendations", [])[:2]:
            doc_id = rec.get("source_doc") or "iGOT-CATALOG"
            if doc_id not in seen:
                seen.add(doc_id)
                citations.append(AssistantSourceCitation(
                    source_id=doc_id,
                    title=f"{rec.get('provider')} — {rec.get('title')}",
                    source_type="IGOT_CATALOG" if rec.get("provider") == "IGOT" else "NSSTA_PROGRAMME",
                    url=rec.get("url"),
                    excerpt=f"Target: {rec.get('competency_code')} (Match Score: {rec.get('score')})",
                ))

        # Add chunk citations
        for c in retrieved_chunks:
            sid = c.get("source_id", "CURRICULUM")
            if sid not in seen:
                seen.add(sid)
                citations.append(AssistantSourceCitation(
                    source_id=sid,
                    title=f"Curriculum Document {sid}",
                    source_type="CURRICULUM_DOCUMENT",
                    excerpt=c.get("text", "")[:120] + "...",
                ))

        return citations

    def process_chat(
        self,
        user_id: str,
        request: AssistantChatRequest,
    ) -> AssistantChatResponse:
        """Processes a chat request with isolated context, RAG, and LLM inference."""
        context_data = build_user_capability_context(
            self.db,
            user_id,
            request.current_competency_code,
        )

        retrieved_chunks = self._retrieve_curriculum_chunks(request.message)

        prompt = build_copilot_user_prompt(
            user_message=request.message,
            context_data=context_data,
            retrieved_text_chunks=retrieved_chunks,
            context_page=request.context_page,
        )

        provider_name = "gemini"
        try:
            # Check if LLM provider supports generate_response or generate_content
            if hasattr(self._llm_provider, "generate_response"):
                answer = self._llm_provider.generate_response(
                    prompt=prompt,
                    system_prompt=CAPABILITY_COPILOT_SYSTEM_PROMPT,
                )
            elif hasattr(self._llm_provider, "generate"):
                answer = self._llm_provider.generate(
                    f"{CAPABILITY_COPILOT_SYSTEM_PROMPT}\n\n{prompt}"
                )
            else:
                answer = self._generate_deterministic_fallback(request.message, context_data)
                provider_name = "rule-based-fallback"
        except Exception as err:
            logger.warning("LLM inference failed, generating graceful capability fallback: %s", err)
            answer = self._generate_deterministic_fallback(request.message, context_data)
            provider_name = "capability-fallback"

        citations = self._extract_citations(context_data, retrieved_chunks)
        suggested_actions = self._generate_suggested_actions(request.message, context_data)

        return AssistantChatResponse(
            answer=answer,
            sources=citations,
            context_summary={
                "profile": context_data.get("profile"),
                "top_gap_count": len(context_data.get("top_gaps", [])),
                "supporting_evidence_count": context_data.get("supporting_evidence_count", 0),
                "authoritative_evidence_count": context_data.get("authoritative_evidence_count", 0),
            },
            suggested_actions=suggested_actions,
            model_provider=provider_name,
        )

    def _generate_deterministic_fallback(
        self,
        message: str,
        context_data: Dict[str, Any],
    ) -> str:
        """Deterministic capability fallback when LLM API is unavailable or rate-limited."""
        profile = context_data.get("profile", {})
        name = profile.get("full_name", "Officer")
        top_gaps = context_data.get("top_gaps", [])
        recs = context_data.get("recommendations", [])

        if top_gaps:
            gap_summary = "\n".join([
                f"- **{g.get('competency_name', g.get('competency_code'))}**: Current {g.get('current_level')}/5.0 vs Target {g.get('required_level')}/5.0 (Deficit: **{g.get('gap')}**, Priority: **{g.get('priority')}**)"
                for g in top_gaps[:3]
            ])
        else:
            gap_summary = "No critical capability deficits identified for your current role."

        rec_summary = ""
        if recs:
            rec_summary = "\n\n### 🎯 Recommended Interventions:\n" + "\n".join([
                f"- **{r.get('title')}** ({r.get('provider')}) — Target: `{r.get('competency_code')}` (Match Score: {r.get('score')})"
                for r in recs[:2]
            ])

        return (
            f"Hello **{name}**. Here is your current capability intelligence summary:\n\n"
            f"### 📊 Your Top Skill Gaps:\n{gap_summary}"
            f"{rec_summary}\n\n"
            f"> 💡 **Governance Notice**: Completing learning courses records **Supporting Evidence (0.30)** in your capability ledger. "
            f"Your formal competency rating will be updated upon completing an **Authoritative Capability Assessment (0.85)**."
        )
