"""
Receipt Scanner Service using Google Gemini Flash Vision.

This service handles receipt image processing and extraction of
structured data (items, prices, dates) using AI vision capabilities.

Uses Gemini's native Structured Outputs (response_schema) to guarantee
100% valid JSON and lock the response keys, eliminating JSONDecodeError
and schema hallucination issues.
"""

import asyncio
import io
import json
import logging
import time
from typing import Optional

from PIL import Image
import typing_extensions as typing

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from fastapi import status


from ..core.config import settings
from ..core.exceptions import AppException
from ..core.logging_config import request_id_ctx

logger = logging.getLogger("fintrack.ocr")


class ReceiptScanException(AppException):
    """Exception for receipt scanning errors with user-friendly metadata."""

    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        retryable: bool = False,
        action_hint: Optional[str] = None,
    ):
        self.retryable = retryable
        self.action_hint = action_hint
        super().__init__(message=message, code=code, status_code=status_code)


# ──────────────────────────────────────────────
#  Structured Output Schemas (TypedDict)
# ──────────────────────────────────────────────


class ReceiptItem(typing.TypedDict):
    """Schema for a single receipt line-item."""

    name: str
    price: int
    category_guess: str


class ExpectedReceipt(typing.TypedDict):
    """Top-level schema enforced on every Gemini response."""

    date: str
    total_amount: int
    items: list[ReceiptItem]


