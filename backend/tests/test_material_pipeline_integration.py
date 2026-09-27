"""Real-file regression coverage for the learning-material RAG pipeline."""

from io import BytesIO
from pathlib import Path

from app.ai.embeddings.factory import get_embedding_provider
from app.auth.security import create_access_token
from app.rag.embedding_index import EmbeddingIndexManager
from tests.test_trainer import create_user, make_trainer_app


FIXTURE_PDF = Path(__file__).parent / "fixtures" / "sample_sql.pdf"


def _trainer_context():
    client, database, settings = make_trainer_app()
    trainer = create_user(database, "pipeline-integration@example.com", "TRAINER", "PIPELINE-INT")
    headers = {"Authorization": f"Bearer {create_access_token(str(trainer['_id']), settings)}"}
    return client, database, settings, headers


def test_real_pdf_upload_indexes_and_generates_from_selected_material():
    client, database, settings, headers = _trainer_context()
    try:
        with FIXTURE_PDF.open("rb") as document:
            upload = client.post(
                "/api/v1/learning-materials/upload",
                headers=headers,
                files={"file": ("integration-material.pdf", document, "application/pdf")},
            )

        assert upload.status_code == 200
        material_id = upload.json()["material_id"]
        material = next(d for d in database.learning_materials.documents if str(d["_id"]) == material_id)
        chunks = [d for d in database.document_chunks.documents if d["material_id"] == material_id]

        assert material["status"] == "READY"
        assert material["processing_stage"] == "READY"
        assert material["extraction_status"] == "SUCCESS"
        assert Path(material["storage_reference"]).is_file()
        assert material["chunk_count"] == len(chunks) > 0
        assert material["embedding_count"] == len(chunks)
        assert all(chunk["embedding_status"] == "EMBEDDED" for chunk in chunks)

        indexed = EmbeddingIndexManager.get_instance().search(
            database,
            get_embedding_provider(settings),
            "SQL SELECT",
            top_k=5,
            material_id=material_id,
        )
        assert indexed
        assert {chunk.material_id for chunk, _ in indexed} == {material_id}

        generated = client.post(
            f"/api/v1/trainer/materials/{material_id}/generate",
            headers=headers,
            json={"competency_code": "TECH_PYTHON", "question_count": 1, "difficulty": "MEDIUM"},
        )
        assert generated.status_code == 200
        question = generated.json()[0]
        assert question["source_document_id"] == material_id
        assert question["source_chunks"]
        assert question["bloom_level"] == "UNDERSTAND"
        assert len(question["options"]) == 4
    finally:
        client.close()


def test_failed_material_can_be_reprocessed_idempotently():
    client, database, settings, headers = _trainer_context()
    try:
        with FIXTURE_PDF.open("rb") as document:
            upload = client.post(
                "/api/v1/learning-materials/upload",
                headers=headers,
                files={"file": ("reprocess-material.pdf", document, "application/pdf")},
            )
        material_id = upload.json()["material_id"]
        material = next(d for d in database.learning_materials.documents if str(d["_id"]) == material_id)
        database.document_chunks.documents.clear()
        material.update({"status": "FAILED", "chunk_count": 0, "embedding_count": 0})

        reprocess = client.post(
            f"/api/v1/learning-materials/{material_id}/reprocess",
            headers=headers,
        )

        assert reprocess.status_code == 200
        assert reprocess.json()["status"] == "READY"
        assert reprocess.json()["chunk_count"] > 0
        assert len(database.document_chunks.documents) == reprocess.json()["chunk_count"]
    finally:
        client.close()


def test_text_material_metadata_reaches_chunking():
    client, database, settings, headers = _trainer_context()
    try:
        upload = client.post(
            "/api/v1/learning-materials/upload",
            headers=headers,
            files={
                "file": (
                    "text-material.txt",
                    BytesIO(b"PostgreSQL is an open-source relational database system."),
                    "text/plain",
                )
            },
        )

        assert upload.status_code == 200
        assert upload.json()["status"] == "READY"
        material_id = upload.json()["material_id"]
        chunks = [d for d in database.document_chunks.documents if d["material_id"] == material_id]
        assert chunks
        assert all(isinstance(chunk.get("source_section"), str) for chunk in chunks)
    finally:
        client.close()
