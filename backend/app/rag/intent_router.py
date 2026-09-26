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
    GLOSSARY     = "GLOSSARY"       # high-precision definition lookup
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
    use_glossary: bool         # True → search rag_glossary collection first
    refuse: bool               # True → return polite refusal immediately


# Standard refusal message required across ShikshaSetu
STANDARD_OFF_TOPIC_REFUSAL: str = (
    "I'm not able to help with that request. I'm here to help with ShikshaSetu, government workforce "
    "capabilities, competencies, skill gaps, assessments, "
    "quizzes and learning recommendations."
)

# ── Keyword sets ──────────────────────────────────────────────────────────────

# Questions clearly about the user's own data
_USER_DATA_SIGNALS: FrozenSet[str] = frozenset({
    "my gap", "my skill", "my competency", "my score", "my level", "my profile",
    "my evidence", "my assessment", "my learning", "my progress", "my course",
    "my result", "my quiz", "my recommendation", "my designation", "my department",
    "my role", "my training", "my history", "why was i recommended", "why am i",
    "my sql", "my python", "my sampling", "my rank", "my deficit", "my weakness",
    "am i on track", "how am i doing", "show my", "what is my",
    "assigned to me", "assigned quizzes", "my assigned", "my tests",
    "what quizzes are assigned", "quizzes assigned to me",
    "who am i", "about me", "tell me about myself", "my identity",
})

# Domain-specific curriculum or capability content (requires concrete domain nouns, NOT bare verbs)
_RAG_SIGNALS: FrozenSet[str] = frozenset({
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
    "how does the platform", "what is the purpose of shikshasetu",
    "give me an assessment", "ask me a question", "quiz me on",
    "explain this competency", "what is this course about",
    "competency intelligence", "civic capability", "igot karmayogi",
    "talathi", "statistical officer", "land records", "revenue department",
    "mospi", "dopt", "nssta", "cbc", "capacity building commission",
})

# Positive domain signals that confirm a query is relevant to ShikshaSetu / Civil Services
_POSITIVE_DOMAIN_SIGNALS: FrozenSet[str] = frozenset({
    "shikshasetu", "karmayogi", "igot", "nssta", "tpac", "dashboard",
    "competency", "competencies", "proficiency", "skill gap", "skill gaps",
    "skill", "skills", "assessment", "assessments", "quiz", "quizzes",
    "test", "tests", "evidence", "ledger", "recommendation", "recommendations",
    "course", "courses", "training", "curriculum", "modules", "learning",
    "civil service", "civil services", "government", "governance",
    "designation", "department", "ministry", "mospi", "dopt", "revenue",
    "talathi", "statistical officer", "sampling", "survey", "statistics",
    "statistical", "deficit", "benchmark", "score", "scores",
    "role", "roles", "target proficiency", "confidence level",
    "authoritative", "supporting",
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
    "current unemployment", "labour force data",
    "inflation data", "price data latest", "iip data",
    "today's iip", "today's cpi", "today's gdp", "today's plfs",
    "latest iip", "current iip", "iip figure",
    "latest unemployment", "current unemployment rate",
    "latest gdp growth", "latest inflation",
})

# Hybrid trigger: user-data question that also needs curriculum context
_HYBRID_SIGNALS: FrozenSet[str] = frozenset({
    "why was this recommended", "why was this course recommended",
    "why is this course", "explain this recommendation",
    "why do i have a gap in", "what should i learn to improve",
    "how can i improve my", "what course should i take for my",
    "what courses should i take", "what should i study",
    "explain my gap in", "help me understand my", "what does my score mean",
    "recommend a course for my", "best course for my gap",
    "how to close my gap", "how to improve my competency",
    "what training for my gap",
    "why was the", "why was it recommended",
    "which quiz should i take", "why was this quiz recommended",
})

# Patterns that are clearly unrelated to the ShikshaSetu domain
_OUT_OF_SCOPE_SIGNALS: FrozenSet[str] = frozenset({
    "capital of", "france", "paris", "germany", "berlin", "cricket", "football",
    "match score", "who won", "write me a python", "write a python", "write python code",
    "write code", "generate code", "program in", "debug my code", "fix this bug",
    "write a poem", "write me a poem", "poem about", "write a story", "tell me a story",
    "tell me a joke", "make me laugh", "joke", "recipe", "food recipe", "how to cook",
    "cooking", "biryani", "pasta", "curry", "pizza", "burger",
    "stock market", "share price", "cryptocurrency", "bitcoin", "ethereum",
    "nse nifty", "bse sensex", "nifty", "sensex",
    "movie", "film", "netflix", "bollywood", "hollywood", "actor", "actress",
    "weather", "weather forecast", "temperature today",
    "relationship advice", "girlfriend", "boyfriend", "dating", "love poem",
    "quantum physics", "astronomy", "black hole", "photosynthesis",
    "write my resume", "build my resume", "cv builder",
    "how do i hack", "hack a website", "penetration testing",
    "translate this", "spanish", "french", "german", "russian",
    "another employee", "other employee", "someone else's",
    "show me other users", "access other accounts",
    "nssta seats available", "available seats", "seat availability",
})

