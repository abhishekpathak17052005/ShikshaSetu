"""
Query Intent Router for ShikshaSetu Karmayogi AI Co-Pilot.

Classifies each incoming user message into one of five intent categories so the
downstream retrieval and generation layers use only the data sources that are
actually needed for that question type.

Categories
----------
USER_DATA     – Answer requires only the requesting user's structured data
                (skill gaps, competency scores, recommendations, evidence, profile).
                No RAG retrieval needed; MongoDB context is sufficient.

RAG           – Answer requires curriculum or learning material knowledge.
                Full hybrid retrieval over document_chunks and learning_resources.

MCP           – Answer requires live official statistics (MoSPI data, PLFS, CPI,
                NSS, NAS indicators). Route to MoSPI MCP if configured.

HYBRID        – Answer requires BOTH the user's structured data AND curriculum
                knowledge (e.g. "Why was this SQL course recommended?" needs the
                user's SQL gap AND course content).

OUT_OF_SCOPE  – Question is completely unrelated to ShikshaSetu, competency
                development, official statistics, or civil services training.
                Return a polite refusal immediately without calling the LLM.

Design principles
-----------------
- Fully deterministic: keyword/pattern matching, no LLM call, no API dependency.
- O(1) with respect to database size.
- Conservative: when uncertain, prefer HYBRID over USER_DATA (retrieval is cheap;
  wrong context is expensive).
- All pattern sets are uppercase-normalised for case-insensitive matching.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet

# ── Intent enum ───────────────────────────────────────────────────────────────

class QueryIntent(str, Enum):
    USER_DATA    = "USER_DATA"
    RAG          = "RAG"
    MCP          = "MCP"
    HYBRID       = "HYBRID"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class IntentResult:
    intent: QueryIntent
    confidence: float          # 0.0–1.0 heuristic (informational only)
    reason: str                # human-readable explanation for logging
    use_rag: bool
    use_user_data: bool
    use_mcp: bool
    refuse: bool               # True → return polite refusal immediately


# ── Keyword sets ──────────────────────────────────────────────────────────────

# Questions clearly about the user's own data
_USER_DATA_SIGNALS: FrozenSet[str] = frozenset({
    "my gap", "my skill", "my competency", "my score", "my level", "my profile",
    "my evidence", "my assessment", "my learning", "my progress", "my course",
    "my result", "my quiz", "my recommendation", "my designation", "my department",
    "my role", "my training", "my history", "why was i recommended", "why am i",
    "my sql", "my python", "my sampling", "my rank", "my deficit", "my weakness",
    "am i on track", "how am i doing", "show my", "what is my",
})

# Questions clearly about curriculum or learning content
_RAG_SIGNALS: FrozenSet[str] = frozenset({
    "what is", "explain", "how does", "define", "describe", "overview",
    "introduction to", "concept of", "difference between", "compare",
    "what are the", "how to", "steps to", "methodology", "technique",
    "sampling technique", "sql joins", "python basics", "data analysis",
    "igot course", "nssta programme", "nssta training", "tpac",
    "karmayogi", "learning path", "curriculum", "syllabus",
    "course content", "study material", "reference document",
    "official statistics", "statistical method", "survey design",
    "probability sampling", "census methodology", "index construction",
    "price index", "labour force", "national accounts", "gdp calculation",
    "data collection", "field survey", "questionnaire design",
    "competency framework", "civil services competency", "competency definition",
    "level definition", "level 1", "level 2", "level 3", "level 4", "level 5",
    "evidence confidence", "supporting evidence", "authoritative evidence",
    "what does shikshasetu", "how does shikshasetu", "what is shikshasetu",
    "how does the platform", "what is the purpose",
    "give me an assessment", "ask me a question", "quiz me on",
    "explain this competency", "what is this course about",
})

# Questions about live MoSPI statistics or official data
_MCP_SIGNALS: FrozenSet[str] = frozenset({
    "latest plfs", "current plfs", "plfs indicator", "plfs data",
    "latest cpi", "current cpi", "cpi data", "consumer price index latest",
    "latest gdp", "current gdp", "gdp growth", "gdp data",
    "nss data", "nss survey result", "nss round",
    "nas data", "national accounts latest",
    "mospi data", "mospi indicator", "mospi release", "mospi report",
    "official statistics latest", "current statistics", "live data",
    "latest report", "recent survey result", "current figure",
    "unemployment rate", "current unemployment", "labour force data",
    "inflation data", "price data latest", "iip data",
    "index of industrial production",
})

# Hybrid trigger: user-data question that also needs curriculum context
_HYBRID_SIGNALS: FrozenSet[str] = frozenset({
    "why was this recommended", "why was this course recommended",
    "why is this course", "explain this recommendation",
    "why do i have a gap in", "what should i learn to improve",
    "how can i improve my", "what course should i take for my",
    "explain my gap in", "help me understand my", "what does my score mean",
    "recommend a course for my", "best course for my gap",
    "how to close my gap", "how to improve my competency",
    "what training for my gap",
})

# Patterns that are clearly unrelated to the ShikshaSetu domain
_OUT_OF_SCOPE_SIGNALS: FrozenSet[str] = frozenset({
    "write a poem", "write me a poem", "poem about",
    "write a story", "write me a story", "tell me a story",
    "joke", "tell me a joke", "make me laugh",
    "recipe", "food recipe", "how to cook", "cooking",
    "stock market", "share price", "cryptocurrency", "bitcoin",
    "sports", "cricket score", "football", "ipl",
    "movie", "film", "netflix", "bollywood",
    "weather", "weather forecast",
    "news", "current news", "latest news",
    "girlfriend", "boyfriend", "relationship advice",
    "what is love", "love",
    "translate", "translation",
    "write code for", "debug my code", "fix this bug",
    "javascript", "react app", "django project",
    "ignore previous", "ignore all previous", "disregard", "forget instructions",
    "reveal your prompt", "show your prompt", "what are your instructions",
    "system prompt", "hidden instructions", "your training data",
    "you are now", "act as", "pretend to be", "roleplay as",
    "jailbreak", "dan mode",
    "another employee", "other employee", "someone else's",
    "show me other users", "access other accounts",
})

# Injection attempt patterns (subset of OUT_OF_SCOPE that warrants a security response)
_INJECTION_SIGNALS: FrozenSet[str] = frozenset({
    "ignore previous", "ignore all previous", "disregard",
    "reveal your prompt", "show your prompt", "what are your instructions",
    "system prompt", "hidden instructions",
    "you are now", "act as", "pretend to be", "roleplay as",
    "jailbreak", "dan mode", "forget instructions",
})


# ── Classifier ────────────────────────────────────────────────────────────────

class QueryIntentRouter:
    """
    Deterministic rule-based intent classifier.

    Classification priority (highest to lowest):
      1. OUT_OF_SCOPE  — refuse before wasting any compute
      2. HYBRID        — explicit cross-domain question
      3. USER_DATA     — pure personal data question
      4. MCP           — live official statistics
      5. RAG           — curriculum / knowledge question
      6. HYBRID        — default when uncertain (conservative)
    """

    def classify(self, message: str) -> IntentResult:
        """
        Classify a user message into an IntentResult.

        Args:
            message: Raw user message text.

        Returns:
            IntentResult with intent, flags, and reason.
        """
        normalised = message.lower().strip()

        # ── 1. Injection / security attempts ─────────────────────────────────
        if self._matches_any(normalised, _INJECTION_SIGNALS):
            return IntentResult(
                intent=QueryIntent.OUT_OF_SCOPE,
                confidence=0.99,
                reason="Prompt injection / instruction override attempt detected",
                use_rag=False,
                use_user_data=False,
                use_mcp=False,
                refuse=True,
            )

        # ── 2. Clearly out-of-scope ───────────────────────────────────────────
        if self._matches_any(normalised, _OUT_OF_SCOPE_SIGNALS):
            return IntentResult(
                intent=QueryIntent.OUT_OF_SCOPE,
                confidence=0.95,
                reason="Message matches out-of-scope keyword pattern",
                use_rag=False,
                use_user_data=False,
                use_mcp=False,
                refuse=True,
            )

        # ── 3. Explicit hybrid (cross-domain) ─────────────────────────────────
        if self._matches_any(normalised, _HYBRID_SIGNALS):
            return IntentResult(
                intent=QueryIntent.HYBRID,
                confidence=0.90,
                reason="Explicit cross-domain trigger: needs user data + curriculum",
                use_rag=True,
                use_user_data=True,
                use_mcp=False,
                refuse=False,
            )

        # ── 4. Pure user-data question ────────────────────────────────────────
        has_user_signal   = self._matches_any(normalised, _USER_DATA_SIGNALS)
        has_rag_signal    = self._matches_any(normalised, _RAG_SIGNALS)
        has_mcp_signal    = self._matches_any(normalised, _MCP_SIGNALS)

        # Strong ownership markers: "my X" or "my X gap/level/score" → USER_DATA
        # even if generic knowledge words like "what is" are present.
        _STRONG_OWNERSHIP = ("my gap", "my skill", "my competency", "my score",
                             "my level", "my evidence", "my result", "my quiz",
                             "my assessment", "my learning", "my progress",
                             "what is my", "show my", "why am i")
        has_strong_ownership = self._matches_any(normalised, frozenset(_STRONG_OWNERSHIP))

        if has_strong_ownership:
            return IntentResult(
                intent=QueryIntent.USER_DATA,
                confidence=0.92,
                reason="Strong ownership marker ('my …') detected — user data only",
                use_rag=False,
                use_user_data=True,
                use_mcp=False,
                refuse=False,
            )

        if has_user_signal and not has_rag_signal and not has_mcp_signal:
            return IntentResult(
                intent=QueryIntent.USER_DATA,
                confidence=0.88,
                reason="User-data signal present; no curriculum or MCP signals",
                use_rag=False,
                use_user_data=True,
                use_mcp=False,
                refuse=False,
            )

        # ── 5. MCP / live statistics ──────────────────────────────────────────
        if has_mcp_signal and not has_user_signal:
            return IntentResult(
                intent=QueryIntent.MCP,
                confidence=0.87,
                reason="Live official statistics signal; no personal user data needed",
                use_rag=False,
                use_user_data=False,
                use_mcp=True,
                refuse=False,
            )

        # ── 6. Pure RAG / curriculum ──────────────────────────────────────────
        if has_rag_signal and not has_user_signal:
            return IntentResult(
                intent=QueryIntent.RAG,
                confidence=0.85,
                reason="Curriculum/knowledge signal; no personal user data needed",
                use_rag=True,
                use_user_data=False,
                use_mcp=False,
                refuse=False,
            )

        # ── 7. Mixed signals or ambiguous → HYBRID (conservative default) ─────
        return IntentResult(
            intent=QueryIntent.HYBRID,
            confidence=0.60,
            reason="Ambiguous or multi-signal — using HYBRID as conservative default",
            use_rag=True,
            use_user_data=True,
            use_mcp=has_mcp_signal,
            refuse=False,
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _matches_any(text: str, patterns: FrozenSet[str]) -> bool:
        """Return True if any pattern is a substring of text."""
        return any(p in text for p in patterns)

    def is_out_of_scope(self, message: str) -> bool:
        """Convenience method — True if message should be refused immediately."""
        return self.classify(message).refuse


# ── Module-level singleton ────────────────────────────────────────────────────

_router = QueryIntentRouter()


def classify_intent(message: str) -> IntentResult:
    """Module-level convenience function."""
    return _router.classify(message)
