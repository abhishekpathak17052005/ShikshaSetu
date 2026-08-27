"""Grounding validation for generated MCQs."""
from typing import List, Tuple, Optional

from .schemas import GeneratedMCQ
from .models import DocumentChunk
from .repository import DocumentChunkRepository


class GroundingValidator:
    """
    Validate that generated MCQs are properly grounded in source material.
    """

    @staticmethod
    async def validate_question(
        question: GeneratedMCQ,
        chunk_repository: DocumentChunkRepository,
        material_id: str,
        database=None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that a question is properly grounded.

        Args:
            question: GeneratedMCQ to validate.
            chunk_repository: Repository for chunk lookup.
            material_id: Material ID for validation.
            database: Optional MongoDB database instance.

        Returns:
            Tuple of:
            - bool: True if valid, False otherwise
            - str: Error message if invalid, None if valid
        """
        # 1. Check that question has source chunks
        if not question.source_chunks:
            return False, "Question has no source chunk references"
        
        # 2. Verify that referenced chunks exist and belong to material
        try:
            # If database is not provided, chunks are assumed to be valid (for mocking)
            if database is not None:
                chunks = await chunk_repository.get_by_ids(database, question.source_chunks)
                
                if not chunks:
                    return False, "Referenced source chunks not found"
                
                # Verify all chunks belong to the correct material
                for chunk in chunks:
                    if chunk.material_id != material_id:
                        return False, "Source chunk does not belong to specified material"
        
        except Exception as e:
            return False, f"Failed to verify source chunks: {str(e)}"
        
        # 3. Validate schema
        if not question.question or len(question.question.strip()) < 10:
            return False, "Question is too short"
        
        if not question.options or len(question.options) < 3:
            return False, "Question must have at least 3 options"
        
        if not question.correct_answer or question.correct_answer not in "ABCDE":
            return False, "Invalid correct answer"
        
        if not question.explanation or len(question.explanation.strip()) < 10:
            return False, "Explanation is too short"
        
        # 4. Check correct answer is valid for number of options
        correct_idx = ord(question.correct_answer) - ord('A')
        if correct_idx >= len(question.options):
            return False, "Correct answer index exceeds number of options"
        
        # All checks passed
        return True, None

    @staticmethod
    async def validate_batch(
        questions: List[GeneratedMCQ],
        chunk_repository: DocumentChunkRepository,
        material_id: str,
        database=None,
    ) -> Tuple[List[GeneratedMCQ], List[Tuple[GeneratedMCQ, str]]]:
        """
        Validate a batch of questions.

        Args:
            questions: List of GeneratedMCQ to validate.
            chunk_repository: Repository for chunk lookup.
            material_id: Material ID for validation.
            database: Optional MongoDB database instance.

        Returns:
            Tuple of:
            - List of valid questions
            - List of (invalid_question, error_message) tuples
        """
        valid_questions = []
        invalid_questions = []
        
        for question in questions:
            is_valid, error_msg = await GroundingValidator.validate_question(
                question,
                chunk_repository,
                material_id,
                database
            )
            
            if is_valid:
                valid_questions.append(question)
            else:
                invalid_questions.append((question, error_msg or "Unknown error"))
        
        return valid_questions, invalid_questions

    @staticmethod
    def check_semantic_grounding(
        question: GeneratedMCQ,
        source_chunks: List[DocumentChunk],
    ) -> Tuple[bool, Optional[str]]:
        """
        Perform a basic semantic check that question relates to chunks.
        
        This is a heuristic check, not a guarantee of factual correctness.

        Args:
            question: GeneratedMCQ to check.
            source_chunks: List of source chunks for context.

        Returns:
            Tuple of:
            - bool: True if question seems grounded, False if appears to hallucinate
            - str: Advisory message if applicable
        """
        if not source_chunks:
            return False, "No source chunks provided for validation"
        
        # Get common words from question and chunks
        question_words = set(question.question.lower().split())
        question_words = {w for w in question_words if len(w) > 3}  # Filter short words
        
        chunk_text = " ".join([chunk.text for chunk in source_chunks]).lower()
        chunk_words = set(chunk_text.split())
        
        # Calculate overlap
        overlap = question_words & chunk_words
        
        # If there's significant word overlap, likely grounded
        overlap_ratio = len(overlap) / len(question_words) if question_words else 0
        
        if overlap_ratio < 0.1:
            return False, "Question has minimal semantic overlap with source material"
        
        return True, None
