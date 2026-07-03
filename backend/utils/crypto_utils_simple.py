#!/usr/bin/env python3
"""
Simple cryptographic utilities for AudiPy
Environment variables + Fernet encryption approach for startups/small apps
"""

import os
import hashlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class UserCrypto:
    """Handles encryption/decryption with environment-based key management"""
    
    def __init__(self):
        """Initialize with master key from environment"""
        self.master_key = self._get_master_key()
    
    def _get_master_key(self) -> bytes:
        """Get master key from environment variable"""
        key_str = os.getenv('AUDIPY_MASTER_KEY')
        
        if not key_str:
            # Generate a new key and show instructions
            key = Fernet.generate_key()
            print(f"🔑 Generated new master key. Add this to your .env file:")
            print(f"AUDIPY_MASTER_KEY={key.decode()}")
            print(f"⚠️  Application will not work until you add this key to .env")
            raise RuntimeError("Master key not found in environment. Please add AUDIPY_MASTER_KEY to .env file.")
        
        return key_str.encode()
    
    def _derive_user_key(self, user_id: int, salt_suffix: str = "audipy_user_salt") -> bytes:
        """
        Derive a user-specific encryption key from master key and user ID
        
        Args:
            user_id: User's database ID
            salt_suffix: Additional salt material
            
        Returns:
            32-byte encryption key for this specific user
        """
        # Create a deterministic salt from user ID and suffix
        salt_material = f"{user_id}:{salt_suffix}".encode()
        salt = hashlib.sha256(salt_material).digest()[:16]  # 16 bytes for salt
        
        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 32 bytes = 256 bits
            salt=salt,
            iterations=100000,  # 100k iterations for security
        )
        
        return kdf.derive(self.master_key)
    
    def encrypt_for_user(self, user_id: int, data: str) -> str:
        """
        Encrypt data for a specific user
        
        Args:
            user_id: User's database ID
            data: String data to encrypt
            
        Returns:
            Base64 encoded encrypted data
        """
        user_key = self._derive_user_key(user_id)
        fernet = Fernet(base64.urlsafe_b64encode(user_key))
        
        encrypted_data = fernet.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt_for_user(self, user_id: int, encrypted_data: str) -> str:
        """
        Decrypt data for a specific user
        
        Args:
            user_id: User's database ID
            encrypted_data: Base64 encoded encrypted data
            
        Returns:
            Decrypted string data
        """
        user_key = self._derive_user_key(user_id)
        fernet = Fernet(base64.urlsafe_b64encode(user_key))
        
        encrypted_bytes = base64.b64decode(encrypted_data)
        decrypted_data = fernet.decrypt(encrypted_bytes)
        return decrypted_data.decode()

def get_crypto_instance() -> UserCrypto:
    """Get a UserCrypto instance"""
    return UserCrypto() 