"""Repository layer for learning materials and document chunks."""
from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from pymongo.database import Database

from .models import LearningMaterial, DocumentChunk


class LearningMaterialRepository:
    """Repository for LearningMaterial documents."""

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
    async def get_by_id(database: Database, material_id: str, user_id: str) -> Optional[LearningMaterial]:
        """
        Get learning material by ID (with user ownership check).

        Args:
            database: MongoDB database instance.
            material_id: Material ID.
            user_id: User ID for authorization check.

        Returns:
            LearningMaterial or None if not found or not owned by user.
        """
        collection = database["learning_materials"]
        
        try:
            obj_id = ObjectId(material_id)
        except Exception:
            return None
        
        doc = await collection.find_one({
            "_id": obj_id,
            "user_id": user_id
        })
        
        if not doc:
            return None
        
        doc["id"] = str(doc["_id"])
        return LearningMaterial(**doc)

    @staticmethod
    async def get_by_user(database: Database, user_id: str, limit: int = 100) -> List[LearningMaterial]:
        """
        Get all learning materials for a user.

        Args:
            database: MongoDB database instance.
            user_id: User ID.
            limit: Maximum number of results.

        Returns:
            List of LearningMaterial documents.
        """
        collection = database["learning_materials"]
        
        cursor = collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        materials = []
        
        async for doc in cursor:
            doc["id"] = str(doc["_id"])
            materials.append(LearningMaterial(**doc))
        
        return materials

    @staticmethod
    def update_status(database: Database, material_id: str, status: str, extraction_status: Optional[str] = None, error: Optional[str] = None) -> bool:
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
            update_data["extraction_error"] = error
        
        result = collection.update_one(
            {"_id": obj_id},
            {"$set": update_data}
        )
        
        return result.modified_count > 0

    @staticmethod
    async def update_chunk_counts(database: Database, material_id: str, chunk_count: int, embedding_count: int = 0) -> bool:
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
        
        result = await collection.update_one(
            {"_id": obj_id},
            {"$set": {
                "chunk_count": chunk_count,
                "embedding_count": embedding_count,
                "updated_at": datetime.utcnow()
            }}
        )
        
        return result.modified_count > 0

    @staticmethod
    async def delete(database: Database, material_id: str, user_id: str) -> bool:
        """
        Delete a learning material (with ownership check).

        Args:
            database: MongoDB database instance.
            material_id: Material ID.
            user_id: User ID for authorization check.

        Returns:
            True if deleted, False otherwise.
        """
        collection = database["learning_materials"]
        
        try:
            obj_id = ObjectId(material_id)
        except Exception:
            return False
        
        result = await collection.delete_one({
            "_id": obj_id,
            "user_id": user_id
        })
        
        return result.deleted_count > 0


class DocumentChunkRepository:
    """Repository for DocumentChunk documents."""

    @staticmethod
    async def create_many(database: Database, chunks: List[DocumentChunk]) -> int:
        """
        Create multiple document chunks.

        Args:
            database: MongoDB database instance.
            chunks: List of DocumentChunk instances.

        Returns:
            Number of chunks inserted.
        """
        collection = database["document_chunks"]
        
        if not chunks:
            return 0
        
        result = await collection.insert_many(
            [chunk.model_dump(by_alias=True, exclude={"id"}) for chunk in chunks]
        )
        
        return len(result.inserted_ids)

    @staticmethod
    async def get_by_material(database: Database, material_id: str, limit: int = 1000) -> List[DocumentChunk]:
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
        
        async for doc in cursor:
            doc["id"] = str(doc["_id"])
            chunks.append(DocumentChunk(**doc))
        
        return chunks

    @staticmethod
    async def delete_by_material(database: Database, material_id: str) -> int:
        """
        Delete all chunks for a material.

        Args:
            database: MongoDB database instance.
            material_id: Material ID.

        Returns:
            Number of chunks deleted.
        """
        collection = database["document_chunks"]
        
        result = await collection.delete_many({"material_id": material_id})
        
        return result.deleted_count

    @staticmethod
    async def get_by_ids(database: Database, chunk_ids: List[str]) -> List[DocumentChunk]:
        """
        Get chunks by their IDs.

        Args:
            database: MongoDB database instance.
            chunk_ids: List of chunk IDs.

        Returns:
            List of DocumentChunk documents.
        """
        collection = database["document_chunks"]
        
        obj_ids = []
        for chunk_id in chunk_ids:
            try:
                obj_ids.append(ObjectId(chunk_id))
            except Exception:
                continue
        
        if not obj_ids:
            return []
        
        cursor = collection.find({"_id": {"$in": obj_ids}})
        chunks = []
        
        async for doc in cursor:
            doc["id"] = str(doc["_id"])
            chunks.append(DocumentChunk(**doc))
        
        return chunks


# Add missing import at the end (remove this - already imported above)
