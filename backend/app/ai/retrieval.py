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
            material_id: Material ID to filter chunks (for future multi-material support).
            top_k: Number of chunks to retrieve.

        Returns:
            List of relevant DocumentChunk instances.
        """
        results = self.vector_store.similarity_search(query, top_k=top_k)
        return [chunk for chunk, _ in results]

    def get_context_for_generation(
        self,
        retrieved_chunks: List[DocumentChunk],
        max_tokens: int = 2000,
    ) -> Tuple[str, List[str]]:
        """
        Format retrieved chunks into a context string for LLM.

        Args:
            retrieved_chunks: List of DocumentChunk instances.
            max_tokens: Maximum tokens to include (approximate, based on chars).

        Returns:
            Tuple of:
            - Formatted context string for LLM
            - List of chunk IDs used for traceability
        """
        if not retrieved_chunks:
            return "", []
        
        context_parts = []
        chunk_ids = []
        total_length = 0
        chars_per_token = 4  # Rough estimate
        max_chars = max_tokens * chars_per_token
        
        for chunk in retrieved_chunks:
            chunk_text = f"\n[Chunk {chunk.sequence}]"
            
            # Add source metadata
            if chunk.source_page:
                chunk_text += f" (Page {chunk.source_page})"
            if chunk.source_slide:
                chunk_text += f" (Slide {chunk.source_slide})"
            if chunk.source_section:
                chunk_text += f" - {chunk.source_section}"
            
            chunk_text += f"\n{chunk.text}\n"
            
            if total_length + len(chunk_text) > max_chars:
                break
            
            context_parts.append(chunk_text)
            chunk_ids.append(str(chunk.id) if chunk.id else f"chunk_{chunk.sequence}")
            total_length += len(chunk_text)
        
        context = "".join(context_parts)
        
        return context, chunk_ids
