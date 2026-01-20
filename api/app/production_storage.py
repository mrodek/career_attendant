import os
import boto3
import uuid
from typing import Optional
from fastapi import UploadFile
import aiofiles
from .secure_storage import SecureLocalStorage

class StorageBackend:
    """Abstract storage backend for resume files."""
    
    async def save_file(self, file: UploadFile, user_id: str) -> str:
        """Save file and return the file path/URL."""
        raise NotImplementedError
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file by path/URL."""
        raise NotImplementedError

class LocalStorage(SecureLocalStorage):
    """Local file system storage for development."""
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            base_path = os.path.join(
                os.path.dirname(__file__), "..", "uploads"
            )
        super().__init__(base_path=base_path)

class S3Storage(StorageBackend):
    """AWS S3 storage for production."""
    
    def __init__(self, bucket: str, access_key: str, secret_key: str, region: str = "us-east-1"):
        self.bucket = bucket
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
    
    async def save_file(self, file: UploadFile, user_id: str) -> str:
        """Save file to S3 and return the S3 URL."""
        # Generate unique filename
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{user_id}/{uuid.uuid4()}{file_ext}"
        
        # Upload to S3
        content = await file.read()
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=unique_filename,
            Body=content,
            ContentType=file.content_type
        )
        
        # Return S3 URL
        return f"https://{self.bucket}.s3.amazonaws.com/{unique_filename}"
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from S3."""
        try:
            # Extract key from S3 URL
            if file_path.startswith('https://'):
                key = file_path.split('/')[-1]
                # Reconstruct full key with user folder
                key = file_path.split('.amazonaws.com/')[-1]
            
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

def get_storage_backend() -> StorageBackend:
    """Get the appropriate storage backend based on environment."""
    # Check if S3 credentials are available
    if all([
        os.getenv('AWS_ACCESS_KEY_ID'),
        os.getenv('AWS_SECRET_ACCESS_KEY'),
        os.getenv('AWS_S3_BUCKET')
    ]):
        return S3Storage(
            bucket=os.getenv('AWS_S3_BUCKET'),
            access_key=os.getenv('AWS_ACCESS_KEY_ID'),
            secret_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region=os.getenv('AWS_REGION', 'us-east-1')
        )
    elif os.getenv('RAILWAY_VOLUME_MOUNT_PATH'):
        # Use Railway's persistent disk storage
        return LocalStorage(base_path=os.getenv('RAILWAY_VOLUME_MOUNT_PATH'))
    else:
        # Fall back to local storage for development
        return LocalStorage()
