"""
Unit-style API Tests - Direct function testing for coverage
Focus: Test route handlers directly, KISS principle, 50% coverage target
"""

import pytest
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime
import json

# Import the route handler functions directly
from api.main import (
    root, health_check, login, verify_otp, get_current_user_info,
    logout, get_user_profile, get_library, sync_library, get_sync_status
)

class TestAPIUnits:
    """Unit tests for API route handlers - direct function calls"""
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        """Test root endpoint function directly"""
        result = await root()
        assert result["message"] == "AudiPy API is running"
        assert result["version"] == "1.0.0"
    
    @patch('api.main.test_connection')
    @pytest.mark.asyncio
    async def test_health_endpoint_healthy(self, mock_test_connection):
        """Test health endpoint when database is healthy"""
        mock_test_connection.return_value = True
        
        result = await health_check()
        assert result["status"] == "healthy"
        assert result["database"] == "connected"
    
    @patch('api.main.test_connection')
    @pytest.mark.asyncio
    async def test_health_endpoint_unhealthy(self, mock_test_connection):
        """Test health endpoint when database is unhealthy"""
        mock_test_connection.return_value = False
        
        result = await health_check()
        assert result["status"] == "unhealthy"
        assert result["database"] == "disconnected"
    
    @patch('api.main.ensure_user_exists')
    @patch('api.main.auth_service.authenticate_user')
    @patch('api.main.create_jwt_token')
    @pytest.mark.asyncio
    async def test_login_success_no_otp(self, mock_jwt, mock_auth, mock_user):
        """Test successful login without OTP"""
        # Setup mocks
        mock_user.return_value = 1
        mock_auth.return_value = {
            'success': True,
            'message': 'Authentication successful',
            'requires_otp': False
        }
        mock_jwt.return_value = "test_jwt_token"
        
        # Create mock request and response
        from api.main import LoginRequest
        login_request = LoginRequest(
            username="test@example.com",
            password="password",
            marketplace="us"
        )
        
        mock_response = Mock()
        
        result = await login(login_request, mock_response)
        
        assert result.success is True
        assert result.message == "Login successful"
        assert result.requires_otp is False
        assert result.user is not None
    
    @patch('api.main.ensure_user_exists')
    @patch('api.main.auth_service.authenticate_user')
    @pytest.mark.asyncio
    async def test_login_requires_otp(self, mock_auth, mock_user):
        """Test login that requires OTP"""
        # Setup mocks
        mock_user.return_value = 1
        mock_auth.return_value = {
            'success': False,
            'message': 'Two-factor authentication required',
            'requires_otp': True
        }
        
        # Create mock request
        from api.main import LoginRequest
        login_request = LoginRequest(
            username="test@example.com",
            password="password",
            marketplace="us"
        )
        
        mock_response = Mock()
        
        result = await login(login_request, mock_response)
        
        assert result.success is False
        assert result.requires_otp is True
        assert result.session_id is not None
    
    @patch('api.main.get_current_user')
    @pytest.mark.asyncio
    async def test_get_current_user_authenticated(self, mock_get_user):
        """Test getting current user when authenticated"""
        mock_user = {
            "user_id": 1,
            "username": "test@example.com",
            "marketplace": "us"
        }
        mock_get_user.return_value = mock_user
        
        mock_request = Mock()
        
        result = await get_current_user_info(mock_request)
        
        assert result.authenticated is True
        assert result.user["user_id"] == 1
        assert result.user["username"] == "test@example.com"
    
    @patch('api.main.get_current_user')
    @pytest.mark.asyncio
    async def test_get_current_user_not_authenticated(self, mock_get_user):
        """Test getting current user when not authenticated"""
        mock_get_user.return_value = None
        
        mock_request = Mock()
        
        result = await get_current_user_info(mock_request)
        
        assert result.authenticated is False
        assert result.user is None
    
    @pytest.mark.asyncio
    async def test_logout(self):
        """Test logout endpoint"""
        mock_response = Mock()
        
        result = await logout(mock_response)
        
        assert result["success"] is True
        assert result["message"] == "Logged out successfully"
    
    @patch('api.main.get_current_user')
    @patch('api.main.get_db_connection')
    @pytest.mark.asyncio
    async def test_get_user_profile_success(self, mock_db, mock_get_user):
        """Test getting user profile successfully"""
        # Setup user
        mock_user = {"user_id": 1, "username": "test@example.com"}
        mock_get_user.return_value = mock_user
        
        # Setup database mocks
        mock_cursor = Mock()
        mock_cursor.fetchone.side_effect = [
            {  # User profile
                "user_id": 1,
                "username": "test@example.com",
                "email": "test@example.com",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {  # User preferences
                "language": "english",
                "marketplace": "us",
                "max_price": 12.66
            },
            {  # Audible account
                "marketplace": "us",
                "sync_status": "completed",
                "tokens_expires_at": datetime.now(),
                "last_sync": datetime.now()
            }
        ]
        
        mock_connection = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__.return_value = mock_connection
        
        mock_request = Mock()
        
        result = await get_user_profile(mock_request)
        
        assert "profile" in result
        assert "preferences" in result
        assert "audible_account" in result
    
    @patch('api.main.get_current_user')
    @patch('api.main.get_db_connection')
    @pytest.mark.asyncio
    async def test_get_library_success(self, mock_db, mock_get_user):
        """Test getting library successfully"""
        # Setup user
        mock_user = {"user_id": 1}
        mock_get_user.return_value = mock_user
        
        # Setup database mocks
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {"total": 5}  # Total count
        mock_cursor.fetchall.return_value = [
            {
                "asin": "B001",
                "title": "Test Book 1",
                "subtitle": None,
                "runtime_length_min": 600,
                "publication_datetime": datetime.now(),
                "language": "english",
                "content_type": "Product",
                "purchase_date": datetime.now(),
                "authors": "Author 1",
                "narrators": "Narrator 1",
                "series": None
            }
        ]
        
        mock_connection = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__.return_value = mock_connection
        
        mock_request = Mock()
        
        result = await get_library(mock_request, page=1, page_size=20, search="", sort_by="title", sort_order="asc")
        
        assert result.books is not None
        assert result.total_count == 5
        assert result.page == 1
        assert result.page_size == 20
        assert len(result.books) == 1
    
    @patch('api.main.get_current_user')
    @patch('api.main.get_user_sync_status')
    @pytest.mark.asyncio
    async def test_sync_library_success(self, mock_sync_status, mock_get_user):
        """Test starting library sync"""
        mock_user = {"user_id": 1}
        mock_get_user.return_value = mock_user
        mock_sync_status.return_value = {"is_syncing": False}
        
        mock_request = Mock()
        
        with patch('threading.Thread') as mock_thread:
            result = await sync_library(mock_request)
        
        assert result["success"] is True
        assert result["message"] == "Library sync started"
        mock_thread.assert_called_once()
    
    @patch('api.main.get_current_user')
    @patch('api.main.get_user_sync_status')
    @pytest.mark.asyncio
    async def test_sync_library_already_syncing(self, mock_sync_status, mock_get_user):
        """Test sync when already in progress"""
        mock_user = {"user_id": 1}
        mock_get_user.return_value = mock_user
        mock_sync_status.return_value = {"is_syncing": True}
        
        mock_request = Mock()
        
        result = await sync_library(mock_request)
        
        assert result["success"] is False
        assert result["message"] == "Sync already in progress"
    
    @patch('api.main.get_current_user')
    @patch('api.main.get_user_sync_status')
    @patch('api.main.get_db_connection')
    @pytest.mark.asyncio
    async def test_get_sync_status_success(self, mock_db, mock_sync_status, mock_get_user):
        """Test getting sync status"""
        mock_user = {"user_id": 1}
        mock_get_user.return_value = mock_user
        mock_sync_status.return_value = {
            "is_syncing": False,
            "last_sync": "2024-01-01T00:00:00",
            "total_books": 0,
            "status_message": "Ready to sync"
        }
        
        # Mock database for book count
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {"total_books": 5}
        mock_connection = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__.return_value = mock_connection
        
        mock_request = Mock()
        
        result = await get_sync_status(mock_request)
        
        assert result.is_syncing is False
        assert result.total_books == 5
        assert result.status_message is not None 