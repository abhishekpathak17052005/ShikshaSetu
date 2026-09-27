"""
P0 Regression Test Suite for ShikshaSetu Assessment Question Generation,
RAG Retrieval, Grounding, and Review Studio (Edit/Reject).
"""
import pytest
from bson import ObjectId
from datetime import datetime, UTC

from app.auth.security import create_access_token, hash_password
from app.core.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient
from tests.test_trainer import FakeDatabase, FakeCollection, create_user, create_material, make_trainer_app

from app.ai.models import DocumentChunk
from app.ai.retrieval import VectorStore, RetrieverService
from app.ai.generation import MCQGenerator, is_duplicate_question
from app.ai.embeddings.mock_provider import MockEmbeddingProvider
from app.ai.providers.mock_provider import MockLLMProvider
from app.ai.validation import GroundingValidator, filter_duplicate_questions
from app.trainer.repository import TrainerRepository
from app.ai.repository import DocumentChunkRepository


def test_no_source_metadata_or_correct_key_in_options_or_stems():
    """Verify that [Chunk X], (Page Y), and 'Correct Key' are never present in options or question stems."""
    embed = MockEmbeddingProvider()
    vs = VectorStore(embed)
    
    # Insert chunks with metadata
    chunks = [
        DocumentChunk(
            material_id="mat_meta",
            sequence=1,
            text="[Chunk 1] (Page 2) - Cross-Site Request Forgery is an attack where unauthorized commands are submitted from a user that the web application trusts.",
            source_page=2,
            source_section="Security",
        ),
        DocumentChunk(
            material_id="mat_meta",
            sequence=2,
            text="[Chunk 2] (Page 3) - Anti-CSRF tokens must be cryptographically secure and uniquely associated with the user session.",
            source_page=3,
            source_section="Mitigation",
        ),
    ]
    vs.add_chunks(chunks)
    retriever = RetrieverService(vs)
    generator = MCQGenerator(MockLLMProvider(), retriever)
    
    questions = generator.generate_questions(
        query="CSRF Defense",
        competency_code="DIGOV_CYBERSECURITY",
        question_count=4,
        difficulty="MEDIUM",
        material_id="mat_meta",
    )
    
    assert len(questions) > 0
    forbidden_terms = ["[chunk", "page 2", "page 3", "correct key", "grounded explanation", "==="]
    for q in questions:
        stem_lower = q.question.lower()
        for term in forbidden_terms:
            assert term not in stem_lower, f"Forbidden term '{term}' leaked into question stem: {q.question}"
            
        assert len(q.options) == 4
        for opt in q.options:
            opt_lower = opt.lower()
            for term in forbidden_terms:
                assert term not in opt_lower, f"Forbidden term '{term}' leaked into option: {opt}"
                
        assert q.correct_answer in ("A", "B", "C", "D")
        assert len(set(q.options)) == 4


def test_filler_distractors_are_rejected():
    """Verify that generic filler distractors are strictly rejected by the normalizer."""
    bad_question = {
        "question": "Which statement is directly supported by the uploaded material?",
        "options": [
            "Valid authentic statement from chunk context.",
            "This claim is not stated in the uploaded material.",
            "The uploaded material provides no support for this claim.",
            "This option cannot be verified from the uploaded material.",
        ],
        "correct_answer": "A",
        "explanation": "Directly from the chunk.",
        "difficulty": "MEDIUM",
        "bloom_level": "UNDERSTAND",
        "source_chunks": ["chunk_1"],
    }
    normalized = MCQGenerator._normalize_generated_question(bad_question)
    assert normalized is None, "Normalizer must reject generic boilerplate distractors and stem"


def test_duplicate_question_detection():
    """Verify exact and near-duplicate question detection."""
    existing = [
        {"question": "What is the primary role of Cross-Site Request Forgery defenses?"},
    ]
    # Exact duplicate
    assert is_duplicate_question("What is the primary role of Cross-Site Request Forgery defenses?", existing) is True
    # Minor casing/punctuation
    assert is_duplicate_question("what is the primary role of cross-site request forgery defenses", existing) is True
    # Near duplicate with high token overlap
    assert is_duplicate_question("What is the primary role of Cross-Site Request Forgery defense?", existing) is True
    # Distinct question on the same topic
    assert is_duplicate_question("How do anti-CSRF tokens prevent state-changing request forgery?", existing) is False


