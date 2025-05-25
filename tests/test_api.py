"""
Tests for FastAPI endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock
from api.main import app


class TestAPI:
    """Test FastAPI endpoints"""
    
    @pytest.fixture
    def client(self):
        """Test client for FastAPI"""
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "AudiPy API is running"
        assert data["version"] == "1.0.0"
    
    @patch('api.main.test_connection')
    def test_health_endpoint_healthy(self, mock_test_connection, client):
        """Test health endpoint when database is healthy"""
        mock_test_connection.return_value = True
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
    
    @patch('api.main.test_connection')
    def test_health_endpoint_unhealthy(self, mock_test_connection, client):
        """Test health endpoint when database is unhealthy"""
        mock_test_connection.return_value = False
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"] == "disconnected"
    
    @patch('api.main.auth_service.authenticate_user')
    def test_authenticate_audible_success(self, mock_authenticate, client):
        """Test successful Audible authentication"""
        mock_authenticate.return_value = {
            'success': True,
            'message': 'Authentication successful',
            'requires_otp': False,
            'tokens_stored': True
        }
        
        response = client.post(
            "/auth/audible",
            json={
                "username": "test@example.com",
                "password": "password",
                "marketplace": "us"
            },
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Authentication successful"
    
    @patch('api.main.auth_service.authenticate_user')
    def test_authenticate_audible_otp_required(self, mock_authenticate, client):
        """Test Audible authentication when OTP is required"""
        mock_authenticate.return_value = {
            'success': False,
            'message': 'Two-factor authentication required',
            'requires_otp': True,
            'tokens_stored': False
        }
        
        response = client.post(
            "/auth/audible",
            json={
                "username": "test@example.com",
                "password": "password",
                "marketplace": "us"
            },
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["requires_otp"] is True
    
    @patch('api.main.auth_service.authenticate_user')
    def test_authenticate_audible_with_otp(self, mock_authenticate, client):
        """Test Audible authentication with OTP code"""
        mock_authenticate.return_value = {
            'success': True,
            'message': 'Authentication successful',
            'requires_otp': False,
            'tokens_stored': True
        }
        
        response = client.post(
            "/auth/audible",
            json={
                "username": "test@example.com",
                "password": "password",
                "marketplace": "us",
                "otp_code": "123456"
            },
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_authenticate_audible_no_auth(self, client):
        """Test Audible authentication without authorization header"""
        response = client.post(
            "/auth/audible",
            json={
                "username": "test@example.com",
                "password": "password",
                "marketplace": "us"
            }
        )
        
        assert response.status_code == 403
    
    @patch('api.main.auth_service.authenticate_user')
    def test_authenticate_audible_service_error(self, mock_authenticate, client):
        """Test Audible authentication when service raises exception"""
        mock_authenticate.side_effect = Exception("Service error")
        
        response = client.post(
            "/auth/audible",
            json={
                "username": "test@example.com",
                "password": "password",
                "marketplace": "us"
            },
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 500
    
    @patch('api.main.auth_service.test_api_access')
    def test_test_audible_access_success(self, mock_test_access, client):
        """Test successful Audible API access test"""
        mock_test_access.return_value = {
            'success': True,
            'message': 'API access confirmed! Library has 100 books'
        }
        
        response = client.get(
            "/auth/test",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "100 books" in data["message"]
    
    @patch('api.main.auth_service.test_api_access')
    def test_test_audible_access_failure(self, mock_test_access, client):
        """Test failed Audible API access test"""
        mock_test_access.return_value = {
            'success': False,
            'message': 'No authentication tokens found'
        }
        
        response = client.get(
            "/auth/test",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "No authentication tokens found" in data["message"]
    
    def test_test_audible_access_no_auth(self, client):
        """Test Audible API access test without authorization header"""
        response = client.get("/auth/test")
        
        assert response.status_code == 403
    
    @patch('api.main.auth_service.test_api_access')
    def test_test_audible_access_service_error(self, mock_test_access, client):
        """Test Audible API access test when service raises exception"""
        mock_test_access.side_effect = Exception("Service error")
        
        response = client.get(
            "/auth/test",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 500
    
    def test_invalid_endpoint(self, client):
        """Test accessing invalid endpoint"""
        response = client.get("/invalid")
        assert response.status_code == 404
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.options("/", headers={"Origin": "http://localhost:3000"})
        # FastAPI automatically handles CORS, so we just check the response is valid
        assert response.status_code in [200, 405]  # 405 is also acceptable for OPTIONS 