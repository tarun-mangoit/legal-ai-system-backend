import pytest
import uuid
import io
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.case_document import DocumentCategory
from app.main import app

@pytest.mark.asyncio
async def test_upload_document(client: TestClient, db: AsyncSession, test_user_token_headers, test_case):
    # This requires creating a test case first, which should be done in a fixture or earlier in the test
    # Assuming test_case fixture provides a valid case
    file_content = b"test content"
    file = io.BytesIO(file_content)
    file.name = "test.txt"

    response = client.post(
        "/api/v1/documents/upload",
        headers=test_user_token_headers,
        data={
            "case_id": str(test_case.id),
            "category": DocumentCategory.OTHER.value,
        },
        files={"file": ("test.txt", file, "text/plain")}
    )
    
    # Since text/plain is not allowed, this should fail with 400
    assert response.status_code == 400
    assert "File type not supported" in response.json()["detail"]

    # Test with valid file
    valid_file = io.BytesIO(b"%PDF-1.4 test")
    valid_file.name = "test.pdf"
    
    response = client.post(
        "/api/v1/documents/upload",
        headers=test_user_token_headers,
        data={
            "case_id": str(test_case.id),
            "category": DocumentCategory.OTHER.value,
        },
        files={"file": ("test.pdf", valid_file, "application/pdf")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["original_filename"] == "test.pdf"
    assert data["extension"] == ".pdf"
    assert data["mime_type"] == "application/pdf"
    
    # Test duplicate
    duplicate_file = io.BytesIO(b"%PDF-1.4 test")
    duplicate_file.name = "test.pdf"
    
    response = client.post(
        "/api/v1/documents/upload",
        headers=test_user_token_headers,
        data={
            "case_id": str(test_case.id),
            "category": DocumentCategory.OTHER.value,
        },
        files={"file": ("test.pdf", duplicate_file, "application/pdf")}
    )
    
    assert response.status_code == 409
    assert "Duplicate file exists" in response.json()["detail"]
