"""Vector embedding and retrieval service."""
import numpy as np
from typing import List, Tuple, Optional

from .embeddings.base import EmbeddingProvider
from .models import DocumentChunk


class VectorStore:
    """
    In-memory vector store for similarity retrieval.
    
    Stores embeddings and provides similarity search.
    Can be rebuilt from persisted chunks if needed.
    """

    def __init__(self, embedding_provider: EmbeddingProvider):
        """
        Initialize vector store.

        Args:
            embedding_provider: Configured embedding provider.
        """
        self.embedding_provider = embedding_provider
        self.chunks: List[DocumentChunk] = []
        self.embeddings: Optional[np.ndarray] = None
        self.dimension = embedding_provider.get_dimension()

    def add_chunks(self, chunks: List[DocumentChunk]) -> int:
        """
        Add chunks and compute their embeddings.

        Args:
            chunks: List of DocumentChunk instances.

        Returns:
            Number of chunks added and embedded.
        """
        if not chunks:
            return 0
        
        # Extract texts
        texts = [chunk.text for chunk in chunks]
        
        # Compute embeddings
        try:
            embeddings = self.embedding_provider.embed_texts(texts)
        except Exception as e:
            raise Exception(f"Embedding failed: {str(e)}")
        
        # Store chunks with embeddings
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
            self.chunks.append(chunk)
        
        # Rebuild embeddings array
        self._rebuild_embeddings_array()
        
        return len(chunks)

    def _rebuild_embeddings_array(self) -> None:
        """Rebuild the embeddings numpy array from stored chunks."""
        if not self.chunks:
            self.embeddings = None
            return
        
        embeddings_list = [chunk.embedding for chunk in self.chunks if chunk.embedding]
        if embeddings_list:
            self.embeddings = np.array(embeddings_list, dtype=np.float32)
        else:
            self.embeddings = None

    def similarity_search(
        self,
        query: str,
        top_k: int = 5,
        threshold: Optional[float] = None,
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Search for similar chunks using cosine similarity.

        Args:
            query: Query text.
            top_k: Number of top results to return.
            threshold: Optional minimum similarity score (0-1).

        Returns:
            List of (chunk, similarity_score) tuples, sorted by similarity descending.
        """
        if not self.chunks or self.embeddings is None:
            return []
        
        # Embed query
        try:
            query_embedding = self.embedding_provider.embed_text(query)
        except Exception as e:
            raise Exception(f"Query embedding failed: {str(e)}")
        
        query_embedding = np.array(query_embedding, dtype=np.float32)
        
        # Compute cosine similarity
        similarities = self._cosine_similarity(query_embedding, self.embeddings)
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            similarity_score = float(similarities[idx])
            
            # Apply threshold if specified
            if threshold is not None and similarity_score < threshold:
                continue
            
            chunk = self.chunks[idx]
            results.append((chunk, similarity_score))
        
        return results

    @staticmethod
    def _cosine_similarity(query_vec: np.ndarray, doc_vecs: np.ndarray) -> np.ndarray:
        """
        Compute cosine similarity between query and document vectors.

        Args:
            query_vec: Query embedding (1D array).
            doc_vecs: Document embeddings (2D array).

        Returns:
            Array of similarity scores.
        """
        # Normalize vectors
        query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)
        doc_norms = doc_vecs / (np.linalg.norm(doc_vecs, axis=1, keepdims=True) + 1e-10)
        
        # Compute dot product (cosine similarity for normalized vectors)
        similarities = np.dot(doc_norms, query_norm)
        
        return similarities

    def clear(self) -> None:
        """Clear all stored chunks and embeddings."""
        self.chunks = []
        self.embeddings = None


class RetrieverService:
    """
    Service for retrieving relevant chunks for question generation.
    """

    def __init__(self, vector_store: VectorStore):
        """
        Initialize retriever service.

        Args:
            vector_store: Configured vector store.
        """
        self.vector_store = vector_store

    def retrieve_for_generation(
        self,
        query: str,
        material_id: str,
        top_k: int = 5,
    ) -> List[DocumentChunk]:
        """
        Retrieve relevant chunks for MCQ generation.

        Args:
            query: Query (e.g., competency name or user request).
            material_id: Material ID to filter chunks.
            top_k: Number of chunks to retrieve.

        Returns:
            List of relevant DocumentChunk instances.
        """
        return self.retrieve_diverse_for_generation(query=query, material_id=material_id, top_k=top_k)

    def retrieve_diverse_for_generation(
        self,
        query: str,
        material_id: str,
        top_k: int = 5,
        exclude_chunk_ids: Optional[List[str]] = None,
    ) -> List[DocumentChunk]:
        """
        Retrieve diverse relevant chunks for question generation, avoiding repeats.
        
        Args:
            query: Semantic query.
            material_id: Target material ID.
            top_k: Number of diverse chunks to retrieve.
            exclude_chunk_ids: Chunks already used in previous generations to avoid.
        """
        exclude_set = set(exclude_chunk_ids or [])
        material_chunks = [
            chunk for chunk in self.vector_store.chunks
            if not material_id or str(chunk.material_id) == str(material_id)
        ]

        if not material_chunks:
            return []

        # If total material chunks is small, cycle cleanly
        if len(material_chunks) <= top_k:
            return material_chunks

        # Score chunks via similarity search
        scored_results = self.vector_store.similarity_search(query, top_k=len(self.vector_store.chunks))
        material_scored = [
            (chunk, score) for chunk, score in scored_results
            if not material_id or str(chunk.material_id) == str(material_id)
        ]

        if not material_scored:
            material_scored = [(c, 1.0) for c in material_chunks]

        # Prioritize unused chunks with high relevance
        unused_chunks = [chunk for chunk, _ in material_scored if str(chunk.id or chunk.sequence) not in exclude_set]
        used_chunks = [chunk for chunk, _ in material_scored if str(chunk.id or chunk.sequence) in exclude_set]

        selected: List[DocumentChunk] = []

        # To avoid clustering in a single section, pick diverse pages/sequences
        seen_pages = set()
        seen_sequences = set()

        # Pass 1: pick unused chunks across distinct pages/sections
        for chunk in unused_chunks:
            page_key = chunk.source_page if chunk.source_page is not None else chunk.sequence
            if page_key not in seen_pages:
                selected.append(chunk)
                seen_pages.add(page_key)
                seen_sequences.add(chunk.sequence)
                if len(selected) >= top_k:
                    break

        # Pass 2: fill remaining from other unused chunks
        if len(selected) < top_k:
            for chunk in unused_chunks:
                if chunk.sequence not in seen_sequences:
                    selected.append(chunk)
                    seen_sequences.add(chunk.sequence)
                    if len(selected) >= top_k:
                        break

        # Pass 3: fill from previously used chunks if still needed
        if len(selected) < top_k:
            for chunk in used_chunks:
                if chunk.sequence not in seen_sequences:
                    selected.append(chunk)
                    seen_sequences.add(chunk.sequence)
                    if len(selected) >= top_k:
                        break

        # Fallback to direct slice
        if not selected:
            selected = [c for c, _ in material_scored[:top_k]]

        return selected[:top_k]

    def get_context_for_generation(
        self,
        retrieved_chunks: List[DocumentChunk],
        max_tokens: int = 2500,
    ) -> Tuple[str, List[str]]:
        """
        Format retrieved chunks into a clean context string for LLM,
        ensuring chunk metadata does not leak into readable prose.

        Args:
            retrieved_chunks: List of DocumentChunk instances.
            max_tokens: Maximum tokens to include.

        Returns:
            Tuple of:
            - Formatted context string for LLM
            - List of chunk IDs used for traceability
        """
        if not retrieved_chunks:
            return "", []

        import re
        context_parts = []
        chunk_ids = []
        total_length = 0
        chars_per_token = 4
        max_chars = max_tokens * chars_per_token

        for chunk in retrieved_chunks:
            cid = str(chunk.id) if chunk.id else f"chunk_{chunk.sequence}"
            raw_text = (chunk.text or "").strip()
            # Clean out any old embedded [Chunk ...] prefixes in stored text
            clean_text = re.sub(r"^\[Chunk \d+\][^\n]*\n*", "", raw_text).strip()

            seq_label = f"Chunk {chunk.sequence}"
            meta_info = f"SOURCE: {seq_label} | ID: {cid}"
            if chunk.source_page:
                meta_info += f" | Page {chunk.source_page}"
            if chunk.source_section:
                meta_info += f" | Section {chunk.source_section}"

            # Format cleanly as an external reference delimiter
            chunk_block = f"\n=== {meta_info} ===\n{clean_text}\n"

            if total_length + len(chunk_block) > max_chars and context_parts:
                break

            context_parts.append(chunk_block)
            chunk_ids.append(cid)
            total_length += len(chunk_block)

        context = "".join(context_parts)
        return context, chunk_ids

