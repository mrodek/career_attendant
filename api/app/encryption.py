import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Any, Dict, Optional
import json

class DataEncryption:
    """Handles encryption/decryption of sensitive resume data."""
    
    def __init__(self, master_key: Optional[str] = None):
        if master_key is None:
            master_key = os.getenv('ENCRYPTION_MASTER_KEY')
            if not master_key:
                raise ValueError("ENCRYPTION_MASTER_KEY environment variable required")
        
        # Derive encryption key from master key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'career_attendant_salt',  # Fixed salt for consistency
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        self.cipher = Fernet(key)
    
    def encrypt_text(self, text: str) -> str:
        """Encrypt text data for database storage."""
        if not text:
            return text
        encrypted_data = self.cipher.encrypt(text.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt_text(self, encrypted_text: str) -> str:
        """Decrypt text data from database."""
        if not encrypted_text:
            return encrypted_text
        try:
            encrypted_data = base64.urlsafe_b64decode(encrypted_text.encode())
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception:
            # Return original text if decryption fails
            return encrypted_text
    
    def encrypt_json(self, data: Dict[str, Any]) -> str:
        """Encrypt JSON data for database storage."""
        if not data:
            return None
        json_str = json.dumps(data)
        return self.encrypt_text(json_str)
    
    def decrypt_json(self, encrypted_json: str) -> Optional[Dict[str, Any]]:
        """Decrypt JSON data from database."""
        if not encrypted_json:
            return None
        try:
            decrypted_str = self.decrypt_text(encrypted_json)
            return json.loads(decrypted_str)
        except Exception:
            return None

# Lazy encryption instance - only created when needed
_encryption = None

def get_encryption():
    """Get encryption instance, creating it lazily."""
    global _encryption
    if _encryption is None:
        _encryption = DataEncryption()
    return _encryption