class ReceiptScanner:
    """
    Receipt scanner using Google Gemini Flash Vision model.

    Extracts structured data from receipt images including:
    - Purchased items and their prices
    - Transaction date
    - Total amount
    - Category guesses for each item

    Uses `response_schema` to enforce output shape at the API level,
    preventing prompt drift and JSON formatting errors.
    """

    SYSTEM_PROMPT = """Analyze this shopping receipt image. Extract every purchased item, its final price, and the transaction date.
    Attempt to guess the category based on the item name.
Rules:
- Date should be in YYYY-MM-DD format.
- Indonesian receipts commonly print dates as DD-MM-YY (e.g. 23-02-26 means 23 Feb 2026, NOT 2023-02-26). Always interpret two-digit years as 20XX. When ambiguous, prefer DD-MM-YY over YY-MM-DD.
- Prices should be strictly numeric.
- Category must be one of: Food, Transport, Shopping, Entertainment, Bills, Health, Hygiene, Education, Other."""

    def __init__(self):
        """Initialize primary and fallback Gemini models."""
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.primary_model_name = getattr(settings, "GEMINI_PRIMARY_MODEL", "gemini-3.8-flash")
        self.fallback_model_name = getattr(settings, "GEMINI_FALLBACK_MODEL", "gemini-3.6-flash")
        self.primary_model = genai.GenerativeModel(self.primary_model_name)
        self.fallback_model = genai.GenerativeModel(self.fallback_model_name)

    @staticmethod
    def _optimize_image_bytes(image_bytes: bytes, mime_type: str = "image/jpeg") -> tuple[bytes, str]:
        """
        Optimize receipt image strictly in-memory (RAM) to minimize vision tokens.
        Never writes files to disk. Uses io.BytesIO buffer.
        """
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                max_dim = getattr(settings, "OCR_MAX_IMAGE_DIMENSION", 1200)
                quality = getattr(settings, "OCR_IMAGE_QUALITY", 85)

                # Resize if image exceeds maximum dimension
                if img.width > max_dim or img.height > max_dim:
                    ratio = min(max_dim / img.width, max_dim / img.height)
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    resized = img.resize(new_size, Image.Resampling.LANCZOS)
                    buffer = io.BytesIO()
                    resized.save(buffer, format="JPEG", quality=quality, optimize=True)
                    return buffer.getvalue(), "image/jpeg"
                elif mime_type not in ("image/jpeg", "image/png", "image/webp"):
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    buffer = io.BytesIO()
                    img.save(buffer, format="JPEG", quality=quality)
                    return buffer.getvalue(), "image/jpeg"
                return image_bytes, mime_type
        except Exception as e:
            logger.warning(f"In-memory image optimization skipped due to error: {e}")
            return image_bytes, mime_type

    def _parse_json_response(self, response_text: str) -> dict:
        """
        Parse JSON from AI response safely without leaking raw prompts.
        """
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            req_id = request_id_ctx.get()
            logger.error(
                "JSON decode error in Gemini response",
                extra={
                    "event": "ocr_json_decode_error",
                    "error": str(e),
                    "request_id": req_id,
                },
            )
            raise ReceiptScanException(
                message="Format data struk dari AI tidak valid. Silakan coba ambil foto ulang dengan posisi tegak.",
                code="AI_PARSING_FAILED",
                status_code=status.HTTP_502_BAD_GATEWAY,
                retryable=False,
                action_hint="retake_photo",
            )

    async def scan_image(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        user_id: Optional[str] = None,
    ) -> dict:
        """
        Scan a receipt image and extract structured data using primary or fallback model.

        Image is processed strictly in RAM and never written to disk.
        """
        start_time = time.perf_counter()
        req_id = request_id_ctx.get()

        # Step 1: In-memory image optimization (Zero-disk footprint)
        opt_bytes, opt_mime = self._optimize_image_bytes(image_bytes, mime_type)

        logger.info(
            "Starting receipt scan with Gemini",
            extra={
                "event": "ocr_scan_start",
                "primary_model": self.primary_model_name,
                "fallback_model": self.fallback_model_name,
                "original_bytes": len(image_bytes),
                "optimized_bytes": len(opt_bytes),
                "mime_type": opt_mime,
                "user_id": user_id,
                "request_id": req_id,
            },
        )

        image_part = {"mime_type": opt_mime, "data": opt_bytes}
        generation_config = genai.types.GenerationConfig(
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=ExpectedReceipt,
        )
        timeout_seconds = getattr(settings, "OCR_TIMEOUT_SECONDS", 35)

        def _call_model(model):
            return model.generate_content(
                [self.SYSTEM_PROMPT, image_part],
                generation_config=generation_config,
                request_options={"timeout": timeout_seconds},
            )

        models_to_try = [
            (self.primary_model_name, self.primary_model),
            (self.fallback_model_name, self.fallback_model),
            ("gemini-2.5-flash", genai.GenerativeModel("gemini-2.5-flash")),
        ]

        last_exception = None
        for idx, (model_name, model_instance) in enumerate(models_to_try):
            is_fallback = idx > 0
            model_start_time = time.perf_counter()
            try:
                if is_fallback:
                    logger.warning(
                        f"Executing automatic fallback to model '{model_name}'",
                        extra={
                            "event": "ocr_model_fallback",
                            "model": model_name,
                            "user_id": user_id,
                            "request_id": req_id,
                        },
                    )

                response = await asyncio.to_thread(_call_model, model_instance)

                # Check if response was blocked or empty
                if not response.text:
                    duration_ms = round((time.perf_counter() - model_start_time) * 1000, 2)
                    logger.warning(
                        f"Model {model_name} returned empty or blocked response",
                        extra={
                            "event": "ocr_empty_response",
                            "model": model_name,
                            "duration_ms": duration_ms,
                            "user_id": user_id,
                            "request_id": req_id,
                        },
                    )
                    raise ReceiptScanException(
                        message="Foto struk tidak terbaca atau terlalu buram. Pastikan foto terang dan teks struk terlihat jelas.",
                        code="AI_IMAGE_UNREADABLE",
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        retryable=False,
                        action_hint="retake_photo",
                    )

                # Parse JSON
                extracted_data = self._parse_json_response(response.text)

                # Post-process items to Title Case
                if "items" in extracted_data and isinstance(extracted_data["items"], list):
                    for item in extracted_data["items"]:
                        if isinstance(item, dict) and "name" in item and isinstance(item["name"], str):
                            item["name"] = item["name"].title()

                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                logger.info(
                    "Receipt scan completed successfully",
                    extra={
                        "event": "ocr_scan_success",
                        "model": model_name,
                        "used_fallback": is_fallback,
                        "duration_ms": duration_ms,
                        "items_count": len(extracted_data.get("items", [])),
                        "total_amount": extracted_data.get("total_amount"),
                        "user_id": user_id,
                        "request_id": req_id,
                    },
                )

                return extracted_data

            except ReceiptScanException:
                # Don't fallback for intentional user error like unreadable image
                raise

            except (
                google_exceptions.DeadlineExceeded,
                google_exceptions.ResourceExhausted,
                google_exceptions.ServiceUnavailable,
            ) as e:
                last_exception = e
                duration_ms = round((time.perf_counter() - model_start_time) * 1000, 2)
                err_type = type(e).__name__
                is_last = idx == len(models_to_try) - 1
                logger.warning(
                    f"Model {model_name} failed with {err_type} after {duration_ms}ms",
                    extra={
                        "event": "ocr_model_error",
                        "model": model_name,
                        "error_type": err_type,
                        "duration_ms": duration_ms,
                        "will_fallback": not is_last,
                        "user_id": user_id,
                        "request_id": req_id,
                    },
                )
                if not is_last:
                    continue
                break

            except google_exceptions.GoogleAPICallError as e:
                last_exception = e
                is_last = idx == len(models_to_try) - 1
                if not is_last:
                    continue
                break

            except Exception as e:
                last_exception = e
                is_last = idx == len(models_to_try) - 1
                if not is_last:
                    continue
                break

        # If execution reached here, both models failed
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        if isinstance(last_exception, google_exceptions.ResourceExhausted):
            logger.warning(
                "All Gemini models exhausted quota",
                extra={
                    "event": "ocr_quota_exhausted",
                    "duration_ms": duration_ms,
                    "user_id": user_id,
                    "request_id": req_id,
                },
            )
            raise ReceiptScanException(
                message="Kuota scan AI sedang penuh. Silakan masukkan transaksi secara manual.",
                code="AI_QUOTA_EXCEEDED",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                retryable=False,
                action_hint="manual_input",
            )
        elif isinstance(last_exception, google_exceptions.DeadlineExceeded):
            logger.warning(
                "All Gemini models timed out",
                extra={
                    "event": "ocr_timeout",
                    "duration_ms": duration_ms,
                    "user_id": user_id,
                    "request_id": req_id,
                },
            )
            raise ReceiptScanException(
                message="Waktu pemrosesan AI habis (timeout). Silakan periksa koneksi internet Anda dan coba lagi.",
                code="AI_TIMEOUT",
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                retryable=True,
                action_hint="retry",
            )
        elif isinstance(last_exception, google_exceptions.ServiceUnavailable):
            logger.warning(
                "All Gemini models service unavailable",
                extra={
                    "event": "ocr_service_unavailable",
                    "duration_ms": duration_ms,
                    "user_id": user_id,
                    "request_id": req_id,
                },
            )
            raise ReceiptScanException(
                message="Layanan Google Gemini sedang tidak dapat dijangkau. Silakan coba beberapa saat lagi.",
                code="AI_SERVICE_UNAVAILABLE",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                retryable=True,
                action_hint="retry",
            )
        elif isinstance(last_exception, (google_exceptions.Unauthenticated, google_exceptions.PermissionDenied)):
            logger.error(
                "Gemini API authentication failed",
                extra={
                    "event": "ocr_auth_failed",
                    "duration_ms": duration_ms,
                    "user_id": user_id,
                    "request_id": req_id,
                },
                exc_info=True,
            )
            raise ReceiptScanException(
                message="Konfigurasi layanan AI bermasalah. Hubungi administrator.",
                code="AI_AUTH_FAILED",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                retryable=False,
                action_hint="contact_support",
            )
        else:
            logger.error(
                f"Unhandled error during receipt scan: {last_exception}",
                extra={
                    "event": "ocr_unhandled_error",
                    "error_type": type(last_exception).__name__ if last_exception else "Unknown",
                    "duration_ms": duration_ms,
                    "user_id": user_id,
                    "request_id": req_id,
                },
                exc_info=True,
            )
            raise ReceiptScanException(
                message="Gagal memproses struk karena kendala teknis. Coba lagi atau input manual.",
                code="AI_PROCESSING_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                retryable=True,
                action_hint="retry",
            )



# Singleton instance for dependency injection
receipt_scanner = ReceiptScanner()


def get_receipt_scanner() -> ReceiptScanner:
    """Dependency injection function for ReceiptScanner."""
    return receipt_scanner