def test_retrieval_diversity_across_chunks():
    """Verify retriever diversifies across document sequence/pages instead of repeating top chunk."""
    embed = MockEmbeddingProvider()
    vs = VectorStore(embed)
    chunks = [
        DocumentChunk(material_id="mat_div", sequence=i, text=f"Concept {i} details in deep architectural implementation.", source_page=i)
        for i in range(1, 10)
    ]
    vs.add_chunks(chunks)
    retriever = RetrieverService(vs)
    
    # Retrieve top 5 diverse chunks
    selected = retriever.retrieve_diverse_for_generation(query="Concept", material_id="mat_div", top_k=5)
    assert len(selected) == 5
    seqs = [c.sequence for c in selected]
    # Must have varied sequences
    assert len(set(seqs)) == 5
    assert max(seqs) > 3, "Retriever should sample across pages/sections"


def test_material_isolation():
    """Verify that Material A and Material B do not cross-contaminate questions."""
    embed = MockEmbeddingProvider()
    vs = VectorStore(embed)
    
    # Material A (Cybersecurity)
    chunks_a = [
        DocumentChunk(material_id="mat_cyber", sequence=1, text="Cryptographic nonce tokens prevent replay attacks.", source_page=1),
    ]
    # Material B (Statistics)
    chunks_b = [
        DocumentChunk(material_id="mat_stats", sequence=1, text="Stratified sampling ensures balanced demographic representation.", source_page=1),
    ]
    vs.add_chunks(chunks_a)
    vs.add_chunks(chunks_b)
    retriever = RetrieverService(vs)
    
    gen = MCQGenerator(MockLLMProvider(), retriever)
    q_a = gen.generate_questions(query="Security", competency_code="CYBER", question_count=1, material_id="mat_cyber")
    q_b = gen.generate_questions(query="Sampling", competency_code="STATS", question_count=1, material_id="mat_stats")
    
    assert len(q_a) == 1
    assert len(q_b) == 1
    assert "Cryptographic" in q_a[0].explanation or "nonce" in q_a[0].explanation or "replay" in q_a[0].explanation
    assert "Stratified" in q_b[0].explanation or "sampling" in q_b[0].explanation or "demographic" in q_b[0].explanation


