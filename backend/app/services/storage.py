"""
S3 Storage Service

Handles PDF file uploads to Google Cloud Storage with encryption.
"""
from datetime import timedelta
from typing import BinaryIO
import os
from uuid import uuid4
import asyncio

from google.cloud import storage
from google.cloud.storage import Blob, Bucket
from fastapi import UploadFile
from loguru import logger

from app.core.config import settings


class S3StorageService:
    """Google Cloud Storage service for PDF file management"""

    def __init__(self):
        """Initialize GCS client"""
        self.client = storage.Client(project=settings.GCP_PROJECT_ID)
        self.bucket_name = settings.GCS_BUCKET_POLICIES
        self.bucket: Bucket = self.client.bucket(self.bucket_name)

    async def upload_pdf(
        self,
        file: UploadFile,
        policy_name: str,
        insurer: str
    ) -> str:
        """
        Upload PDF file to GCS with server-side encryption.

        Args:
            file: Uploaded PDF file
            policy_name: Name of the insurance policy
            insurer: Insurance company name

        Returns:
            S3 key (GCS object path) for the uploaded file

        Raises:
            Exception: If upload fails
        """
        try:
            # Generate unique file key
            file_id = str(uuid4())
            # Sanitize names for file path
            safe_insurer = insurer.replace(" ", "_").replace("/", "-")
            safe_policy = policy_name.replace(" ", "_").replace("/", "-")

            # Construct S3 key: policies/{insurer}/{policy_name}_{uuid}.pdf
            s3_key = f"policies/{safe_insurer}/{safe_policy}_{file_id}.pdf"

            # Create blob
            blob: Blob = self.bucket.blob(s3_key)

            # Set content type
            blob.content_type = "application/pdf"

            # Upload with server-side encryption (GCS default: AES-256)
            # GCS encrypts all data at rest by default
            await file.seek(0)  # Reset file pointer
            content = await file.read()

            # Upload in async-compatible way using to_thread to avoid blocking event loop
            # This prevents blocking the async event loop during upload
            await asyncio.to_thread(
                blob.upload_from_string,
                content,
                content_type="application/pdf",
            )

            logger.info(f"Uploaded PDF to GCS: {s3_key} (size: {len(content)} bytes)")

            return s3_key

        except Exception as e:
            logger.error(f"Failed to upload PDF to GCS: {e}")
            raise Exception(f"S3 upload failed: {str(e)}")

    async def get_signed_url(self, s3_key: str, expiration: int = 3600) -> str:
        """
        Generate a signed URL for downloading a file.

        Args:
            s3_key: GCS object key
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            Presigned URL for file download

        Raises:
            Exception: If URL generation fails
        """
        try:
            blob: Blob = self.bucket.blob(s3_key)

            # Generate signed URL valid for specified duration
            # Wrap in to_thread to avoid blocking
            url = await asyncio.to_thread(
                blob.generate_signed_url,
                version="v4",
                expiration=timedelta(seconds=expiration),
                method="GET",
            )

            logger.info(f"Generated signed URL for {s3_key} (expires in {expiration}s)")

            return url

        except Exception as e:
            logger.error(f"Failed to generate signed URL for {s3_key}: {e}")
            raise Exception(f"Signed URL generation failed: {str(e)}")

    async def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from GCS.

        Args:
            s3_key: GCS object key

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            blob: Blob = self.bucket.blob(s3_key)
            # Wrap delete in to_thread to avoid blocking
            await asyncio.to_thread(blob.delete)

            logger.info(f"Deleted file from GCS: {s3_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file {s3_key}: {e}")
            return False

    async def file_exists(self, s3_key: str) -> bool:
        """
        Check if a file exists in GCS.

        Args:
            s3_key: GCS object key

        Returns:
            True if file exists, False otherwise
        """
        try:
            blob: Blob = self.bucket.blob(s3_key)
            # Wrap exists check in to_thread to avoid blocking
            return await asyncio.to_thread(blob.exists)

        except Exception as e:
            logger.error(f"Failed to check file existence {s3_key}: {e}")
            return False


# Singleton instance
_storage_service: S3StorageService | None = None


def get_storage_service() -> S3StorageService:
    """Get or create storage service singleton"""
    global _storage_service
    if _storage_service is None:
        _storage_service = S3StorageService()
    return _storage_service
