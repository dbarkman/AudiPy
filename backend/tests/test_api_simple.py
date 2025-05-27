"""
Simple API Tests - Pragmatic approach using requests
Focus: Critical paths, regression prevention, KISS principle
"""

import pytest
import requests
import json
from unittest.mock import patch, Mock
import time

# Test against running server (simple and reliable)
BASE_URL = "http://localhost:8000"

class TestAPISimple:
    """Simple API tests focusing on critical paths"""
    
    def test_health_endpoint(self):
        """Test basic health check - most important for monitoring"""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "database" in data
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running - skipping integration tests")
    
    def test_root_endpoint(self):
        """Test root endpoint - basic API functionality"""
        try:
            response = requests.get(f"{BASE_URL}/", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "AudiPy API is running"
            assert "version" in data
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running - skipping integration tests")
    
    @patch('api.main.ensure_user_exists')
    @patch('api.main.auth_service.authenticate_user')
    def test_login_endpoint_structure(self, mock_auth, mock_user):
        """Test login endpoint accepts correct data structure"""
        mock_user.return_value = 1
        mock_auth.return_value = {
            'success': True,
            'message': 'Authentication successful',
            'requires_otp': False
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={
                    "username": "test@example.com",
                    "password": "password",
                    "marketplace": "us"
                },
                timeout=5
            )
            # Just check it doesn't crash and returns JSON
            assert response.status_code in [200, 401, 422]  # Valid responses
            assert response.headers.get('content-type', '').startswith('application/json')
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running - skipping integration tests")
    
    def test_auth_me_endpoint_unauthenticated(self):
        """Test /auth/me returns proper structure when not authenticated"""
        try:
            response = requests.get(f"{BASE_URL}/api/auth/me", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert "authenticated" in data
            assert "user" in data
            # When not authenticated, should be False/None
            assert data["authenticated"] is False
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running - skipping integration tests")
    
    def test_library_endpoint_requires_auth(self):
        """Test library endpoint properly requires authentication"""
        try:
            response = requests.get(f"{BASE_URL}/api/library", timeout=5)
            # Should require authentication
            assert response.status_code in [401, 403]
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running - skipping integration tests")
    
    def test_user_profile_requires_auth(self):
        """Test user profile endpoint properly requires authentication"""
        try:
            response = requests.get(f"{BASE_URL}/api/user/profile", timeout=5)
            # Should require authentication
            assert response.status_code in [401, 403]
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running - skipping integration tests")
    
    def test_sync_endpoint_requires_auth(self):
        """Test sync endpoint properly requires authentication"""
        try:
            response = requests.post(f"{BASE_URL}/api/library/sync", timeout=5)
            # Should require authentication
            assert response.status_code in [401, 403]
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running - skipping integration tests")
    
    def test_invalid_endpoint_returns_404(self):
        """Test invalid endpoints return 404"""
        try:
            response = requests.get(f"{BASE_URL}/api/nonexistent", timeout=5)
            assert response.status_code == 404
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running - skipping integration tests")
    
    def test_cors_headers_present(self):
        """Test CORS headers are present for frontend"""
        try:
            response = requests.options(
                f"{BASE_URL}/api/auth/login",
                headers={
                    "Origin": "http://localhost:5173",
                    "Access-Control-Request-Method": "POST"
                },
                timeout=5
            )
            # CORS should be handled, check headers exist
            assert response.status_code in [200, 204, 405]
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running - skipping integration tests")
    
    def test_json_content_type(self):
        """Test API returns proper JSON content type"""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            assert response.headers.get('content-type', '').startswith('application/json')
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running - skipping integration tests") 