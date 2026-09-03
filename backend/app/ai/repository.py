"""Repository layer for learning materials and document chunks (sync version with PyMongo)."""
from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from pymongo.database import Database

from .models import LearningMaterial, DocumentChunk


class LearningMaterialRepository:
    """Repository for LearningMaterial documents (synchronous)."""

    @staticmethod
    def create(database: Database, material: LearningMaterial) -> str:
        """
        Create a new learning material.

        Args:
            database: MongoDB database instance.
            material: LearningMaterial instance.

        Returns:
            Created material ID.
        """
        collection = database["learning_materials"]
        result = collection.insert_one(material.model_dump(by_alias=True, exclude={"id"}))
        return str(result.inserted_id)

    @staticmethod
    def get_by_id(database: Database, material_id: str, user_id: str) -> Optional[LearningMaterial]:
        """
        Get learning material by ID (with user ownership check).

        Args:
            database: MongoDB database instance.
            material_id: Material ID.
            user_id: User ID for authorization check (stored as string or ObjectId in DB).

        Returns:
            LearningMaterial or None if not found or not owned by user.
        """
        collection = database["learning_materials"]
        
        m_oid = ObjectId(material_id) if ObjectId.is_valid(material_id) else None
        u_oid = ObjectId(user_id) if ObjectId.is_valid(user_id) else None
        user_id_str = str(user_id)
        
        id_query = {"$in": [m_oid, str(material_id)]} if m_oid else str(material_id)
        user_query = {"$in": [user_id_str, u_oid]} if u_oid else user_id_str

        query = {
            "_id": id_query,
            "user_id": user_query,
        }
        doc = collection.find_one(query)
        
        if not doc:
            return None
        
        doc["_id"] = str(doc["_id"])
        doc["id"] = str(doc["_id"])
        return LearningMaterial(**doc)

    @staticmethod
    def get_by_status(database: Database, status: str, limit: int = 200) -> List[LearningMaterial]:
        """Get all learning materials with a given status (e.g. READY)."""
        collection = database["learning_materials"]
        cursor = collection.find({"status": status}).sort("created_at", -1).limit(limit)
        materials = []
        for doc in cursor:
            doc["id"] = str(doc["_id"])
            doc["_id"] = str(doc["_id"])
            materials.append(LearningMaterial(**doc))
        return materials

    @staticmethod
    def get_by_user(database: Database, user_id: str, limit: int = 100) -> List[LearningMaterial]:
        """
        Get all learning materials for a user.

        Args:
            database: MongoDB database instance.
            user_id: User ID (stored as string or ObjectId in DB).
            limit: Maximum number of results.

        Returns:
            List of LearningMaterial documents.
        """
        collection = database["learning_materials"]
        u_oid = ObjectId(user_id) if ObjectId.is_valid(user_id) else None
        user_id_str = str(user_id)
        query = {"$or": [{"user_id": user_id_str}, {"user_id": u_oid}]} if u_oid else {"user_id": user_id_str}
        
        cursor = collection.find(query).sort("created_at", -1).limit(limit)
        materials = []
        
        for doc in cursor:
            doc["id"] = str(doc["_id"])
            doc["_id"] = str(doc["_id"])
            materials.append(LearningMaterial(**doc))
        
        return materials

    @staticmethod
    def update_status(
        database: Database,
        material_id: str,
        status: str,
        extraction_status: Optional[str] = None,
        error: Optional[str] = None
    ) -> bool:
        """
        Update material processing status.

        Args:
            database: MongoDB database instance.
            material_id: Material ID.
            status: New status (UPLOADED, PROCESSING, READY, FAILED).
            extraction_status: Optional extraction result.
            error: Optional error message.

        Returns:
            True if updated, False otherwise.
        """
        collection = database["learning_materials"]
        
        try:
            obj_id = ObjectId(material_id)
        except Exception:
            return False
        
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if extraction_status is not None:
            update_data["extraction_status"] = extraction_status
        
        if error is not None:
            update_data["error_message"] = error
        
        result = collection.update_one(
            {"_id": obj_id},
            {"$set": update_data}
        )
        
        return result.modified_count > 0

    @staticmethod
    def update_chunk_counts(
        database: Database,
        material_id: str,
        chunk_count: int,
        embedding_count: int = 0
    ) -> bool:
        """
        Update chunk counts for a material.

        Args:
            database: MongoDB database instance.
            material_id: Material ID.
            chunk_count: Total chunks created.
            embedding_count: Total chunks embedded.

        Returns:
            True if updated, False otherwise.
        """
        collection = database["learning_materials"]
        
        try:
            obj_id = ObjectId(material_id)
        except Exception:
            return False
        
        result = collection.update_one(
            {"_id": obj_id},
            {"$set": {
                "chunk_count": chunk_count,
                "embedding_count": embedding_count,
                "updated_at": datetime.utcnow()
            }}
        )
        
        return result.modified_count > 0

    @staticmethod
    def delete(database: Database, material_id: str, user_id: str) -> bool:
        """
        Delete a learning material (with ownership check).

        Args:
            database: MongoDB database instance.
            material_id: Material ID.
            user_id: User ID for authorization check (stored as string in DB).

        Returns:
            True if deleted, False otherwise.
        """
        collection = database["learning_materials"]
        
        try:
            obj_id = ObjectId(material_id)
            user_id_str = str(user_id) if not isinstance(user_id, str) else user_id
        except Exception:
            return False
        
        result = collection.delete_one({
            "_id": obj_id,
            "user_id": user_id_str
        })
        
        return result.deleted_count > 0


