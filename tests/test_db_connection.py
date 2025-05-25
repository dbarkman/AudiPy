"""
Tests for database connection utilities
"""

import pytest
from unittest.mock import patch, Mock
from utils.db.connection import get_db_connection, test_connection as db_test_connection, DB_CONFIG


class TestDatabaseConnection:
    """Test database connection utilities"""
    
    def test_db_config_exists(self):
        """Test that database configuration exists"""
        assert DB_CONFIG is not None
        assert 'host' in DB_CONFIG
        assert 'database' in DB_CONFIG
        assert 'user' in DB_CONFIG
    
    @patch('utils.db.connection.mysql.connector.connect')
    def test_get_db_connection_success(self, mock_connect):
        """Test successful database connection"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        with get_db_connection() as conn:
            assert conn == mock_conn
        
        mock_connect.assert_called_once_with(**DB_CONFIG)
        mock_conn.close.assert_called_once()
    
    @patch('utils.db.connection.mysql.connector.connect')
    def test_get_db_connection_exception(self, mock_connect):
        """Test database connection with exception"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        with pytest.raises(Exception):
            with get_db_connection():
                raise Exception("Test exception")
        
        mock_conn.rollback.assert_called_once()
        mock_conn.close.assert_called_once()
    
    @patch('utils.db.connection.mysql.connector.connect')
    def test_test_connection_success(self, mock_connect):
        """Test successful connection test"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        result = db_test_connection()
        
        assert result is True
        mock_cursor.execute.assert_called_once_with("SELECT 1")
        mock_cursor.fetchone.assert_called_once()
        mock_cursor.close.assert_called_once()
    
    @patch('utils.db.connection.mysql.connector.connect')
    def test_test_connection_failure(self, mock_connect):
        """Test failed connection test"""
        mock_connect.side_effect = Exception("Connection failed")
        
        result = db_test_connection()
        
        assert result is False
    
    @patch('utils.db.connection.mysql.connector.connect')
    def test_connection_cleanup_on_error(self, mock_connect):
        """Test that connections are properly cleaned up on error"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        try:
            with get_db_connection():
                raise ValueError("Test error")
        except ValueError:
            pass
        
        mock_conn.rollback.assert_called_once()
        mock_conn.close.assert_called_once() 