# Patterns that strongly indicate a pure concept definition lookup → GLOSSARY route
# IMPORTANT: Generic patterns like "what is" and "explain" are intentionally EXCLUDED.
# They are too broad and would swallow RAG queries. Only match when the query
# contains a specific statistical/organisational term from the domain vocabulary.
_GLOSSARY_SIGNALS: FrozenSet[str] = frozenset({
    # Specific statistical concepts only — NOT generic verbs
    "gdp", "gross domestic product", "gva", "gross value added",
    "ndp", "net domestic product",
    "gdp deflator", "chain linking", "base year",
    "cfc", "consumption of fixed capital",
    "cpi", "consumer price index",
    "wpi", "wholesale price index",
    "core inflation",
    "laspeyres index", "laspeyres price",
    "index of industrial production",
    # IIP is tricky: only glossary when definitional ("what is iip", "define iip")
    # not when combined with "latest"/"current" (→ MCP)
    "plfs", "periodic labour force survey",
    "lfpr", "labour force participation rate",
    "worker population ratio", "wpr",
    "usual principal activity", "upss", "usual status",
    "current weekly status",
    "unemployment rate", "what is unemployment",
    "pps sampling", "probability proportional to size",
    "stratified random sampling", "what is stratified",
    "sampling frame", "what is a sampling frame",
    "confidence interval", "what is confidence interval",
    "standard error", "what is standard error",
    "non-sampling error",
    "dqaf", "data quality assessment framework",
    "sdmx", "statistical data and metadata",
    "sdg", "sustainable development goal",
    "what is the nsc", "national statistical commission",
    "what is nsso", "national sample survey office",
    "what is nso", "national statistical office",
    "what is nssta", "national school of statistical",
    "capacity building commission", "what is cbc",
    "igot karmayogi", "what is igot", "karmayogi platform",
    "mission karmayogi",
    "probity in public service",
    "competency level", "what is authoritative evidence", "what is supporting evidence",
    "what is skill gap", "what is a skill gap",
    "what is shikshasetu",
    "define gdp", "define cpi", "define plfs", "define lfpr",
    "define wpr", "define gva",
    "what does plfs stand for", "what does cpi stand for",
    "what does gdp stand for", "what does wpi stand for",
    "what does lfpr stand for", "what does wpr stand for",
    "what does iip stand for", "what does dqaf stand for",
    "what does mospi stand for", "what does nssta stand for",
    "explain consumer price index", "explain gdp", "explain gva",
    "explain plfs", "explain sampling frame",
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
      3. USER_DATA     — pure personal data question (strong ownership)
      4. GLOSSARY      — "what is X?" concept definition → glossary first
      5. MCP           — live official statistics
      6. RAG           — curriculum / knowledge question
      7. HYBRID        — default when uncertain (conservative)
    """

    def classify(self, message: str) -> IntentResult:
        normalised = message.lower().strip()

        # ── 1. Injection / security attempts ─────────────────────────────────
        if self._matches_any(normalised, _INJECTION_SIGNALS):
            return IntentResult(
                intent=QueryIntent.OUT_OF_SCOPE,
                confidence=0.99,
                reason="Prompt injection / instruction override attempt detected",
                use_rag=False, use_user_data=False, use_mcp=False,
                use_glossary=False, refuse=True,
            )

        # ── 2. Clearly out-of-scope ───────────────────────────────────────────
        if self._matches_any(normalised, _OUT_OF_SCOPE_SIGNALS):
            return IntentResult(
                intent=QueryIntent.OUT_OF_SCOPE,
                confidence=0.95,
                reason="Message matches out-of-scope keyword pattern",
                use_rag=False, use_user_data=False, use_mcp=False,
                use_glossary=False, refuse=True,
            )

        # ── 3. Explicit hybrid (cross-domain) — check BEFORE strong ownership ──
        # Hybrid signals take priority because a question like
        # "My gap is high, what courses?" needs both user data AND curriculum.
        if self._matches_any(normalised, _HYBRID_SIGNALS):
            has_glossary = self._matches_any(normalised, _GLOSSARY_SIGNALS)
            return IntentResult(
                intent=QueryIntent.HYBRID,
                confidence=0.90,
                reason="Explicit cross-domain trigger: needs user data + curriculum",
                use_rag=True, use_user_data=True, use_mcp=False,
                use_glossary=has_glossary, refuse=False,
            )

        has_user_signal  = self._matches_any(normalised, _USER_DATA_SIGNALS)
        has_rag_signal   = self._matches_any(normalised, _RAG_SIGNALS)
        has_mcp_signal   = self._matches_any(normalised, _MCP_SIGNALS)
        has_gloss_signal = self._matches_any(normalised, _GLOSSARY_SIGNALS)

        # ── 4a. Strong ownership → USER_DATA ─────────────────────────────────
        _STRONG_OWNERSHIP = frozenset((
            "my gap", "my skill", "my competency", "my score",
            "my level", "my evidence", "my result", "my quiz",
            "my assessment", "my learning", "my progress",
            "what is my", "show my", "why am i",
            "show me my", "how many learning", "how many activities",
            "my current competency", "my latest", "my profile",
            "what competency level do i", "do i need for",
            "what level do i need", "who am i", "about me", "tell me about myself",
        ))
        if self._matches_any(normalised, _STRONG_OWNERSHIP):
            return IntentResult(
                intent=QueryIntent.USER_DATA,
                confidence=0.92,
                reason="Strong ownership marker ('my …') detected — user data only",
                use_rag=False, use_user_data=True, use_mcp=False,
                use_glossary=False, refuse=False,
            )

        # ── 4b. Pure user-data (no curriculum or MCP signals) ────────────────
        if has_user_signal and not has_rag_signal and not has_mcp_signal:
            return IntentResult(
                intent=QueryIntent.USER_DATA,
                confidence=0.88,
                reason="User-data signal present; no curriculum or MCP signals",
                use_rag=False, use_user_data=True, use_mcp=False,
                use_glossary=False, refuse=False,
            )

        # ── 5. GLOSSARY — "what is X?" with no user-data context ─────────────
        # Prioritise the high-precision glossary for simple concept definitions
        # before falling through to full document RAG.
        if has_gloss_signal and not has_user_signal and not has_mcp_signal:
            return IntentResult(
                intent=QueryIntent.GLOSSARY,
                confidence=0.91,
                reason="Concept definition signal — route to glossary first, then RAG fallback",
                use_rag=True,          # fallback if glossary misses
                use_user_data=False,
                use_mcp=False,
                use_glossary=True,     # check glossary collection first
                refuse=False,
            )

        # ── 6. MCP / live statistics ──────────────────────────────────────────
        if has_mcp_signal and not has_user_signal:
            return IntentResult(
                intent=QueryIntent.MCP,
                confidence=0.87,
                reason="Live official statistics signal; no personal user data needed",
                use_rag=False, use_user_data=False, use_mcp=True,
                use_glossary=False, refuse=False,
            )

        # ── 7. Pure RAG / curriculum ──────────────────────────────────────────
        if has_rag_signal and not has_user_signal:
            return IntentResult(
                intent=QueryIntent.RAG,
                confidence=0.85,
                reason="Curriculum/knowledge signal; no personal user data needed",
                use_rag=True, use_user_data=False, use_mcp=False,
                use_glossary=has_gloss_signal, refuse=False,
            )

        # ── 8. General ShikshaSetu / Government domain check ──────────────────
        has_domain_signal = self._matches_any(normalised, _POSITIVE_DOMAIN_SIGNALS)
        if has_domain_signal:
            if has_user_signal:
                return IntentResult(
                    intent=QueryIntent.USER_DATA,
                    confidence=0.80,
                    reason="Domain signal + user context -> USER_DATA",
                    use_rag=False, use_user_data=True, use_mcp=False,
                    use_glossary=False, refuse=False,
                )
            return IntentResult(
                intent=QueryIntent.RAG,
                confidence=0.75,
                reason="Civil services domain signal -> RAG knowledge",
                use_rag=True, use_user_data=False, use_mcp=False,
                use_glossary=has_gloss_signal, refuse=False,
            )

        # ── 9. Strict Scope Gate: No positive domain signal -> OUT_OF_SCOPE ──
        return IntentResult(
            intent=QueryIntent.OUT_OF_SCOPE,
            confidence=0.95,
            reason="Query does not relate to ShikshaSetu, competencies, or government workforce",
            use_rag=False, use_user_data=False, use_mcp=False,
            use_glossary=False, refuse=True,
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
