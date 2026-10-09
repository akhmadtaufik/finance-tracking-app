from datetime import date
import io
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from httpx import AsyncClient
from PIL import Image
from google.api_core import exceptions as google_exceptions

from backend.app.services.ocr_service import ReceiptScanner, ReceiptScanException



class TestReceiptsSecurity:
    """Test receipt upload security and error handling endpoints."""

    async def test_upload_large_file(self, client: AsyncClient, auth_headers):
        """Test file larger than 5MB is rejected with 413 and structured code."""
        # Create a 6MB dummy file
        large_content = b"0" * (6 * 1024 * 1024)
        files = {"file": ("large_receipt.jpg", large_content, "image/jpeg")}

        response = await client.post(
            "/receipts/scan",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == 413
        data = response.json()
        assert data["code"] == "FILE_TOO_LARGE"
        assert "5MB" in data["detail"]
        assert "request_id" in data
        assert data["retryable"] is False
        assert data["action_hint"] == "retake_photo"

    async def test_upload_empty_file(self, client: AsyncClient, auth_headers):
        """Test empty file upload is rejected with 400 and EMPTY_FILE code."""
        files = {"file": ("empty.jpg", b"", "image/jpeg")}

        response = await client.post(
            "/receipts/scan",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "EMPTY_FILE"
        assert "kosong" in data["detail"].lower()
        assert "request_id" in data

    async def test_upload_invalid_mime_type(self, client: AsyncClient, auth_headers):
        """Test unsupported MIME type is rejected with 400 and INVALID_FILE_TYPE."""
        files = {"file": ("document.pdf", b"%PDF-1.4...", "application/pdf")}

        response = await client.post(
            "/receipts/scan",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "INVALID_FILE_TYPE"
        assert "request_id" in data

    async def test_upload_invalid_magic_bytes(self, client: AsyncClient, auth_headers):
        """Test text file renamed to .jpg is rejected with 415 and INVALID_MAGIC_BYTES."""
        fake_image = b"This is just a text file, not an image."
        files = {"file": ("fake_image.jpg", fake_image, "image/jpeg")}

        response = await client.post(
            "/receipts/scan",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == 415
        data = response.json()
        assert data["code"] == "INVALID_MAGIC_BYTES"
        assert "request_id" in data
        assert data["retryable"] is False

    async def test_ai_quota_exceeded_handling(self, client: AsyncClient, auth_headers):
        """Test AI quota exhaustion returns 429 with AI_QUOTA_EXCEEDED."""
        # Minimal valid 1x1 GIF / JPEG magic byte header for upload bypass
        valid_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00"
        files = {"file": ("receipt.jpg", valid_jpeg, "image/jpeg")}

        with patch("backend.app.routers.receipts.ReceiptScanner.scan_image", new_callable=AsyncMock) as mock_scan:
            mock_scan.side_effect = ReceiptScanException(
                message="Kuota harian scan AI telah habis. Silakan masukkan transaksi secara manual.",
                code="AI_QUOTA_EXCEEDED",
                status_code=429,
                retryable=False,
                action_hint="manual_input",
            )

            response = await client.post(
                "/receipts/scan",
                files=files,
                headers=auth_headers,
            )

            assert response.status_code == 429
            data = response.json()
            assert data["code"] == "AI_QUOTA_EXCEEDED"
            assert data["retryable"] is False
            assert data["action_hint"] == "manual_input"
            assert "request_id" in data

    async def test_ai_unreadable_image_handling(self, client: AsyncClient, auth_headers):
        """Test unreadable image returns 422 with AI_IMAGE_UNREADABLE."""
        valid_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00"
        files = {"file": ("blurry.jpg", valid_jpeg, "image/jpeg")}

        with patch("backend.app.routers.receipts.ReceiptScanner.scan_image", new_callable=AsyncMock) as mock_scan:
            mock_scan.side_effect = ReceiptScanException(
                message="Foto struk tidak terbaca atau terlalu buram.",
                code="AI_IMAGE_UNREADABLE",
                status_code=422,
                retryable=False,
                action_hint="retake_photo",
            )

            response = await client.post(
                "/receipts/scan",
                files=files,
                headers=auth_headers,
            )

            assert response.status_code == 422
            data = response.json()
            assert data["code"] == "AI_IMAGE_UNREADABLE"
            assert data["action_hint"] == "retake_photo"
            assert "request_id" in data

    async def test_ai_timeout_handling(self, client: AsyncClient, auth_headers):
        """Test AI timeout returns 504 with retryable=True."""
        valid_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00"
        files = {"file": ("receipt.jpg", valid_jpeg, "image/jpeg")}

        with patch("backend.app.routers.receipts.ReceiptScanner.scan_image", new_callable=AsyncMock) as mock_scan:
            mock_scan.side_effect = ReceiptScanException(
                message="Waktu pemrosesan AI habis (timeout).",
                code="AI_TIMEOUT",
                status_code=504,
                retryable=True,
                action_hint="retry",
            )

            response = await client.post(
                "/receipts/scan",
                files=files,
                headers=auth_headers,
            )

            assert response.status_code == 504
            data = response.json()
            assert data["code"] == "AI_TIMEOUT"
            assert data["retryable"] is True
            assert data["action_hint"] == "retry"
            assert "request_id" in data

    async def test_scan_success_response(self, client: AsyncClient, auth_headers):
        """Test successful receipt scanning extracts items and metadata."""
        valid_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00"
        files = {"file": ("receipt.jpg", valid_jpeg, "image/jpeg")}

        mock_result = {
            "date": "2026-10-09",
            "total_amount": 55000,
            "items": [
                {"name": "Susu UHT", "price": 20000, "category_guess": "Food"},
                {"name": "Roti Gandum", "price": 35000, "category_guess": "Food"},
            ],
        }

        with patch("backend.app.routers.receipts.ReceiptScanner.scan_image", new_callable=AsyncMock) as mock_scan:
            mock_scan.return_value = mock_result

            response = await client.post(
                "/receipts/scan",
                files=files,
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["date"] == "2026-10-09"
            assert float(data["total_amount"]) == 55000
            assert len(data["items"]) == 2
            assert data["items"][0]["name"] == "Susu UHT"
            assert float(data["items"][0]["price"]) == 20000

    async def test_scan_empty_date_falls_back_to_today(self, client: AsyncClient, auth_headers):
        """Test missing or empty receipt date defaults to today's date."""
        valid_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00"
        files = {"file": ("receipt.jpg", valid_jpeg, "image/jpeg")}

        mock_result = {
            "date": "",
            "total_amount": 171262,
            "items": [
                {"name": "Item A", "price": 10000, "category_guess": "Food"},
            ],
        }

        with patch("backend.app.routers.receipts.ReceiptScanner.scan_image", new_callable=AsyncMock) as mock_scan:
            mock_scan.return_value = mock_result

            response = await client.post(
                "/receipts/scan",
                files=files,
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["date"] == str(date.today())
            assert float(data["total_amount"]) == 171262
            assert len(data["items"]) == 1

    async def test_scan_indonesian_date_format(self, client: AsyncClient, auth_headers):
        """Test Indonesian DD/MM/YYYY date format parses to ISO YYYY-MM-DD."""
        valid_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00"
        files = {"file": ("receipt.jpg", valid_jpeg, "image/jpeg")}

        mock_result = {
            "date": "23/02/2026",
            "total_amount": 50000,
            "items": [
                {"name": "Kopi", "price": 50000, "category_guess": "Food"},
            ],
        }

        with patch("backend.app.routers.receipts.ReceiptScanner.scan_image", new_callable=AsyncMock) as mock_scan:
            mock_scan.return_value = mock_result

            response = await client.post(
                "/receipts/scan",
                files=files,
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["date"] == "2026-02-23"

    async def test_scan_unparseable_date_falls_back_to_today(self, client: AsyncClient, auth_headers):
        """Test invalid/unparseable date string gracefully falls back to today's date."""
        valid_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00"
        files = {"file": ("receipt.jpg", valid_jpeg, "image/jpeg")}

        mock_result = {
            "date": "unreadable_date",
            "total_amount": 35000,
            "items": [
                {"name": "Teh", "price": 35000, "category_guess": "Food"},
            ],
        }

        with patch("backend.app.routers.receipts.ReceiptScanner.scan_image", new_callable=AsyncMock) as mock_scan:
            mock_scan.return_value = mock_result

            response = await client.post(
                "/receipts/scan",
                files=files,
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["date"] == str(date.today())

    def test_in_memory_image_optimization(self):
        """Test large images are resized in-memory strictly to <= 1200px."""
        # Create a large dummy image in RAM (2400 x 1600)
        img = Image.new("RGB", (2400, 1600), color=(200, 200, 200))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        raw_bytes = buf.getvalue()

        opt_bytes, opt_mime = ReceiptScanner._optimize_image_bytes(raw_bytes, "image/jpeg")
        assert opt_mime == "image/jpeg"
        assert len(opt_bytes) < len(raw_bytes)

        # Verify resized dimensions
        with Image.open(io.BytesIO(opt_bytes)) as result_img:
            assert max(result_img.width, result_img.height) <= 1200
            assert result_img.format == "JPEG"

    async def test_ocr_service_fallback_on_primary_quota_exhausted(self):
        """Test fallback model is invoked when primary model hits quota limit."""
        scanner = ReceiptScanner()

        mock_fallback_response = MagicMock()
        mock_fallback_response.text = '{"date": "2026-10-09", "total_amount": 25000, "items": [{"name": "Roti", "price": 25000, "category_guess": "Food"}]}'

        # Mock primary to fail with ResourceExhausted, fallback to succeed
        with patch.object(scanner.primary_model, "generate_content", side_effect=google_exceptions.ResourceExhausted("quota exhausted")), \
             patch.object(scanner.fallback_model, "generate_content", return_value=mock_fallback_response):

            dummy_img = Image.new("RGB", (100, 100), color="white")
            buf = io.BytesIO()
            dummy_img.save(buf, format="JPEG")

            result = await scanner.scan_image(buf.getvalue(), "image/jpeg")
            assert result["date"] == "2026-10-09"
            assert result["total_amount"] == 25000
            assert len(result["items"]) == 1
            assert result["items"][0]["name"] == "Roti"

    async def test_ocr_service_fallback_on_primary_deadline_exceeded(self):
        """Test fallback model is invoked when primary model times out."""
        scanner = ReceiptScanner()

        mock_fallback_response = MagicMock()
        mock_fallback_response.text = '{"date": "2026-10-09", "total_amount": 40000, "items": [{"name": "Kopi", "price": 40000, "category_guess": "Food"}]}'

        # Mock primary to fail with DeadlineExceeded, fallback to succeed
        with patch.object(scanner.primary_model, "generate_content", side_effect=google_exceptions.DeadlineExceeded("timeout")), \
             patch.object(scanner.fallback_model, "generate_content", return_value=mock_fallback_response):

            dummy_img = Image.new("RGB", (100, 100), color="white")
            buf = io.BytesIO()
            dummy_img.save(buf, format="JPEG")

            result = await scanner.scan_image(buf.getvalue(), "image/jpeg")
            assert result["date"] == "2026-10-09"
            assert result["total_amount"] == 40000
            assert len(result["items"]) == 1
            assert result["items"][0]["name"] == "Kopi"


