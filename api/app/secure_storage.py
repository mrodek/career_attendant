import os
import aiofiles
from fastapi import UploadFile
from .encryption import get_encryption
import uuid
import gzip

class SecureLocalStorage:
    """Encrypted local file storage for sensitive resume files."""
    
    def __init__(self, base_path: str = None):
        self.base_path = base_path or os.path.join(
            os.path.dirname(__file__), "..", "uploads"
        )
    
    async def save_file(self, file: UploadFile, user_id: str) -> str:
        """Save file with encryption and compression."""
        user_storage_path = os.path.join(self.base_path, user_id)
        os.makedirs(user_storage_path, exist_ok=True)
        
        # Generate unique filename
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}.enc{file_ext}"
        file_path = os.path.join(user_storage_path, unique_filename)
        
        # Read and compress file content
        content = await file.read()
        compressed_content = gzip.compress(content)
        
        # Encrypt compressed content
        encrypted_content = get_encryption().cipher.encrypt(compressed_content)
        
        # Save encrypted file
        async with aiofiles.open(file_path, 'wb') as out_file:
            await out_file.write(encrypted_content)
        
        return file_path
    
    async def read_file(self, file_path: str) -> bytes:
        """Read and decrypt file content."""
        async with aiofiles.open(file_path, 'rb') as in_file:
            encrypted_content = await in_file.read()
        
        # Decrypt and decompress
        compressed_content = get_encryption().cipher.decrypt(encrypted_content)
        original_content = gzip.decompress(compressed_content)
        
        return original_content
    
    async def delete_file(self, file_path: str) -> bool:
        """Securely delete file."""
        try:
            # Overwrite file with random data before deletion (optional security measure)
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(os.urandom(os.path.getsize(file_path)))
            
            os.remove(file_path)
            return True
        except OSError:
            return False
