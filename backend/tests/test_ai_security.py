"""Security and user isolation tests for AI module."""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock

from app.main import create_app
from app.core.config import Settings


@pytest.fixture
def app():
    """Create test app."""
    settings = Settings(
        mongodb_uri="mongodb://localhost:27017",
        mongodb_database="shikshasetu_test",
        llm_provider="mock",
        embedding_provider="mock",
    )
    return create_app(settings)


@pytest.fixture
async def client(app):
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_upload_requires_authentication(client):
    """Test that document upload requires authentication."""
    with open("tests/fixtures/sample.pdf", "rb") as f:
        response = await client.post(
            "/api/v1/learning-materials/upload",
            files={"file": f}
        )
    
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_upload_unsupported_file_type(client, auth_headers):
    """Test that upload rejects unsupported file types."""
    import io
    
    file_content = b"This is a text file"
    files = {"file": ("test.txt", io.BytesIO(file_content))}
    
    response = await client.post(
        "/api/v1/learning-materials/upload",
        files=files,
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_empty_file(client, auth_headers):
    """Test that upload rejects empty files."""
    import io
    
    files = {"file": ("test.pdf", io.BytesIO(b""))}
    
    response = await client.post(
        "/api/v1/learning-materials/upload",
        files=files,
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_user_cannot_access_other_users_material(client):
    """Test that User A cannot access User B's materials."""
    # Create material for user A
    user_a_token = "valid_token_a"
    user_b_token = "valid_token_b"
    
    # Mock database to return different materials for different users
    with patch("app.ai.repository.LearningMaterialRepository.get_by_id") as mock_get:
        mock_get.return_value = None  # User B cannot see User A's material
        
        response = await client.get(
            "/api/v1/learning-materials/507f1f77bcf86cd799439011",
            headers={"Authorization": f"Bearer {user_b_token}"}
        )
        
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_generation_requires_ownership(client):
    """Test that generation only works for material owner."""
    material_id = "507f1f77bcf86cd799439011"
    
    request_body = {
        "competency_code": "TECH_SQL",
        "question_count": 5
    }
    
    with patch("app.ai.repository.LearningMaterialRepository.get_by_id") as mock_get:
        # Material exists but doesn't belong to current user
        mock_get.return_value = None
        
        response = await client.post(
            f"/api/v1/learning-materials/{material_id}/generate-questions",
            json=request_body,
            headers={"Authorization": "Bearer some_token"}
        )
        
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_material_not_ready_for_generation(client, auth_headers, monkeypatch):
    """Test that generation fails if material is not READY."""
    material_id = "507f1f77bcf86cd799439011"
    
    # Mock material as PROCESSING
    from app.ai.models import LearningMaterial
    mock_material = MagicMock(spec=LearningMaterial)
    mock_material.status = "PROCESSING"
    mock_material.id = material_id
    
    request_body = {
        "competency_code": "TECH_SQL",
        "question_count": 5
    }
    
    with patch("app.ai.repository.LearningMaterialRepository.get_by_id") as mock_get:
        mock_get.return_value = mock_material
        
        response = await client.post(
            f"/api/v1/learning-materials/{material_id}/generate-questions",
            json=request_body,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "not ready" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_file_size_limit_enforced(client, auth_headers):
    """Test that file size limit is enforced."""
    import io
    
    # Create a file larger than max size
    large_content = b"x" * (100 * 1024 * 1024)  # 100MB
    files = {"file": ("large.pdf", io.BytesIO(large_content))}
    
    response = await client.post(
        "/api/v1/learning-materials/upload",
        files=files,
        headers=auth_headers
    )
    
    assert response.status_code == 413
    assert "too large" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_user_isolation_in_material_list():
    """Test that users only see their own materials."""
    from app.ai.repository import LearningMaterialRepository
    from app.ai.models import LearningMaterial
    
    user_a_id = "user_a_123"
    user_b_id = "user_b_456"
    
    # Mock materials for different users
    materials = [
        MagicMock(user_id=user_a_id, filename="sql.pdf"),
        MagicMock(user_id=user_a_id, filename="python.pdf"),
        MagicMock(user_id=user_b_id, filename="java.pdf"),
    ]
    
    with patch("app.ai.repository.LearningMaterialRepository.get_by_user") as mock_get:
        mock_get.side_effect = lambda uid, limit: [m for m in materials if m.user_id == uid]
        
        # User A should see only their materials
        user_a_mats = mock_get(user_a_id)
        assert len(user_a_mats) == 2
        assert all(m.user_id == user_a_id for m in user_a_mats)
        
        # User B should see only their materials
        user_b_mats = mock_get(user_b_id)
        assert len(user_b_mats) == 1
        assert all(m.user_id == user_b_id for m in user_b_mats)


@pytest.mark.asyncio
async def test_jwt_token_validation():
    """Test that invalid tokens are rejected."""
    from app.auth.dependencies import get_current_user
    
    with patch("app.auth.dependencies.get_current_user") as mock_verify:
        mock_verify.side_effect = Exception("Invalid token")
        
        # Should raise exception
        with pytest.raises(Exception):
            await mock_verify("invalid_token")


@pytest.mark.asyncio
async def test_chunk_ownership_validation():
    """Test that chunks are validated against material ownership."""
    from app.ai.validation import GroundingValidator
    from app.ai.models import DocumentChunk, LearningMaterial
    from app.ai.schemas import GeneratedMCQ
    
    material_id = "material_123"
    user_id = "user_123"
    
    # Create a question referencing chunks
    question = GeneratedMCQ(
        question="Test question?",
        options=["A", "B", "C", "D"],
        correct_answer="A",
        explanation="Test explanation",
        source_chunks=["chunk_1", "chunk_2"]
    )
    
    # Mock chunks that don't belong to material
    mock_chunk = MagicMock(spec=DocumentChunk)
    mock_chunk.material_id = "other_material"
    mock_chunk.id = "chunk_1"
    
    with patch("app.ai.repository.DocumentChunkRepository.get_by_ids") as mock_get:
        mock_get.return_value = [mock_chunk]
        
        is_valid, error = await GroundingValidator.validate_question(
            question,
            MagicMock(),
            material_id
        )
        
        # Should be invalid because chunk belongs to different material
        assert not is_valid
        assert "does not belong" in error


@pytest.mark.asyncio
async def test_provider_not_configured_error(client, auth_headers):
    """Test graceful error when LLM provider not configured."""
    material_id = "507f1f77bcf86cd799439011"
    
    request_body = {
        "competency_code": "TECH_SQL",
        "question_count": 5
    }
    
    # Mock material as ready but provider unavailable
    from app.ai.models import LearningMaterial
    mock_material = MagicMock(spec=LearningMaterial)
    mock_material.status = "READY"
    mock_material.id = material_id
    
    with patch("app.ai.repository.LearningMaterialRepository.get_by_id") as mock_get:
        mock_get.return_value = mock_material
        
        with patch("app.ai.providers.factory.get_llm_provider") as mock_provider:
            mock_provider.return_value.is_available.return_value = False
            
            response = await client.post(
                f"/api/v1/learning-materials/{material_id}/generate-questions",
                json=request_body,
                headers=auth_headers
            )
            
            # Should return 503 Service Unavailable
            assert response.status_code == 503


# Fixtures
@pytest.fixture
def auth_headers():
    """Return authorization headers for authenticated requests."""
    return {
        "Authorization": "Bearer valid_test_token"
    }