def test_edit_question_persistence_and_validation():
    """Verify editing question persists stem, options, Bloom, difficulty, and validates strictly."""
    client, database, settings = make_trainer_app()
    trainer = create_user(database, "edit_test@test.com", "TRAINER", "TRN-EDT")
    token = create_access_token(str(trainer["_id"]), settings)
    headers = {"Authorization": f"Bearer {token}"}
    mat = create_material(database, str(trainer["_id"]), "Cybersecurity_Guide.pdf")
    
    # Insert an existing generated question
    q_doc = {
        "_id": ObjectId(),
        "trainer_id": str(trainer["_id"]),
        "material_id": str(mat["_id"]),
        "competency_code": "DIGOV_CYBERSECURITY",
        "question": "Original question stem?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": "B",
        "explanation": "Original explanation.",
        "difficulty": "MEDIUM",
        "bloom_level": "UNDERSTAND",
        "source_document_id": str(mat["_id"]),
        "source_chunks": ["chunk_1"],
        "status": "GENERATED",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    database.trainer_questions.insert_one(q_doc)
    qid = str(q_doc["_id"])
    
    # Perform Edit
    edit_payload = {
        "question": "Updated security question: Which control mitigates session hijacking?",
        "options": [
            "HTTP Strict Transport Security (HSTS)",
            "Secure session cookies with HttpOnly and SameSite flags",
            "Disabling TLS certificate checking",
            "Storing credentials in browser localStorage",
        ],
        "correct_answer": "B",
        "explanation": "Updated explanation: HttpOnly prevents JavaScript access and SameSite limits cross-site transmission.",
        "bloom_level": "APPLY",
        "difficulty": "HARD",
        "competency_code": "DIGOV_CYBERSECURITY",
    }
    edit_resp = client.put(f"/api/v1/trainer/questions/{qid}", headers=headers, json=edit_payload)
    assert edit_resp.status_code == 200, edit_resp.text
    edited_data = edit_resp.json()
    assert edited_data["question"] == edit_payload["question"]
    assert edited_data["bloom_level"] == "APPLY"
    assert edited_data["difficulty"] == "HARD"
    assert edited_data["options"] == edit_payload["options"]
    assert edited_data["source_document_id"] == str(mat["_id"]), "Provenance must not be corrupted"
    assert edited_data["source_chunks"] == ["chunk_1"], "Source chunks must be preserved"
    
    # Verify persistence via direct DB check (simulating page reload)
    db_record = database.trainer_questions.find_one({"_id": q_doc["_id"]})
    assert db_record is not None
    assert db_record["question"] == edit_payload["question"]
    assert db_record["bloom_level"] == "APPLY"
    assert db_record["difficulty"] == "HARD"


def test_reject_question_lifecycle_and_persistence():
    """Verify rejecting a question persists status REJECTED and review_notes."""
    client, database, settings = make_trainer_app()
    trainer = create_user(database, "reject_test@test.com", "TRAINER", "TRN-REJ")
    token = create_access_token(str(trainer["_id"]), settings)
    headers = {"Authorization": f"Bearer {token}"}
    mat = create_material(database, str(trainer["_id"]), "Cybersecurity_Guide.pdf")
    
    q_doc = {
        "_id": ObjectId(),
        "trainer_id": str(trainer["_id"]),
        "material_id": str(mat["_id"]),
        "competency_code": "DIGOV_CYBERSECURITY",
        "question": "Question to be rejected?",
        "options": ["Opt 1", "Opt 2", "Opt 3", "Opt 4"],
        "correct_answer": "A",
        "explanation": "Explanation.",
        "difficulty": "MEDIUM",
        "bloom_level": "REMEMBER",
        "status": "GENERATED",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    database.trainer_questions.insert_one(q_doc)
    qid = str(q_doc["_id"])
    
    reject_payload = {
        "action": "REJECT",
        "review_notes": "Question too ambiguous and lacks domain rigor.",
    }
    resp = client.post(f"/api/v1/trainer/questions/{qid}/reject", headers=headers, json=reject_payload)
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "REJECTED"
    assert resp.json()["review_notes"] == reject_payload["review_notes"]
    
    # Verify DB persistence
    db_record = database.trainer_questions.find_one({"_id": q_doc["_id"]})
    assert db_record["status"] == "REJECTED"
    assert db_record["review_notes"] == reject_payload["review_notes"]


def test_status_all_filter_repository_fix():
    """Verify that status='ALL' returns all questions instead of querying MongoDB for status='ALL'."""
    client, database, settings = make_trainer_app()
    trainer = create_user(database, "filter_test@test.com", "TRAINER", "TRN-FLT")
    mat = create_material(database, str(trainer["_id"]), "Manual.pdf")
    
    # Insert one generated and one approved
    database.trainer_questions.insert_one({
        "_id": ObjectId(),
        "trainer_id": str(trainer["_id"]),
        "material_id": str(mat["_id"]),
        "status": "GENERATED",
        "question": "Q1",
    })
    database.trainer_questions.insert_one({
        "_id": ObjectId(),
        "trainer_id": str(trainer["_id"]),
        "material_id": str(mat["_id"]),
        "status": "APPROVED",
        "question": "Q2",
    })
    
    repo = TrainerRepository()
    # status="ALL" should return both
    results_all = repo.list_questions_by_material(database, str(mat["_id"]), str(trainer["_id"]), status="ALL")
    assert len(results_all) == 2
    
    # status=None should return both
    results_none = repo.list_questions_by_material(database, str(mat["_id"]), str(trainer["_id"]), status=None)
    assert len(results_none) == 2
    
    # status="APPROVED" should return 1
    results_app = repo.list_questions_by_material(database, str(mat["_id"]), str(trainer["_id"]), status="APPROVED")
    assert len(results_app) == 1
    assert results_app[0]["status"] == "APPROVED"
