"""PDF document extraction."""
from typing import List, Tuple

from pypdf import PdfReader


class PDFExtractor:
    """Extract text from PDF documents."""

    @staticmethod
    def extract(file_path: str) -> Tuple[str, List[dict]]:
        """
        Extract text from a PDF file.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Tuple of:
            - Full extracted text
            - List of page metadata with text

        Raises:
            Exception: If PDF cannot be read or has no extractable text.
        """
        try:
            reader = PdfReader(file_path)
            
            if len(reader.pages) == 0:
                raise Exception("PDF contains no pages")
            
            full_text = []
            pages_metadata = []
            
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                
                if text:
                    full_text.append(text)
                    pages_metadata.append({
                        "page": page_num,
                        "text": text
                    })
            
            if not full_text:
                raise Exception("PDF contains no extractable text")
            
            return "\n".join(full_text), pages_metadata
        
        except Exception as e:
            # Re-raise with context
            raise Exception(f"PDF extraction failed: {str(e)}")
