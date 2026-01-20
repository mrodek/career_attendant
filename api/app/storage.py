import os
import aiofiles
from fastapi import UploadFile

# For local development, store files in a directory relative to this file.
# In production, this would be replaced with an S3 client.
LOCAL_STORAGE_PATH = os.path.join(os.path.dirname(__file__), "..", "uploads")

async def save_file(file: UploadFile, user_id: str) -> str:
    """Saves an uploaded file to the local storage and returns the file path."""
    # Create a user-specific directory
    user_storage_path = os.path.join(LOCAL_STORAGE_PATH, user_id)
    os.makedirs(user_storage_path, exist_ok=True)

    file_path = os.path.join(user_storage_path, file.filename)

    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    return file_path

async def delete_file(file_path: str) -> bool:
    """Deletes a file from the local storage."""
    try:
        os.remove(file_path)
        return True
    except OSError:
        return False
