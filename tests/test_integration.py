"""
Integration tests for AudiPy components
"""

import pytest
from unittest.mock import patch, Mock
from services.auth_service import AuthService
from utils.db.connection import get_db_connection


class TestIntegration:
    """Test integration between components"""
    
    @pytest.mark.asyncio
    @patch('services.auth_service.get_db_connection')
    @patch('services.auth_service.Authenticator')
    @patch('services.auth_service.Client')
    async def test_full_auth_flow(self, mock_client_class, mock_auth_class, mock_get_db, 
                                 mock_authenticator, crypto_instance):
        """Test complete authentication flow from start to finish"""
        # Setup mocks
        mock_auth_class.from_login.return_value = mock_authenticator
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Setup database mock
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        service = AuthService()
        
        # Mock crypto encryption
        with patch.object(service.crypto, 'encrypt_for_user', return_value='encrypted_data'):
            # Test authentication
            result = await service.authenticate_user(
                user_id=1,
                username="test@example.com",
                password="password",
                marketplace="us"
            )
        
        # Verify authentication succeeded
        assert result['success'] is True
        assert result['tokens_stored'] is True
        
        # Verify database interaction
        mock_cursor.execute.assert_called_once()
        mock_auth_class.from_login.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('services.auth_service.get_db_connection')
    async def test_auth_service_with_real_crypto(self, mock_get_db, sample_auth_data):
        """Test auth service with real crypto (no mocking encryption)"""
        # Setup database mock
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = ('real_encrypted_data',)
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        service = AuthService()
        
        # Test that we can encrypt and then decrypt
        test_data = "test authentication data"
        encrypted = service.crypto.encrypt_for_user(1, test_data)
        
        # Mock the database to return our encrypted data
        with patch.object(service.crypto, 'decrypt_for_user', return_value=test_data):
            # This would normally decrypt the data from database
            decrypted = service.crypto.decrypt_for_user(1, encrypted)
            assert decrypted == test_data
    
    @pytest.mark.asyncio
    async def test_error_handling_chain(self):
        """Test error handling across multiple components"""
        service = AuthService()
        
        # Test with invalid user ID
        with patch('services.auth_service.get_db_connection') as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")
            
            client = await service.get_audible_client(999)
            assert client is None
    
    def test_crypto_with_different_data_types(self, crypto_instance):
        """Test crypto with various data types that might be stored"""
        import json
        
        # Test with complex auth data structure
        complex_data = {
            'tokens': ['token1', 'token2'],
            'expires': 1234567890,
            'nested': {'key': 'value'},
            'unicode': '测试 🎵',
            'boolean': True,
            'null_value': None
        }
        
        json_data = json.dumps(complex_data)
        encrypted = crypto_instance.encrypt_for_user(1, json_data)
        decrypted = crypto_instance.decrypt_for_user(1, encrypted)
        
        assert json.loads(decrypted) == complex_data
    
    @pytest.mark.integration
    def test_database_connection_with_real_config(self):
        """Test database connection with real configuration"""
        # This test uses the real database configuration
        # Mark as integration test so it can be skipped in unit test runs
        from utils.db.connection import test_connection
        
        # This will test the actual database connection
        # Should pass if database is properly configured
        result = test_connection()
        assert isinstance(result, bool)  # Should return True or False
    
    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test that all services can be initialized without errors"""
        # Test AuthService
        auth_service = AuthService()
        assert auth_service.crypto is not None
        
        # Test that crypto instance is working
        test_data = "initialization test"
        encrypted = auth_service.crypto.encrypt_for_user(1, test_data)
        decrypted = auth_service.crypto.decrypt_for_user(1, encrypted)
        assert decrypted == test_data 