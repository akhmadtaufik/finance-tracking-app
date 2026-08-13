import pytest
from httpx import AsyncClient

class TestReceiptsSecurity:
    """Test receipt upload security endpoints."""
    
    async def test_upload_large_file(self, client: AsyncClient, auth_headers):
        """Test file larger than 5MB is rejected with 413."""
        # Create a 6MB dummy file
        large_content = b"0" * (6 * 1024 * 1024)
        files = {"file": ("large_receipt.jpg", large_content, "image/jpeg")}
        
        response = await client.post(
            "/receipts/scan",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == 413
        assert "exceeds the 5MB limit" in response.text

    async def test_upload_invalid_magic_bytes(self, client: AsyncClient, auth_headers):
        """Test text file renamed to .jpg is rejected with 415."""
        # Text content but pretending to be JPEG
        fake_image = b"This is just a text file, not an image."
        files = {"file": ("fake_image.jpg", fake_image, "image/jpeg")}
        
        response = await client.post(
            "/receipts/scan",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == 415
        assert "Malicious file signature detected" in response.text
