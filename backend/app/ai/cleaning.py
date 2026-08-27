"""Text cleaning and normalization."""
import re


class TextCleaner:
    """Clean and normalize extracted document text."""

    @staticmethod
    def clean(text: str) -> str:
        """
        Clean extracted text by:
        - Normalizing whitespace
        - Removing extra blank lines
        - Removing obvious extraction artifacts
        - Preserving meaningful structure

        Args:
            text: Raw extracted text.

        Returns:
            Cleaned text.
        """
        # Remove form feed and other control characters
        text = text.replace('\f', '\n')
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t\r')
        
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove leading/trailing whitespace from each line
        lines = [line.rstrip() for line in text.split('\n')]
        
        # Remove excessive blank lines (more than 2 consecutive)
        cleaned_lines = []
        blank_count = 0
        for line in lines:
            if line.strip() == '':
                blank_count += 1
                if blank_count <= 2:
                    cleaned_lines.append(line)
            else:
                blank_count = 0
                cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """
        Normalize whitespace within text while preserving paragraph structure.

        Args:
            text: Text to normalize.

        Returns:
            Normalized text.
        """
        # Split by double newlines to preserve paragraphs
        paragraphs = text.split('\n\n')
        
        normalized_paragraphs = []
        for para in paragraphs:
            # Replace multiple spaces/tabs with single space
            normalized_para = re.sub(r'[ \t]+', ' ', para)
            # Replace multiple newlines within paragraph with space
            normalized_para = re.sub(r'\n+', ' ', normalized_para)
            normalized_para = normalized_para.strip()
            if normalized_para:
                normalized_paragraphs.append(normalized_para)
        
        return '\n\n'.join(normalized_paragraphs)

    @staticmethod
    def remove_artifacts(text: str) -> str:
        """
        Remove common PDF/OCR extraction artifacts.

        Args:
            text: Text with potential artifacts.

        Returns:
            Cleaned text.
        """
        # Remove page numbers at end of lines (e.g., "content 123")
        # Be conservative to avoid removing valid content
        text = re.sub(r'\s+\d{1,4}\s*$', '', text, flags=re.MULTILINE)
        
        # Remove excessive special characters that likely indicate corruption
        text = re.sub(r'[^\w\s\-.,;:!?\'"\n\t]', '', text)
        
        return text
