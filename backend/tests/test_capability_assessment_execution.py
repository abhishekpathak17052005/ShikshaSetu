"""Tests for capability assessment execution (Phase 2)."""
from datetime import UTC, datetime

from bson import ObjectId
import pytest

from app.capability_assessments import repository, service
from app.capability_assessments.scoring import (
    calculate_assessment_percentage,
    calculate_normalized_score_from_percentage,
    calculate_question_score,
)


class TestCapabilityAssessmentScoring:
    """Test scoring functions."""

    def test_calculate_question_score_correct(self):
        """Test MCQ scoring for correct answer."""
        score = calculate_question_score("B", "B")
        assert score == 1.0

    def test_calculate_question_score_incorrect(self):
        """Test MCQ scoring for incorrect answer."""
        score = calculate_question_score("A", "B")
        assert score == 0.0

    def test_calculate_assessment_percentage_all_correct(self):
        """Test percentage calculation when all correct."""
        answers = [
            {"question_id": "Q1", "is_correct": True},
            {"question_id": "Q2", "is_correct": True},
            {"question_id": "Q3", "is_correct": True},
        ]
        percentage = calculate_assessment_percentage(answers)
        assert percentage == 1.0

    def test_calculate_assessment_percentage_half_correct(self):
        """Test percentage calculation with 50% correct."""
        answers = [
            {"question_id": "Q1", "is_correct": True},
            {"question_id": "Q2", "is_correct": False},
        ]
        percentage = calculate_assessment_percentage(answers)
        assert percentage == 0.5

    def test_calculate_assessment_percentage_all_incorrect(self):
        """Test percentage calculation when all incorrect."""
        answers = [
            {"question_id": "Q1", "is_correct": False},
            {"question_id": "Q2", "is_correct": False},
        ]
        percentage = calculate_assessment_percentage(answers)
        assert percentage == 0.0

    def test_calculate_assessment_percentage_empty(self):
        """Test percentage calculation with empty answers."""
        percentage = calculate_assessment_percentage([])
        assert percentage == 0.0

    def test_calculate_normalized_score_0_percent(self):
        """Test 0% maps to 1."""
        score = calculate_normalized_score_from_percentage(0.0)
        assert score == 1.0

    def test_calculate_normalized_score_50_percent(self):
        """Test 50% maps to 3."""
        score = calculate_normalized_score_from_percentage(0.5)
        assert score == 3.0

    def test_calculate_normalized_score_100_percent(self):
        """Test 100% maps to 5."""
        score = calculate_normalized_score_from_percentage(1.0)
        assert score == 5.0

    def test_calculate_normalized_score_75_percent(self):
        """Test 75% maps to 4."""
        score = calculate_normalized_score_from_percentage(0.75)
        assert score == 4.0


class FakeCollection:
    """Fake MongoDB collection for testing."""
    
    def __init__(self):
        self.documents = []
    
    def find_one(self, query):
        for doc in self.documents:
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None
    
    def find(self, query):
        result = [doc for doc in self.documents if all(doc.get(k) == v for k, v in query.items())]
        return FakeCursor(result)
    
    def insert_one(self, doc):
        doc["_id"] = doc.get("_id", ObjectId())
        self.documents.append(doc)
        class Result:
            def __init__(self, oid):
                self.inserted_id = oid
        return Result(doc["_id"])
    
    def insert_many(self, docs):
        ids = []
        for doc in docs:
            doc["_id"] = doc.get("_id", ObjectId())
            self.documents.append(doc)
            ids.append(doc["_id"])
        class Result:
            def __init__(self, oids):
                self.inserted_ids = oids
        return Result(ids)
    
    def find_one_and_update(self, query, update, return_document=False):
        doc = self.find_one(query)
        if doc is None:
            return None
        if "$set" in update:
            doc.update(update["$set"])
        return doc if return_document else None
    
    def count_documents(self, query):
        return len([d for d in self.documents if all(d.get(k) == v for k, v in query.items())])
    
    def aggregate(self, pipeline):
        # Simplified aggregation for $sample
        if pipeline and pipeline[0].get("$match"):
            query = pipeline[0]["$match"]
            matching = [d for d in self.documents if all(d.get(k) == v for k, v in query.items())]
        else:
            matching = self.documents
        
        if pipeline and any("$sample" in stage for stage in pipeline):
            return matching[:1]  # Return first for testing
        return matching
    
    def update_one(self, query, update):
        doc = self.find_one(query)
        if doc is not None and "$set" in update:
            doc.update(update["$set"])


