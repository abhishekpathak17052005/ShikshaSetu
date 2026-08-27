"""Deterministic text chunking with metadata preservation."""
from typing import List, Optional

from .models import DocumentChunk


class TextChunker:
    """Deterministically chunk text while preserving metadata."""

    @staticmethod
    def chunk_text(
        text: str,
        material_id: str,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        source_page: Optional[int] = None,
        source_slide: Optional[int] = None,
        source_section: Optional[str] = None,
    ) -> List[DocumentChunk]:
        """
        Split text into chunks with metadata.

        Args:
            text: Text to chunk.
            material_id: ID of the learning material.
            chunk_size: Target chunk size in characters.
            chunk_overlap: Overlap between chunks in characters.
            source_page: Page number (for PDFs/DOCX).
            source_slide: Slide number (for PPTX).
            source_section: Section/heading name.

        Returns:
            List of DocumentChunk instances.
        """
        if not text or not text.strip():
            return []
        
        if chunk_size <= 0:
            chunk_size = 500
        if chunk_overlap < 0:
            chunk_overlap = 0
        if chunk_overlap >= chunk_size:
            chunk_overlap = chunk_size // 2
        
        chunks = []
        sequence = 0
        
        # Split by paragraphs first (separated by double newlines)
        paragraphs = text.split('\n\n')
        
        current_chunk = []
        current_length = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            para_length = len(paragraph)
            
            # If adding this paragraph would exceed chunk size
            if current_length > 0 and current_length + para_length + 1 > chunk_size:
                # Save current chunk
                chunk_text = '\n\n'.join(current_chunk).strip()
                if chunk_text:
                    chunks.append(
                        DocumentChunk(
                            material_id=material_id,
                            sequence=sequence,
                            text=chunk_text,
                            source_page=source_page,
                            source_slide=source_slide,
                            source_section=source_section,
                        )
                    )
                    sequence += 1
                
                # Start new chunk with overlap from previous
                if chunk_overlap > 0 and current_chunk:
                    # Keep last paragraph(s) that fit in overlap
                    overlap_text = '\n\n'.join(current_chunk)
                    if len(overlap_text) > chunk_overlap:
                        # Keep only the end that fits in overlap
                        overlap_text = overlap_text[-chunk_overlap:]
                    current_chunk = [overlap_text] if overlap_text.strip() else []
                    current_length = len(overlap_text)
                else:
                    current_chunk = []
                    current_length = 0
            
            current_chunk.append(paragraph)
            current_length += para_length + 2  # +2 for the double newline separator
        
        # Save final chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk).strip()
            if chunk_text:
                chunks.append(
                    DocumentChunk(
                        material_id=material_id,
                        sequence=sequence,
                        text=chunk_text,
                        source_page=source_page,
                        source_slide=source_slide,
                        source_section=source_section,
                    )
                )
        
        return chunks

    @staticmethod
    def chunk_document(
        text: str,
        material_id: str,
        pages_metadata: List[dict],
        chunk_size: int = 500,
        chunk_overlap: int = 100,
    ) -> List[DocumentChunk]:
        """
        Chunk a document while preserving page/slide metadata.

        Args:
            text: Full document text.
            material_id: ID of the learning material.
            pages_metadata: List of page/slide metadata dicts.
                           Each should have 'page' or 'slide' key and 'text' key.
            chunk_size: Target chunk size in characters.
            chunk_overlap: Overlap between chunks in characters.

        Returns:
            List of DocumentChunk instances with preserved metadata.
        """
        chunks = []
        sequence = 0
        
        for page_meta in pages_metadata:
            page_text = page_meta.get("text", "").strip()
            if not page_text:
                continue
            
            page_num = page_meta.get("page")
            slide_num = page_meta.get("slide")
            section_name = page_meta.get("section")
            
            # Chunk this page's text
            page_chunks = TextChunker.chunk_text(
                text=page_text,
                material_id=material_id,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                source_page=page_num,
                source_slide=slide_num,
                source_section=section_name,
            )
            
            # Update sequence numbers
            for chunk in page_chunks:
                chunk.sequence = sequence
                sequence += 1
                chunks.append(chunk)
        
        return chunks
