"""
Pytest configuration and shared fixtures
"""

import pytest
import os
from unittest.mock import Mock, patch
from dotenv import load_dotenv
from utils.crypto_utils_simple import get_crypto_instance

# Load environment variables for testing
load_dotenv()


@pytest.fixture
def mock_db_connection():
    """Mock database connection for testing"""
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor


@pytest.fixture
def crypto_instance():
    """Get crypto instance for testing"""
    return get_crypto_instance()


@pytest.fixture
def sample_auth_data():
    """Sample authentication data for testing"""
    return {
        'website_cookies': {'test': 'cookie'},
        'adp_token': 'test_adp_token',
        'access_token': 'test_access_token',
        'refresh_token': 'test_refresh_token',
        'device_private_key': 'test_private_key',
        'store_authentication_cookie': {'store': 'cookie'},
        'device_info': {'device': 'info'},
        'customer_info': {'customer': 'info'},
        'expires': 1234567890,
        'locale_code': 'us',
        'with_username': False,
        'activation_bytes': None
    }


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing"""
    return 1


@pytest.fixture
def mock_audible_client():
    """Mock Audible client for testing"""
    mock_client = Mock()
    mock_client.get.return_value = {
        'total_size': 100,
        'items': []
    }
    return mock_client


@pytest.fixture
def mock_authenticator():
    """Mock Audible authenticator for testing"""
    mock_auth = Mock()
    mock_auth.website_cookies = {'test': 'cookie'}
    mock_auth.adp_token = 'test_adp_token'
    mock_auth.access_token = 'test_access_token'
    mock_auth.refresh_token = 'test_refresh_token'
    mock_auth.device_private_key = 'test_private_key'
    mock_auth.store_authentication_cookie = {'store': 'cookie'}
    mock_auth.device_info = {'device': 'info'}
    mock_auth.customer_info = {'customer': 'info'}
    mock_auth.expires = 1234567890
    mock_auth.with_username = False
    mock_auth.activation_bytes = None
    return mock_auth 