class FakeCursor:
    """Fake MongoDB cursor."""
    
    def __init__(self, docs):
        self.docs = docs
        self.sort_order = None
        self.limit_count = None
    
    def sort(self, field, direction):
        if direction == -1:
            self.docs.sort(key=lambda d: d.get(field, ""), reverse=True)
        else:
            self.docs.sort(key=lambda d: d.get(field, ""))
        return self
    
    def limit(self, count):
        self.limit_count = count
        return self
    
    def __iter__(self):
        return iter(self.docs[:self.limit_count] if self.limit_count else self.docs)


class FakeDatabase:
    """Fake MongoDB database for testing."""
    
    def __init__(self):
        self.capability_assessments = FakeCollection()
        self.question_bank = FakeCollection()
        self.assessment_configurations = FakeCollection()
        self.competencies = FakeCollection()
        self.competency_profiles = FakeCollection()
        self.competency_evidence = FakeCollection()
        self.assessments = FakeCollection()


class TestCapabilityAssessmentRepository:
    """Test repository functions."""
    
    def test_insert_capability_assessment(self):
        """Test inserting a capability assessment."""
        db = FakeDatabase()
        user_id = ObjectId()
        
        doc = {
            "_id": ObjectId(),
            "user_id": user_id,
            "competency_code": "TECH_SQL",
            "questions": [{"question_id": "Q1", "question_text": "What is SQL?"}],
            "status": "IN_PROGRESS",
        }
        
        assessment_id = repository.insert_capability_assessment(db, doc)
        assert assessment_id is not None
        assert len(db.capability_assessments.documents) == 1
    
    def test_get_capability_assessment_for_user(self):
        """Test retrieving assessment with ownership check."""
        db = FakeDatabase()
        user_id = ObjectId()
        assessment_id = ObjectId()
        
        doc = {
            "_id": assessment_id,
            "user_id": user_id,
            "competency_code": "TECH_SQL",
            "status": "IN_PROGRESS",
        }
        db.capability_assessments.insert_one(doc)
        
        result = repository.get_capability_assessment_for_user(
            db, str(assessment_id), str(user_id)
        )
        assert result is not None
        assert result["competency_code"] == "TECH_SQL"
    
    def test_get_capability_assessment_for_user_wrong_user(self):
        """Test that ownership check prevents access."""
        db = FakeDatabase()
        user_id = ObjectId()
        other_user = ObjectId()
        assessment_id = ObjectId()
        
        doc = {
            "_id": assessment_id,
            "user_id": user_id,
            "competency_code": "TECH_SQL",
        }
        db.capability_assessments.insert_one(doc)
        
        result = repository.get_capability_assessment_for_user(
            db, str(assessment_id), str(other_user)
        )
        assert result is None
    
    def test_get_in_progress_assessment_for_user_and_competency(self):
        """Test checking for IN_PROGRESS assessment."""
        db = FakeDatabase()
        user_id = ObjectId()
        
        doc = {
            "_id": ObjectId(),
            "user_id": user_id,
            "competency_code": "TECH_SQL",
            "status": "IN_PROGRESS",
        }
        db.capability_assessments.insert_one(doc)
        
        result = repository.get_in_progress_assessment_for_user_and_competency(
            db, str(user_id), "TECH_SQL"
        )
        assert result is not None
        assert result["status"] == "IN_PROGRESS"
    
    def test_get_in_progress_assessment_not_found(self):
        """Test when no IN_PROGRESS assessment exists."""
        db = FakeDatabase()
        user_id = ObjectId()
        
        result = repository.get_in_progress_assessment_for_user_and_competency(
            db, str(user_id), "TECH_SQL"
        )
        assert result is None
    
    def test_update_assessment_status_and_submit(self):
        """Test updating assessment status atomically."""
        db = FakeDatabase()
        user_id = ObjectId()
        assessment_id = ObjectId()
        
        doc = {
            "_id": assessment_id,
            "user_id": user_id,
            "status": "IN_PROGRESS",
            "answers": [],
        }
        db.capability_assessments.insert_one(doc)
        
        update = {
            "status": "SUBMITTED",
            "answers": [{"question_id": "Q1", "selected_answer": "B"}],
        }
        
        result = repository.update_assessment_status_and_submit(
            db, str(assessment_id), str(user_id), update
        )
        assert result is not None
        assert result["status"] == "SUBMITTED"
    
    def test_update_assessment_status_already_submitted(self):
        """Test that update fails if already submitted."""
        db = FakeDatabase()
        user_id = ObjectId()
        assessment_id = ObjectId()
        
        doc = {
            "_id": assessment_id,
            "user_id": user_id,
            "status": "SUBMITTED",  # Already submitted
        }
        db.capability_assessments.insert_one(doc)
        
        update = {"status": "SUBMITTED"}
        result = repository.update_assessment_status_and_submit(
            db, str(assessment_id), str(user_id), update
        )
        # Should return None because status is not IN_PROGRESS
        assert result is None
    
    def test_get_user_capability_assessments(self):
        """Test listing assessments for a user."""
        db = FakeDatabase()
        user_id = ObjectId()
        
        doc1 = {
            "_id": ObjectId(),
            "user_id": user_id,
            "competency_code": "TECH_SQL",
            "status": "SUBMITTED",
            "created_at": datetime.now(UTC),
        }
        doc2 = {
            "_id": ObjectId(),
            "user_id": user_id,
            "competency_code": "TECH_PYTHON",
            "status": "IN_PROGRESS",
            "created_at": datetime.now(UTC),
        }
        db.capability_assessments.insert_one(doc1)
        db.capability_assessments.insert_one(doc2)
        
        result = repository.get_user_capability_assessments(db, str(user_id))
        assert len(result) == 2
    
    def test_get_user_capability_assessments_filter_by_competency(self):
        """Test listing with competency filter."""
        db = FakeDatabase()
        user_id = ObjectId()
        
        doc1 = {
            "_id": ObjectId(),
            "user_id": user_id,
            "competency_code": "TECH_SQL",
            "created_at": datetime.now(UTC),
        }
        doc2 = {
            "_id": ObjectId(),
            "user_id": user_id,
            "competency_code": "TECH_PYTHON",
            "created_at": datetime.now(UTC),
        }
        db.capability_assessments.insert_one(doc1)
        db.capability_assessments.insert_one(doc2)
        
        result = repository.get_user_capability_assessments(
            db, str(user_id), competency_code="TECH_SQL"
        )
        assert len(result) == 1
        assert result[0]["competency_code"] == "TECH_SQL"


