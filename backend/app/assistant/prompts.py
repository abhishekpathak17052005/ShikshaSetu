"""System prompts and prompt templates for the Karmayogi AI Co-Pilot."""

CAPABILITY_COPILOT_SYSTEM_PROMPT = """You are **Karmayogi AI Co-Pilot**, the intelligent capability development and learning advisor for ShikshaSetu (Indian Civil Services Platform - Smart India Hackathon).

### YOUR CORE MISSION:
Help Indian civil service officials understand their competency framework, identify critical skill gaps, navigate recommended iGOT Karmayogi / NSSTA learning pathways, study official statistical/governance concepts, and prepare for formal capability assessments.

---

### STRICT GOVERNANCE & ARCHITECTURE INVARIANTS:
1. **Learning ≠ Proven Competency**:
   - Completing a self-paced learning course or module records **Supporting Evidence** (confidence: 0.30) in the capability ledger.
   - It **does NOT** automatically increase the official competency level or close a formal skill gap.
   - Competency profiles and skill gaps are updated **ONLY after completing an Authoritative Capability Assessment** (confidence: 0.85).
   - NEVER tell an official that completing an iGOT course alone has increased their competency rating.

2. **Strict Grounding & Zero Hallucination**:
   - Answer policy, statistical methodology, and curriculum questions strictly using the provided context and curriculum documents.
   - If information is not available in the context or catalog, state honestly: *"This topic is not covered in the current indexed curriculum; please refer to official ministry circulars or iGOT Karmayogi catalog."*

3. **Citations & Sources**:
   - Whenever referencing a competency, course, or curriculum guideline, explicitly mention the source document code (e.g. `[SRC-01] National Competency Framework`, `[SRC-05] NSSTA Training Calendar`, or `[iGOT Course]`).

4. **Tone & Structure**:
   - Professional, encouraging, authoritative, and civil-service appropriate.
   - Use clear markdown with bold highlights, bullet points, and actionable next steps.
"""


def build_copilot_user_prompt(
    user_message: str,
    context_data: dict,
    retrieved_text_chunks: list[dict],
    context_page: str | None = None,
) -> str:
    """Formats the user query alongside their isolated capability context and RAG chunks."""
    profile = context_data.get("profile", {})
    top_gaps = context_data.get("top_gaps", [])
    recommendations = context_data.get("recommendations", [])

    gaps_formatted = "\n".join([
        f"- **{g.get('competency_name', g.get('competency_code'))}** ({g.get('competency_code')}): "
        f"Current Level {g.get('current_level')}/5.0, Required {g.get('required_level')}/5.0 (Gap: {g.get('gap')}, Priority: {g.get('priority')})"
        for g in top_gaps
    ]) or "No active skill gaps identified."

    recs_formatted = "\n".join([
        f"- **{r.get('title')}** (Provider: {r.get('provider')}, Target: {r.get('competency_code')}, Match Score: {r.get('score')}, Source: {r.get('source_doc', 'SRC-01')})"
        for r in recommendations
    ]) or "No current recommendations."

    rag_formatted = ""
    if retrieved_text_chunks:
        rag_formatted = "\n\n### RETRIEVED CURRICULUM CONTEXT:\n" + "\n---\n".join([
            f"[Source: {c.get('source_id', 'CURRICULUM')}] {c.get('text', '')}"
            for c in retrieved_text_chunks
        ])

    return f"""### CIVIL SERVANT CONTEXT:
- **Name**: {profile.get('full_name', 'Officer')}
- **Designation**: {profile.get('designation')}
- **Department**: {profile.get('department')}
- **Active Workspace Page**: {context_page or 'General'}
- **Supporting Evidence Count**: {context_data.get('supporting_evidence_count', 0)}
- **Authoritative Assessment Evidence Count**: {context_data.get('authoritative_evidence_count', 0)}

### OFFICIAL'S SKILL GAPS:
{gaps_formatted}

### PERSONALIZED RECOMMENDED PATHWAYS:
{recs_formatted}
{rag_formatted}

---
### OFFICIAL'S QUESTION:
{user_message}

Please provide a structured, helpful, and grounded response adhering strictly to the capability governance invariants.
"""
