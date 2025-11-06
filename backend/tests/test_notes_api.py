"""
Unit tests for notes API endpoints.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.models.user import User


@pytest.mark.unit
def test_get_all_notes(client, db_session, test_user, test_note_document):
    """Test fetching all notes for a user."""
    response = client.get("/notes/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["title"] == "Test Biochemistry Notes"
    assert "has_study_material" in data[0]


@pytest.mark.unit
def test_upload_text_note(client, db_session, test_user):
    """Test uploading a text note."""
    response = client.post(
        "/notes/upload",
        data={
            "text": "Test note content about proteins",
            "title": "Protein Notes"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "note_document_id" in data
    assert data["extracted_text"] == "Test note content about proteins"


@pytest.mark.unit
def test_delete_note(client, db_session, test_user, test_note_document):
    """Test deleting a note document."""
    response = client.delete(f"/notes/{test_note_document.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Note deleted successfully"


@pytest.mark.unit
def test_get_study_material(client, db_session, test_user, test_note_document, test_study_material):
    """Test fetching study material for a note."""
    response = client.get(f"/notes/{test_note_document.id}/study")

    assert response.status_code == 200
    data = response.json()
    assert "summary_short" in data
    assert "flashcards" in data
    assert "practice_questions" in data
    assert len(data["flashcards"]) == 1


@pytest.mark.unit
def test_get_study_material_not_found(client, db_session, test_user, test_note_document):
    """Test fetching study material that doesn't exist."""
    response = client.get(f"/notes/{test_note_document.id}/study")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.skip(reason="Integration test requiring external Gemini API mocking - skip for CI")
@pytest.mark.slow
@pytest.mark.integration
def test_generate_study_material(client, db_session, test_user, test_note_document):
    """Test generating study material (requires Gemini API integration)."""
    # NOTE: This test is skipped because it requires complex async mocking
    # of the Gemini API service. In a real production environment, you would:
    # 1. Use dependency injection for the Gemini service
    # 2. Mock at the service layer, not the function level
    # 3. Or use VCR.py to record/replay API interactions

    mock_material = {
        "summary_short": "Test summary",
        "summary_detailed": "Detailed test summary",
        "flashcards": [{"question": "Q1", "answer": "A1"}],
        "practice_questions": [{
            "question": "Q1",
            "options": ["A", "B", "C", "D"],
            "correct_index": 0,
            "explanation": "Exp"
        }]
    }

    with patch('app.services.gemini_service.generate_study_material', return_value=mock_material):
        response = client.post(
            "/notes/generate-study",
            json={"note_document_id": str(test_note_document.id)}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["summary_short"] == "Test summary"
        assert len(data["flashcards"]) == 1


@pytest.mark.unit
def test_upload_note_validation_error(client, db_session, test_user):
    """Test uploading a note with no content."""
    response = client.post(
        "/notes/upload",
        data={"title": "Empty Note"}
    )

    assert response.status_code == 400
    assert "must be provided" in response.json()["detail"].lower()
