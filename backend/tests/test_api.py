"""
Tests for FastAPI endpoints - Phases 1-3
NOTE: These tests are currently disabled due to FastAPI TestClient compatibility issues.
TODO: Fix httpx.AsyncClient integration or downgrade to compatible versions.
"""

import pytest
import httpx
import asyncio
from unittest.mock import patch, Mock, AsyncMock
import json
from datetime import datetime, timedelta

from api.main import app

# Skip all API tests due to compatibility issues
pytestmark = pytest.mark.skip(reason="API tests disabled due to FastAPI TestClient compatibility issues")


class TestAPI:
    """Test FastAPI endpoints"""
    
    @pytest.fixture
    def client(self):
        """HTTP client for FastAPI testing"""
        return httpx.AsyncClient(app=app, base_url="http://testserver")
    
    @pytest.fixture
    def mock_user(self):
        """Mock user data for testing"""
        return {
            "user_id": 1,
            "username": "test@example.com",
            "marketplace": "us"
        }
    
    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        return {"Cookie": "auth_token=mock_jwt_token"}

    # Basic Health Endpoints
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "AudiPy API is running"
        assert data["version"] == "1.0.0"
    
    @pytest.mark.asyncio
    @patch('api.main.test_connection')
    async def test_health_endpoint_healthy(self, mock_test_connection, client):
        """Test health endpoint when database is healthy"""
        mock_test_connection.return_value = True
        
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
    
    @pytest.mark.asyncio
    @patch('api.main.test_connection')
    async def test_health_endpoint_unhealthy(self, mock_test_connection, client):
        """Test health endpoint when database is unhealthy"""
        mock_test_connection.return_value = False
        
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"] == "disconnected"

    # Phase 1: Authentication Tests
    @pytest.mark.asyncio
    @patch('api.main.ensure_user_exists')
    @patch('api.main.auth_service.authenticate_user')
    async def test_login_success(self, mock_authenticate, mock_ensure_user, client):
        """Test successful login without OTP"""
        mock_ensure_user.return_value = 1
        mock_authenticate.return_value = {
            'success': True,
            'message': 'Authentication successful',
            'requires_otp': False
        }
        
        response = await client.post(
            "/api/auth/login",
            json={
                "username": "test@example.com",
                "password": "password",
                "marketplace": "us"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Login successful"
        assert data["requires_otp"] is False
        assert "user" in data
    
    @pytest.mark.asyncio
    @patch('api.main.ensure_user_exists')
    @patch('api.main.auth_service.authenticate_user')
    def test_login_requires_otp(self, mock_authenticate, mock_ensure_user, client):
        """Test login that requires OTP"""
        mock_ensure_user.return_value = 1
        mock_authenticate.return_value = {
            'success': False,
            'message': 'Two-factor authentication required',
            'requires_otp': True
        }
        
        response = client.post(
            "/api/auth/login",
            json={
                "username": "test@example.com",
                "password": "password",
                "marketplace": "us"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["requires_otp"] is True
        assert "session_id" in data
    
    @pytest.mark.asyncio
    @patch('api.main.ensure_user_exists')
    @patch('api.main.auth_service.authenticate_user')
    async def test_verify_otp_success(self, mock_authenticate, mock_ensure_user, client):
        """Test successful OTP verification"""
        mock_ensure_user.return_value = 1
        mock_authenticate.return_value = {
            'success': True,
            'message': 'Authentication successful'
        }
        
        # First create an OTP session
        with patch.object(client.app, 'otp_sessions', {"test_session": {
            "username": "test@example.com",
            "password": "password",
            "marketplace": "us",
            "created_at": datetime.utcnow()
        }}):
            response = client.post(
                "/api/auth/verify-otp",
                json={
                    "session_id": "test_session",
                    "otp_code": "123456"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Authentication successful"
    
    @pytest.mark.asyncio
    @patch('api.main.get_current_user')
    async def test_get_current_user_authenticated(self, mock_get_user, client, mock_user):
        """Test getting current user when authenticated"""
        mock_get_user.return_value = mock_user
        
        response = await client.get("/api/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["user"]["user_id"] == 1
        assert data["user"]["username"] == "test@example.com"
    
    @pytest.mark.asyncio
    @patch('api.main.get_current_user')
    async def test_get_current_user_not_authenticated(self, mock_get_user, client):
        """Test getting current user when not authenticated"""
        mock_get_user.return_value = None
        
        response = await client.get("/api/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False
        assert data["user"] is None
    
    @pytest.mark.asyncio
    async def test_logout(self, client):
        """Test logout endpoint"""
        response = await client.post("/api/auth/logout")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Logged out successfully"

    # Phase 2: User Profile Tests
    @pytest.mark.asyncio
    @patch('api.main.get_current_user')
    @patch('api.main.get_db_connection')
    async def test_get_user_profile_authenticated(self, mock_db, mock_get_user, client, mock_user):
        """Test getting user profile when authenticated"""
        mock_get_user.return_value = mock_user
        
        # Mock database responses
        mock_cursor = Mock()
        mock_cursor.fetchone.side_effect = [
            {"user_id": 1, "username": "test@example.com", "email": "test@example.com", "created_at": datetime.now(), "updated_at": datetime.now()},
            {"language": "english", "marketplace": "us", "max_price": 12.66},
            {"marketplace": "us", "sync_status": "completed", "tokens_expires_at": datetime.now(), "last_sync": datetime.now()}
        ]
        mock_db.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        response = await client.get("/api/user/profile")
        
        assert response.status_code == 200
        data = response.json()
        assert "profile" in data
        assert "preferences" in data
        assert "audible_account" in data
    
    @pytest.mark.asyncio
    @patch('api.main.get_current_user')
    async def test_get_user_profile_not_authenticated(self, mock_get_user, client):
        """Test getting user profile when not authenticated"""
        mock_get_user.return_value = None
        
        response = await client.get("/api/user/profile")
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Not authenticated"

    # Phase 3: Library Management Tests
    @pytest.mark.asyncio
    @patch('api.main.get_current_user')
    @patch('api.main.get_db_connection')
    async def test_get_library_authenticated(self, mock_db, mock_get_user, client, mock_user):
        """Test getting library when authenticated"""
        mock_get_user.return_value = mock_user
        
        # Mock database responses
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {"total": 5}
        mock_cursor.fetchall.return_value = [
            {
                "asin": "B001", "title": "Test Book 1", "subtitle": None,
                "runtime_length_min": 600, "publication_datetime": datetime.now(),
                "language": "english", "content_type": "Product", "purchase_date": datetime.now(),
                "authors": "Author 1", "narrators": "Narrator 1", "series": None
            }
        ]
        mock_db.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        response = await client.get("/api/library")
        
        assert response.status_code == 200
        data = response.json()
        assert "books" in data
        assert "total_count" in data
        assert "page" in data
        assert "page_size" in data
        assert "has_next" in data
    
    @pytest.mark.asyncio
    @patch('api.main.get_current_user')
    async def test_get_library_not_authenticated(self, mock_get_user, client):
        """Test getting library when not authenticated"""
        mock_get_user.return_value = None
        
        response = await client.get("/api/library")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    @patch('api.main.get_current_user')
    @patch('api.main.get_user_sync_status')
    async def test_sync_library_success(self, mock_sync_status, mock_get_user, client, mock_user):
        """Test starting library sync"""
        mock_get_user.return_value = mock_user
        mock_sync_status.return_value = {"is_syncing": False}
        
        with patch('threading.Thread') as mock_thread:
            response = await client.post("/api/library/sync")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Library sync started"
    
    @pytest.mark.asyncio
    @patch('api.main.get_current_user')
    @patch('api.main.get_user_sync_status')
    async def test_sync_library_already_syncing(self, mock_sync_status, mock_get_user, client, mock_user):
        """Test starting library sync when already syncing"""
        mock_get_user.return_value = mock_user
        mock_sync_status.return_value = {"is_syncing": True}
        
        response = await client.post("/api/library/sync")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["message"] == "Sync already in progress"
    
    @pytest.mark.asyncio
    @patch('api.main.get_current_user')
    @patch('api.main.get_user_sync_status')
    @patch('api.main.get_db_connection')
    async def test_get_sync_status(self, mock_db, mock_sync_status, mock_get_user, client, mock_user):
        """Test getting sync status"""
        mock_get_user.return_value = mock_user
        mock_sync_status.return_value = {
            "is_syncing": False,
            "last_sync": "2024-01-01T00:00:00",
            "total_books": 0,
            "status_message": "Ready to sync"
        }
        
        # Mock database response
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {"total_books": 5}
        mock_db.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        response = await client.get("/api/library/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "is_syncing" in data
        assert "last_sync" in data
        assert "total_books" in data
        assert "status_message" in data

    # Error Handling Tests
    @pytest.mark.asyncio
    async def test_invalid_endpoint(self, client):
        """Test accessing invalid endpoint"""
        response = await client.get("/api/nonexistent")
        assert response.status_code == 404
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.options("/api/auth/login", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST"
        })
        # FastAPI handles CORS automatically, just check it doesn't error
        assert response.status_code in [200, 405]  # 405 is also acceptable for OPTIONS 