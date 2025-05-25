"""
Tests for crypto utilities
"""

import pytest
from utils.crypto_utils_simple import get_crypto_instance


class TestCryptoUtils:
    """Test crypto utilities functionality"""
    
    def test_get_crypto_instance(self):
        """Test getting crypto instance"""
        crypto = get_crypto_instance()
        assert crypto is not None
        assert hasattr(crypto, 'encrypt_for_user')
        assert hasattr(crypto, 'decrypt_for_user')
    
    def test_encrypt_decrypt_roundtrip(self, crypto_instance, sample_user_id):
        """Test encryption and decryption roundtrip"""
        test_data = "test data to encrypt"
        
        # Encrypt
        encrypted = crypto_instance.encrypt_for_user(sample_user_id, test_data)
        assert encrypted != test_data
        assert isinstance(encrypted, str)
        
        # Decrypt
        decrypted = crypto_instance.decrypt_for_user(sample_user_id, encrypted)
        assert decrypted == test_data
    
    def test_encrypt_different_users(self, crypto_instance):
        """Test that different users get different encrypted data"""
        test_data = "same data"
        
        encrypted_user1 = crypto_instance.encrypt_for_user(1, test_data)
        encrypted_user2 = crypto_instance.encrypt_for_user(2, test_data)
        
        assert encrypted_user1 != encrypted_user2
    
    def test_decrypt_wrong_user_fails(self, crypto_instance):
        """Test that decrypting with wrong user ID fails"""
        test_data = "test data"
        
        encrypted = crypto_instance.encrypt_for_user(1, test_data)
        
        with pytest.raises(Exception):
            crypto_instance.decrypt_for_user(2, encrypted)
    
    def test_encrypt_empty_string(self, crypto_instance, sample_user_id):
        """Test encrypting empty string"""
        test_data = ""
        
        encrypted = crypto_instance.encrypt_for_user(sample_user_id, test_data)
        decrypted = crypto_instance.decrypt_for_user(sample_user_id, encrypted)
        
        assert decrypted == test_data
    
    def test_encrypt_unicode_data(self, crypto_instance, sample_user_id):
        """Test encrypting unicode data"""
        test_data = "测试数据 🎵 émojis"
        
        encrypted = crypto_instance.encrypt_for_user(sample_user_id, test_data)
        decrypted = crypto_instance.decrypt_for_user(sample_user_id, encrypted)
        
        assert decrypted == test_data 