class DocumentChunkRepository:
    """Repository for DocumentChunk documents (synchronous)."""

    # Fields that must never be written to MongoDB (raw vectors stored separately)
    _EXCLUDE_FROM_DB = {"id", "embedding"}

    @staticmethod
    def create_many(database: Database, chunks: List[DocumentChunk]) -> int:
        """
        Create multiple document chunks WITHOUT embedding vectors.
        Embeddings are written separately via update_embedding() to avoid
        storing large float arrays inside every document on initial insert.
        """
        collection = database["document_chunks"]

        if not chunks:
            return 0

        # Exclude embedding vectors from initial insert — written later via update_embedding()
        docs = [
            chunk.model_dump(by_alias=True, exclude={"id", "embedding"})
            for chunk in chunks
        ]
        result = collection.insert_many(docs)
        # Backfill the string ID onto each chunk object so callers can reference it
        for chunk, inserted_id in zip(chunks, result.inserted_ids):
            chunk.id = str(inserted_id)
        return len(result.inserted_ids)

    @staticmethod
    def get_by_material(
        database: Database,
        material_id: str,
        limit: int = 1000
    ) -> List[DocumentChunk]:
        """
        Get all chunks for a material.

        Args:
            database: MongoDB database instance.
            material_id: Material ID.
            limit: Maximum number of results.

        Returns:
            List of DocumentChunk documents.
        """
        collection = database["document_chunks"]
        
        cursor = collection.find({"material_id": material_id}).sort("sequence", 1).limit(limit)
        chunks = []
        
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            doc["id"] = str(doc["_id"])
            chunks.append(DocumentChunk(**doc))
        
        return chunks

    @staticmethod
    def delete_by_material(database: Database, material_id: str) -> int:
        """
        Delete all chunks for a material.

        Args:
            database: MongoDB database instance.
            material_id: Material ID.

        Returns:
            Number of chunks deleted.
        """
        collection = database["document_chunks"]
        
        result = collection.delete_many({"material_id": material_id})
        
        return result.deleted_count

    @staticmethod
    def get_by_ids(database: Database, chunk_ids: List[str]) -> List[DocumentChunk]:
        """
        Get chunks by their IDs.

        Args:
            database: MongoDB database instance.
            chunk_ids: List of chunk IDs.

        Returns:
            List of DocumentChunk documents.
        """
        collection = database["document_chunks"]
        
        obj_ids = [ObjectId(cid) for cid in chunk_ids if ObjectId.is_valid(cid)]
        str_ids = [str(cid) for cid in chunk_ids]
        
        id_clauses = []
        if obj_ids:
            id_clauses.append({"_id": {"$in": obj_ids}})
        if str_ids:
            id_clauses.append({"_id": {"$in": str_ids}})
            id_clauses.append({"chunk_id": {"$in": str_ids}})
        
        if not id_clauses:
            return []
        
        cursor = collection.find({"$or": id_clauses})
        chunks = []
        
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            doc["id"] = str(doc["_id"])
            chunks.append(DocumentChunk(**doc))
        
        return chunks

    @staticmethod
    def update_embedding(
        database: Database,
        chunk_id: str,
        embedding: list,
        embedding_model: str,
    ) -> bool:
        """
        Persist a real semantic embedding vector for a chunk.
        Called after successful embedding API call.

        Args:
            database: MongoDB database instance.
            chunk_id: The _id of the chunk to update.
            embedding: Float list from the embedding model.
            embedding_model: Name of the model used (for provenance).

        Returns:
            True if updated.
        """
        obj_id = ObjectId(chunk_id) if ObjectId.is_valid(chunk_id) else None
        if not obj_id:
            return False
        result = database["document_chunks"].update_one(
            {"_id": obj_id},
            {"$set": {
                "embedding": embedding,
                "embedding_status": "EMBEDDED",
                "embedding_model": embedding_model,
            }},
        )
        return result.modified_count > 0

    @staticmethod
    def mark_embedding_failed(database: Database, chunk_id: str) -> bool:
        """Mark a chunk's embedding as FAILED so it can be retried later."""
        obj_id = ObjectId(chunk_id) if ObjectId.is_valid(chunk_id) else None
        if not obj_id:
            return False
        result = database["document_chunks"].update_one(
            {"_id": obj_id},
            {"$set": {"embedding_status": "FAILED"}},
        )
        return result.modified_count > 0

    @staticmethod
    def get_chunks_with_embeddings(
        database: Database,
        material_id: str,
        limit: int = 2000,
    ) -> List[DocumentChunk]:
        """
        Retrieve chunks that have a real semantic embedding (embedding_status == EMBEDDED).
        Used by EmbeddingIndexManager to rebuild the numpy index on startup.
        """
        collection = database["document_chunks"]
        cursor = collection.find(
            {"material_id": material_id, "embedding_status": "EMBEDDED"},
            # Include embedding field for index rebuild
        ).sort("sequence", 1).limit(limit)
        chunks = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            doc["id"] = str(doc["_id"])
            chunks.append(DocumentChunk(**doc))
        return chunks

    @staticmethod
    def get_chunks_needing_embedding(
        database: Database,
        material_id: str,
    ) -> List[DocumentChunk]:
        """Return chunks with embedding_status PENDING or FAILED for retry."""
        collection = database["document_chunks"]
        cursor = collection.find(
            {"material_id": material_id, "embedding_status": {"$in": ["PENDING", "FAILED"]}},
        ).sort("sequence", 1)
        chunks = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            doc["id"] = str(doc["_id"])
            chunks.append(DocumentChunk(**doc))
        return chunks