class TestCapabilityAssessmentIntegration:
    """Integration tests for complete flows."""
    
    def test_assessment_creation_requires_valid_config(self):
        """Test that assessment creation validates config exists."""
        db = FakeDatabase()
        user_id = ObjectId()
        
        # No configuration in database
        with pytest.raises(Exception):  # HTTPException
            service.create_capability_assessment(db, str(user_id), "NONEXISTENT")
    
    def test_assessment_scoring_binary(self):
        """Test that assessment scoring is binary (correct/incorrect)."""
        # Test with 3 answers: 2 correct, 1 incorrect
        answers = [
            {"question_id": "Q1", "is_correct": True},
            {"question_id": "Q2", "is_correct": True},
            {"question_id": "Q3", "is_correct": False},
        ]
        
        percentage = calculate_assessment_percentage(answers)
        assert percentage == pytest.approx(2/3, abs=0.01)
        
        normalized = calculate_normalized_score_from_percentage(percentage)
        assert 3.0 <= normalized <= 4.0  # Should be between 3 and 4
    
    def test_assessment_ownership_validation(self):
        """Test that only owner can access assessment."""
        db = FakeDatabase()
        owner_id = ObjectId()
        other_user = ObjectId()
        assessment_id = ObjectId()
        
        doc = {
            "_id": assessment_id,
            "user_id": owner_id,
            "competency_code": "TECH_SQL",
            "questions": [],
            "status": "IN_PROGRESS",
        }
        db.capability_assessments.insert_one(doc)
        
        # Owner can access
        result = repository.get_capability_assessment_for_user(
            db, str(assessment_id), str(owner_id)
        )
        assert result is not None
        
        # Other user cannot access
        result = repository.get_capability_assessment_for_user(
            db, str(assessment_id), str(other_user)
        )
        assert result is None
    
    def test_duplicate_submission_prevention(self):
        """Test that duplicate submissions are prevented."""
        db = FakeDatabase()
        user_id = ObjectId()
        assessment_id = ObjectId()
        
        doc = {
            "_id": assessment_id,
            "user_id": user_id,
            "status": "IN_PROGRESS",
        }
        db.capability_assessments.insert_one(doc)
        
        # First submission succeeds
        update = {"status": "SUBMITTED", "answers": []}
        result1 = repository.update_assessment_status_and_submit(
            db, str(assessment_id), str(user_id), update
        )
        assert result1 is not None
        assert result1["status"] == "SUBMITTED"
        
        # Second submission fails (status not IN_PROGRESS)
        update2 = {"status": "SUBMITTED", "answers": []}
        result2 = repository.update_assessment_status_and_submit(
            db, str(assessment_id), str(user_id), update2
        )
        assert result2 is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
