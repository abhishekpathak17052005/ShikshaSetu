"""Plain text document extraction."""
from typing import List, Tuple


class TXTExtractor:
    """Extract text from plain text documents."""

    @staticmethod
    def extract(file_path: str) -> Tuple[str, List[dict]]:
        """
        Extract text from a TXT file.

        Args:
            file_path: Path to the TXT file.

        Returns:
            Tuple of:
            - Full extracted text
            - List of section metadata with text
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().strip()

            if not content:
                raise Exception("Text document is empty")

            # Split into logical paragraphs
            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
            if not paragraphs:
                paragraphs = [content]

            pages_metadata = [
                {"section": idx + 1, "text": p} for idx, p in enumerate(paragraphs)
            ]

            return content, pages_metadata
        except Exception as e:
            raise Exception(f"TXT extraction failed: {str(e)}")
