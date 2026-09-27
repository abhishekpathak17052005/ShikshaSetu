"""Mock LLM Provider for testing and offline generation."""
import hashlib
import json
import random
import re
from typing import List, Optional

from .base import LLMProvider


class MockLLMProvider(LLMProvider):
    """
    Mock LLM provider for testing and deterministic offline question generation.

    Generates structured, source-grounded multiple-choice questions without calling external APIs.
    """

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> str:
        """Generate mock text response."""
        return "This is a grounded response generated for testing purposes."

    def generate_stream(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ):
        """Generate mock streaming text chunks."""
        text = self.generate(prompt, max_tokens, temperature)
        words = text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")

    def generate_json(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ):
        """
        Generate grounded JSON question responses from prompt context.
        Synthesizes varied questions, distinct Bloom levels, and plausible distractors
        directly from the supplied educational context without boilerplate filler strings.
        """
        match = re.search(r"exactly (\d+) questions", prompt)
        count = int(match.group(1)) if match else 1

        context_match = re.search(
            r"CONTEXT FROM DOCUMENT:\s*(.*?)(?:\n\s*AVAILABLE SOURCE CHUNK IDs:|\Z)",
            prompt,
            flags=re.DOTALL,
        )
        raw_context = (context_match.group(1).strip() if context_match else "")
        source_match = re.search(r"AVAILABLE SOURCE CHUNK IDs:\s*(\[[^\n]+\])", prompt)
        source_chunks = json.loads(source_match.group(1)) if source_match else []

        competency_match = re.search(r"Competency:\s*([A-Za-z0-9_]+)", prompt)
        competency = competency_match.group(1) if competency_match else "GENERAL"

        difficulty_match = re.search(r"Difficulty level:\s*([A-Za-z]+)", prompt)
        req_difficulty = difficulty_match.group(1).upper() if difficulty_match else "MEDIUM"

        bloom_match = re.search(r"Bloom target:\s*([A-Za-z]+)", prompt)
        req_bloom = bloom_match.group(1).upper() if bloom_match else None

        # Clean metadata artifacts from context text
        clean_context = re.sub(r"===.*?===", " ", raw_context)
        clean_context = re.sub(r"\[Chunk \d+\](?:\s*\(Page \d+\))?(?:\s*-\s*[^\n]+)?", " ", clean_context)
        clean_context = re.sub(r"--- (?:Content Block|Context Section)[^\n]+---", " ", clean_context)
        clean_context = re.sub(r"</?untrusted_educational_context>", " ", clean_context)
        clean_context = re.sub(r"\s+", " ", clean_context).strip()

        if not clean_context:
            clean_context = "Educational concepts and operational standards defined in curriculum."

        # Extract sentences from context
        raw_sentences = [
            s.strip() for s in re.split(r"(?<=[.!?])\s+", clean_context)
            if len(s.strip()) > 25 and not s.strip().startswith("[")
        ]
        if not raw_sentences:
            raw_sentences = [clean_context[:300]]

        start_match = re.search(r"starting from question index (\d+)", prompt)
        start_idx = int(start_match.group(1)) if start_match else 0

        # Bloom levels to cycle through if none requested or across multi-question batch
        bloom_cycle = ["REMEMBER", "UNDERSTAND", "APPLY", "ANALYZE", "EVALUATE"]
        difficulties = ["EASY", "MEDIUM", "HARD"]

        generated_list: List[dict] = []
        used_stems = set()

        for i in range(count):
            global_i = start_idx + i
            if count > 1:
                base_idx = bloom_cycle.index(req_bloom) if req_bloom in bloom_cycle else 0
                bloom = bloom_cycle[(base_idx + global_i) % len(bloom_cycle)]
            else:
                bloom = req_bloom or bloom_cycle[global_i % len(bloom_cycle)]

            diff = req_difficulty if req_difficulty in difficulties else difficulties[global_i % len(difficulties)]

            # Select primary source sentence for this question
            sentence = raw_sentences[global_i % len(raw_sentences)]

            # Extract meaningful key terms, filtering out structure labels and stopwords
            stopwords = {
                "source", "chunk", "page", "section", "content", "covering", "chapter",
                "module", "about", "with", "this", "that", "from", "into", "their",
                "which", "there", "these", "those", "have", "more", "also", "using",
                "detail", "techniques", "identified", "method"
            }
            words = [w for w in re.findall(r"\b[A-Za-z0-9_\-]{4,}\b", sentence) if not w.lower().startswith("chunk")]
            meaningful_words = [w for w in words if w.lower() not in stopwords]
            if not meaningful_words:
                meaningful_words = words or ["core concept"]
            key_term = meaningful_words[(global_i * 2) % len(meaningful_words)]
            key_term_2 = meaningful_words[(global_i * 2 + 1) % len(meaningful_words)]

            stem_templates = {
                "REMEMBER": [
                    "What is the primary role of {key_term} as defined in the provided material?",
                    "According to the documentation, what is {key_term} primarily responsible for?",
                    "Which definition accurately describes {key_term} based on the text?",
                ],
                "UNDERSTAND": [
                    "Which statement best explains how {key_term} operates within the described framework?",
                    "Why is {key_term} essential to the process described in the material?",
                    "What is the main principle underlying {key_term} as presented in the document?",
                ],
                "APPLY": [
                    "In an operational scenario involving {key_term}, which procedure should be implemented?",
                    "How should an administrator properly configure {key_term} based on the guidelines?",
                    "When encountering a requirement for {key_term}, what is the recommended procedure?",
                ],
                "ANALYZE": [
                    "Which factor distinguishes {key_term} from related components in the workflow?",
                    "What is the primary operational consequence if {key_term} is misapplied?",
                    "How does {key_term} interact with and impact {key_term_2}?",
                ],
                "EVALUATE": [
                    "Under what conditions is {key_term} deemed most effective for ensuring compliance?",
                    "Which criterion is most critical when assessing the effectiveness of {key_term}?",
                    "Why is {key_term} preferred over alternative approaches under the stated requirements?",
                ],
                "CREATE": [
                    "Which architectural configuration best integrates {key_term} to meet the documented objectives?",
                    "How should {key_term} be structured to ensure seamless operation with {key_term_2}?",
                    "What design strategy most effectively utilizes {key_term} based on the material?",
                ],
            }
            templates = stem_templates.get(bloom, stem_templates["UNDERSTAND"])
            stem = templates[global_i % len(templates)].format(key_term=key_term, key_term_2=key_term_2)
            if global_i >= len(templates):
                stem = f"{stem[:-1]} (Concept {global_i // len(templates) + 1})?"

            # Ensure unique stems
            disambiguator = 2
            original_stem = stem
            while stem.lower() in used_stems:
                stem = f"{original_stem[:-1]} (Variation {disambiguator})?"
                disambiguator += 1
            used_stems.add(stem.lower())

            # Generate correct answer from the source sentence (truncated cleanly)
            clean_ans = sentence[:220].rstrip(".,; ") + "."

            # Generate plausible domain distractors based on sentence terms and domain context
            distractor_1 = f"It requires manual authorization before any {key_term_2} modification can take place."
            distractor_2 = f"It operates as a deprecated client-side policy without server-side validation."
            distractor_3 = f"It is solely restricted to unauthenticated guest sessions across public endpoints."

            # If sentence contains specific security / statistical terms, adapt distractors
            if "csrf" in clean_context.lower() or "token" in clean_context.lower():
                distractor_1 = "Validating the HTTP Referer header exclusively without generating anti-forgery tokens."
                distractor_2 = "Encrypting browser session cookies using symmetrical keys without SameSite flags."
                distractor_3 = "Relying on client-side JavaScript execution without server verification."
            elif "sampling" in clean_context.lower() or "survey" in clean_context.lower():
                distractor_1 = "Selecting samples entirely based on convenience rather than probability weighting."
                distractor_2 = "Excluding non-response adjustments from the final weighting calculation."
                distractor_3 = "Applying uniform strata sizes irrespective of population variance."

            options_pool = [
                {"text": clean_ans, "is_correct": True},
                {"text": distractor_1, "is_correct": False},
                {"text": distractor_2, "is_correct": False},
                {"text": distractor_3, "is_correct": False},
            ]

            # Deterministic shuffle seeded by question index + sentence length
            rng = random.Random(i * 37 + len(sentence))
            rng.shuffle(options_pool)

            correct_letter = "A"
            for opt_idx, opt_row in enumerate(options_pool):
                if opt_row["is_correct"]:
                    correct_letter = chr(ord("A") + opt_idx)
                    break

            # Associate chunk ID if available
            chosen_chunks = [source_chunks[i % len(source_chunks)]] if source_chunks else []

            generated_list.append({
                "question": stem,
                "options": [row["text"] for row in options_pool],
                "correct_answer": correct_letter,
                "explanation": f"The material directly establishes: {clean_ans}",
                "difficulty": diff,
                "bloom_level": bloom,
                "source_chunks": chosen_chunks,
            })

        if count == 1 and generated_list:
            return generated_list[0]
        return generated_list

    def is_available(self) -> bool:
        """Mock provider is always available."""
        return True
