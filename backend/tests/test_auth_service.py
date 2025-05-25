"""
Tests for authentication service
"""

import pytest
import json
from unittest.mock import patch, Mock, AsyncMock
from services.auth_service import AuthService


class TestAuthService:
    """Test authentication service functionality"""
    
    def test_auth_service_init(self):
        """Test AuthService initialization"""
        service = AuthService()
        assert service.crypto is not None
    
    @pytest.mark.asyncio
    @patch('services.auth_service.Authenticator')
    @patch('services.auth_service.Client')
    async def test_authenticate_user_success(self, mock_client_class, mock_auth_class, mock_authenticator):
        """Test successful user authentication"""
        # Setup mocks
        mock_auth_class.from_login.return_value = mock_authenticator
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        service = AuthService()
        
        with patch.object(service, '_store_tokens', return_value=True):
            result = await service.authenticate_user(
                user_id=1,
                username="test@example.com",
                password="password",
                marketplace="us"
            )
        
        assert result['success'] is True
        assert result['message'] == 'Authentication successful'
        assert result['requires_otp'] is False
        assert result['tokens_stored'] is True
    
    @pytest.mark.asyncio
    @patch('services.auth_service.Authenticator')
    async def test_authenticate_user_otp_required(self, mock_auth_class):
        """Test authentication when OTP is required"""
        mock_auth_class.from_login.side_effect = Exception("OTP required")
        
        service = AuthService()
        result = await service.authenticate_user(
            user_id=1,
            username="test@example.com",
            password="password",
            marketplace="us"
        )
        
        assert result['success'] is False
        assert result['requires_otp'] is True
        assert 'Two-factor authentication required' in result['message']
    
    @pytest.mark.asyncio
    @patch('services.auth_service.Authenticator')
    async def test_authenticate_user_failure(self, mock_auth_class):
        """Test authentication failure"""
        mock_auth_class.from_login.side_effect = Exception("Invalid credentials")
        
        service = AuthService()
        result = await service.authenticate_user(
            user_id=1,
            username="test@example.com",
            password="wrong_password",
            marketplace="us"
        )
        
        assert result['success'] is False
        assert result['requires_otp'] is False
        assert 'Authentication failed' in result['message']
    
    @pytest.mark.asyncio
    @patch('services.auth_service.get_db_connection')
    async def test_store_tokens_success(self, mock_get_db, mock_authenticator, sample_auth_data):
        """Test successful token storage"""
        # Setup database mock
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        service = AuthService()
        
        # Mock the crypto encryption
        with patch.object(service.crypto, 'encrypt_for_user', return_value='encrypted_data'):
            result = await service._store_tokens(1, mock_authenticator, 'us')
        
        assert result is True
        mock_cursor.execute.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('services.auth_service.get_db_connection')
    async def test_store_tokens_failure(self, mock_get_db, mock_authenticator):
        """Test token storage failure"""
        mock_get_db.side_effect = Exception("Database error")
        
        service = AuthService()
        result = await service._store_tokens(1, mock_authenticator, 'us')
        
        assert result is False
    
    @pytest.mark.asyncio
    @patch('services.auth_service.get_db_connection')
    @patch('services.auth_service.Authenticator')
    @patch('services.auth_service.Client')
    async def test_get_audible_client_success(self, mock_client_class, mock_auth_class, mock_get_db, sample_auth_data):
        """Test successful Audible client retrieval"""
        # Setup database mock
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = ('encrypted_data',)
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        # Setup authenticator mock
        mock_auth = Mock()
        mock_auth_class.from_dict.return_value = mock_auth
        
        # Setup client mock
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        service = AuthService()
        
        # Mock crypto decryption
        with patch.object(service.crypto, 'decrypt_for_user', return_value=json.dumps(sample_auth_data)):
            client = await service.get_audible_client(1)
        
        assert client == mock_client
        mock_auth_class.from_dict.assert_called_once_with(sample_auth_data)
    
    @pytest.mark.asyncio
    @patch('services.auth_service.get_db_connection')
    async def test_get_audible_client_no_tokens(self, mock_get_db):
        """Test Audible client retrieval when no tokens exist"""
        # Setup database mock with no results
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        service = AuthService()
        client = await service.get_audible_client(1)
        
        assert client is None
    
    @pytest.mark.asyncio
    async def test_test_api_access_success(self, mock_audible_client):
        """Test successful API access test"""
        service = AuthService()
        
        with patch.object(service, 'get_audible_client', return_value=mock_audible_client):
            result = await service.test_api_access(1)
        
        assert result['success'] is True
        assert 'API access confirmed' in result['message']
        assert '100 books' in result['message']
    
    @pytest.mark.asyncio
    async def test_test_api_access_no_client(self):
        """Test API access test when no client available"""
        service = AuthService()
        
        with patch.object(service, 'get_audible_client', return_value=None):
            result = await service.test_api_access(1)
        
        assert result['success'] is False
        assert 'No authentication tokens found' in result['message']
    
    @pytest.mark.asyncio
    async def test_test_api_access_api_failure(self):
        """Test API access test when API call fails"""
        mock_client = Mock()
        mock_client.get.side_effect = Exception("API error")
        
        service = AuthService()
        
        with patch.object(service, 'get_audible_client', return_value=mock_client):
            result = await service.test_api_access(1)
        
        assert result['success'] is False
        assert 'API access test failed' in result['message']
    
    def test_make_json_safe_basic_types(self):
        """Test _make_json_safe with basic types"""
        service = AuthService()
        
        assert service._make_json_safe("string") == "string"
        assert service._make_json_safe(123) == 123
        assert service._make_json_safe([1, 2, 3]) == [1, 2, 3]
        assert service._make_json_safe({"key": "value"}) == {"key": "value"}
        assert service._make_json_safe(None) is None
    
    def test_make_json_safe_object_with_dict(self):
        """Test _make_json_safe with object that has __dict__"""
        service = AuthService()
        
        class TestObj:
            def __init__(self):
                self.attr = "value"
        
        obj = TestObj()
        result = service._make_json_safe(obj)
        assert result == {"attr": "value"}
    
    def test_format_expires_date(self):
        """Test _format_expires_date with different input types"""
        service = AuthService()
        
        # String input
        assert service._format_expires_date("2023-01-01") == "2023-01-01"
        
        # None input
        assert service._format_expires_date(None) is None
        
        # Timestamp input (timezone-aware test)
        timestamp = 1640995200  # 2022-01-01 00:00:00 UTC
        result = service._format_expires_date(timestamp)
        assert isinstance(result, str)
        # Check for either date depending on timezone
        assert "2021-12-31" in result or "2022-01-01" in result 