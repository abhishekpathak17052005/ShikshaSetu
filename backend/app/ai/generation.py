"""Grounded MCQ generation from retrieved context."""
import json
from typing import List, Optional

from app.core.config import get_settings

from .providers.base import LLMProvider
from .retrieval import RetrieverService
from .schemas import GeneratedMCQ
from .models import DocumentChunk


class MCQGenerator:
    """
    Generate grounded MCQs from document content using an LLM.
    
    All questions are strictly grounded in the retrieved source chunks.
    """

    def __init__(self, llm_provider: LLMProvider, retriever: RetrieverService):
        """
        Initialize MCQ generator.

        Args:
            llm_provider: Configured LLM provider.
            retriever: Retriever service with loaded chunks.
        """
        self.llm_provider = llm_provider
        self.retriever = retriever
        self.settings = get_settings()

    def generate_questions(
        self,
        query: str,
        competency_code: str,
        question_count: int = 5,
        difficulty: Optional[str] = None,
    ) -> List[GeneratedMCQ]:
        """
        Generate grounded MCQs for a competency.

        Args:
            query: Query for retrieval (e.g., competency name).
            competency_code: Competency code for association.
            question_count: Number of questions to generate.
            difficulty: Target difficulty (EASY, MEDIUM, HARD).

        Returns:
            List of validated GeneratedMCQ instances.

        Raises:
            Exception: If generation fails after retries.
        """
        questions = []
        retry_count = 0
        max_retries = self.settings.generation_retry_count
        
        while len(questions) < question_count and retry_count < max_retries:
            try:
                # Retrieve relevant chunks
                retrieved_chunks = self.retriever.retrieve_for_generation(
                    query=query,
                    material_id="",  # Not used for single material filtering
                    top_k=10
                )
                
                if not retrieved_chunks:
                    raise Exception("No relevant chunks retrieved")
                
                # Format context
                context, chunk_ids = self.retriever.get_context_for_generation(
                    retrieved_chunks,
                    max_tokens=2000
                )
                
                # Generate questions
                batch_size = min(question_count - len(questions), 3)
                generated = self._generate_batch(
                    context=context,
                    chunk_ids=chunk_ids,
                    competency_code=competency_code,
                    batch_size=batch_size,
                    difficulty=difficulty
                )
                
                questions.extend(generated)
                
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    raise Exception(f"Failed to generate questions after {max_retries} retries: {str(e)}")
        
        return questions[:question_count]

    def _generate_batch(
        self,
        context: str,
        chunk_ids: List[str],
        competency_code: str,
        batch_size: int = 3,
        difficulty: Optional[str] = None,
    ) -> List[GeneratedMCQ]:
        """
        Generate a batch of questions from context.

        Args:
            context: Formatted context from retrieved chunks.
            chunk_ids: IDs of source chunks.
            competency_code: Competency code.
            batch_size: Number of questions to generate in this batch.
            difficulty: Target difficulty level.

        Returns:
            List of validated GeneratedMCQ instances.
        """
        # Build prompt
        difficulty_instruction = ""
        if difficulty:
            difficulty_instruction = f"Difficulty level: {difficulty}."
        
        prompt = f"""You are an expert educational question generator. Your task is to create multiple-choice questions
from the following educational material. Each question MUST be directly supported by the provided context.

CRITICAL RULES:
1. Generate ONLY from the provided context - do not use external knowledge
2. Do NOT invent facts or hallucinate
3. Every question must have a clear correct answer supported by the text
4. Create exactly {batch_size} questions in JSON array format
5. Each question must have exactly 4 options (A, B, C, D)
6. {difficulty_instruction}
7. Competency: {competency_code}

CONTEXT FROM DOCUMENT:
{context}

AVAILABLE SOURCE CHUNK IDs: {json.dumps(chunk_ids)}

Generate {batch_size} multiple-choice questions based ONLY on the above context.
Return a JSON array with exactly {batch_size} question objects.

Each question object must have:
- "question": string (question text)
- "options": array of 4 strings (A, B, C, D options)
- "correct_answer": string (single letter: A, B, C, or D)
- "explanation": string (explanation referencing the source material)
- "difficulty": string (EASY, MEDIUM, or HARD)
- "source_chunks": array of chunk IDs from AVAILABLE SOURCE CHUNK IDs that support this question

RESPONSE FORMAT (valid JSON array only, no markdown, no extra text):
[
  {{
    "question": "...",
    "options": ["...", "...", "...", "..."],
    "correct_answer": "B",
    "explanation": "...",
    "difficulty": "MEDIUM",
    "source_chunks": ["chunk-id-1", "chunk-id-2"]
  }}
]"""

        try:
            # For mock provider, use generate_json to get structured output
            # For real provider, call generate and parse
            if hasattr(self.llm_provider, 'generate_json'):
                # Try to use generate_json if available (useful for testing)
                try:
                    response_data = self.llm_provider.generate_json(
                        prompt=prompt,
                        max_tokens=2000,
                        temperature=0.7
                    )
                    # Ensure response_data is a list
                    if isinstance(response_data, dict):
                        # Single question returned, wrap in list
                        questions_data = [response_data]
                    else:
                        questions_data = response_data
                except:
                    # Fall back to text generation and parsing
                    response_text = self.llm_provider.generate(
                        prompt=prompt,
                        max_tokens=2000,
                        temperature=0.7
                    )
                    questions_data = self._parse_response(response_text)
            else:
                # Standard text generation and parsing
                response_text = self.llm_provider.generate(
                    prompt=prompt,
                    max_tokens=2000,
                    temperature=0.7
                )
                questions_data = self._parse_response(response_text)
            
            # Validate and convert to schema
            validated_questions = []
            for q_data in questions_data:
                try:
                    mcq = GeneratedMCQ(**q_data)
                    # Ensure source chunks are mapped to retrieved chunk IDs
                    valid_chunk_ids = [cid for cid in mcq.source_chunks if cid in chunk_ids]
                    mcq.source_chunks = valid_chunk_ids if valid_chunk_ids else chunk_ids[:2]
                    validated_questions.append(mcq)
                except Exception as e:
                    # Skip invalid questions
                    continue
            
            return validated_questions
        
        except Exception as e:
            raise Exception(f"Batch generation failed: {str(e)}")

    @staticmethod
    def _parse_response(response_text: str) -> List[dict]:
        """
        Parse LLM response to extract JSON questions.

        Args:
            response_text: Raw LLM response.

        Returns:
            List of question dictionaries.

        Raises:
            Exception: If response cannot be parsed.
        """
        # Try to extract JSON array from response
        response_text = response_text.strip()
        
        # If response starts with markdown code block, extract the content
        if response_text.startswith("```"):
            # Find content between backticks
            start = response_text.find('[')
            end = response_text.rfind(']')
            if start >= 0 and end > start:
                response_text = response_text[start:end+1]
        
        # Try to parse as JSON
        try:
            data = json.loads(response_text)
            if isinstance(data, list):
                return data
            else:
                raise Exception("Response is not a JSON array")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON in response: {str(e)}")
