"""
Google Cloud Storage service for policy document uploads
"""
from typing import BinaryIO, Tuple
from uuid import UUID
import os
from datetime import timedelta

from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError

from app.core.config import settings


class GCSStorageService:
    """Service for uploading and managing policy documents in GCS"""

    def __init__(self):
        """Initialize GCS client"""
        self.client = storage.Client(project=settings.GCP_PROJECT_ID)
        self.bucket_name = settings.GCS_BUCKET_POLICIES

    def upload_policy_pdf(
        self,
        file: BinaryIO,
        job_id: UUID,
        filename: str,
        content_type: str = "application/pdf"
    ) -> Tuple[str, str]:
        """
        Upload a policy PDF to GCS

        Args:
            file: File-like object to upload
            job_id: Job ID for organizing files
            filename: Original filename
            content_type: MIME type

        Returns:
            Tuple of (blob_name, gcs_uri)

        Raises:
            GoogleCloudError: If upload fails
        """
        try:
            # Get or create bucket
            bucket = self.client.bucket(self.bucket_name)

            # Create blob name: policies/{job_id}/{filename}
            blob_name = f"policies/{job_id}/{filename}"
            blob = bucket.blob(blob_name)

            # Set metadata
            blob.metadata = {
                "job_id": str(job_id),
                "original_filename": filename,
                "uploaded_by": "insuregraph-backend"
            }

            # Upload file
            blob.upload_from_file(
                file,
                content_type=content_type,
                timeout=300  # 5 minutes timeout
            )

            # Construct GCS URI
            gcs_uri = f"gs://{self.bucket_name}/{blob_name}"

            return blob_name, gcs_uri

        except GoogleCloudError as e:
            raise Exception(f"Failed to upload to GCS: {str(e)}")

    def generate_signed_url(self, blob_name: str, expiration_minutes: int = 60) -> str:
        """
        Generate a signed URL for temporary access to a blob

        Args:
            blob_name: Name of the blob in GCS
            expiration_minutes: URL expiration time in minutes

        Returns:
            Signed URL string
        """
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(blob_name)

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="GET"
        )

        return url

    def delete_policy_pdf(self, blob_name: str) -> bool:
        """
        Delete a policy PDF from GCS

        Args:
            blob_name: Name of the blob to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(blob_name)
            blob.delete()
            return True
        except GoogleCloudError:
            return False

    def check_file_exists(self, blob_name: str) -> bool:
        """
        Check if a file exists in GCS

        Args:
            blob_name: Name of the blob to check

        Returns:
            True if exists, False otherwise
        """
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(blob_name)
        return blob.exists()

    def get_file_size(self, blob_name: str) -> int:
        """
        Get file size in bytes

        Args:
            blob_name: Name of the blob

        Returns:
            File size in bytes
        """
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(blob_name)
        blob.reload()  # Fetch metadata
        return blob.size


# Global instance
gcs_service = GCSStorageService()
