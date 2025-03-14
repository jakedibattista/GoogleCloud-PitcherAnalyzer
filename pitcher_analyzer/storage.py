"""Module for handling Google Cloud Storage operations."""

import os
import logging
from datetime import datetime
from google.cloud import storage
from google.oauth2 import service_account
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pitcher_analyzer.config import (
    PROJECT_ID, BUCKET_NAME, CREDENTIALS_PATH, 
    MAX_RETRIES, MIN_RETRY_WAIT_SECONDS, MAX_RETRY_WAIT_SECONDS
)

logger = logging.getLogger(__name__)

class CloudStorage:
    """Handler for Google Cloud Storage operations."""
    
    def __init__(self):
        """Initialize the storage client with the project credentials."""
        try:
            credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
            self.client = storage.Client(credentials=credentials, project=PROJECT_ID)
            self.bucket_name = BUCKET_NAME
            self._ensure_bucket_exists()
            logger.info(f"Cloud Storage initialized for project: {PROJECT_ID}")
        except Exception as e:
            logger.error(f"Failed to initialize Cloud Storage: {e}")
            raise

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=MIN_RETRY_WAIT_SECONDS, max=MAX_RETRY_WAIT_SECONDS),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True
    )
    def _ensure_bucket_exists(self):
        """Ensure that the storage bucket exists, creating it if necessary."""
        try:
            bucket = self.client.bucket(self.bucket_name)
            if not bucket.exists():
                bucket = self.client.create_bucket(self.bucket_name)
                logger.info(f"Created new bucket: {self.bucket_name}")
            else:
                logger.info(f"Using existing bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            raise

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=MIN_RETRY_WAIT_SECONDS, max=MAX_RETRY_WAIT_SECONDS),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True
    )
    def upload_video(self, file_path):
        """
        Upload a video file to Google Cloud Storage with retry logic.
        
        Args:
            file_path: Local path to the video file
            
        Returns:
            GCS URI of the uploaded file
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
                
            # Generate a unique blob name with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            blob_name = f"uploads/{timestamp}_{os.path.basename(file_path)}"
            
            # Get bucket and upload file
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(blob_name)
            
            logger.info(f"Uploading {file_path} to gs://{self.bucket_name}/{blob_name}")
            blob.upload_from_filename(file_path)
            
            # Generate the full GCS URI
            gcs_uri = f"gs://{self.bucket_name}/{blob_name}"
            logger.info(f"Upload complete: {gcs_uri}")
            
            return gcs_uri
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise

    def check_connectivity(self):
        """
        Check if we can connect to Google Cloud Storage.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Try to list a single bucket to verify connectivity
            next(self.client.list_buckets(max_results=1), None)
            return True
        except Exception as e:
            logger.error(f"GCS connectivity check failed: {e}")
            return False 