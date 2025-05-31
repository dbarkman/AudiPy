"""
Simple tests for Phase 4 recommendation system
Focus: Core functionality, KISS principle, pragmatic testing
"""

import pytest
from unittest.mock import patch, Mock
import json
from datetime import datetime


class TestRecommendationCore:
    """Test core recommendation functionality - simple and focused"""
    
    def test_recommendation_confidence_scores(self):
        """Test confidence score calculation - core business logic"""
        # Import here to avoid module loading issues
        from phase4_generate_recommendations import RecommendationGenerator
        
        generator = RecommendationGenerator()
        
        # Test the confidence scoring logic
        assert generator.calculate_confidence_score('series', 'Test') == 1.0
        assert generator.calculate_confidence_score('author', 'Test') == 0.8
        assert generator.calculate_confidence_score('narrator', 'Test') == 0.6
        assert generator.calculate_confidence_score('unknown', 'Test') == 0.5
    
    def test_book_ownership_detection(self):
        """Test duplicate detection - prevents recommending owned books"""
        from phase4_generate_recommendations import RecommendationGenerator
        
        generator = RecommendationGenerator()
        generator.user_books = {'B001', 'B002'}
        generator.user_titles = {'existing book'}
        
        # Test ASIN match
        owned_book = {'asin': 'B001', 'title': 'Some Title'}
        assert generator.is_book_owned(owned_book) is True
        
        # Test title match
        title_match = {'asin': 'B999', 'title': 'Existing Book'}
        assert generator.is_book_owned(title_match) is True
        
        # Test not owned
        new_book = {'asin': 'B999', 'title': 'New Book'}
        assert generator.is_book_owned(new_book) is False
    
    def test_purchase_method_logic(self):
        """Test cash vs credits recommendation logic"""
        from phase4_generate_recommendations import RecommendationGenerator
        
        generator = RecommendationGenerator()
        generator.user_preferences = {'max_price': 12.66}
        generator.user_id = 1
        
        # Mock database connection for store_recommendation
        with patch('phase4_generate_recommendations.mysql.connector.connect'):
            mock_connection = Mock()
            mock_cursor = Mock()
            mock_cursor.fetchone.return_value = (123,)  # Book exists
            mock_connection.cursor.return_value = mock_cursor
            generator.db = mock_connection
            
            # Test cash recommendation (price under limit)
            result = generator.store_recommendation('B001', 'author', 'Test', 0.8, 9.99)
            
            # Verify the call included 'cash' as purchase method
            calls = mock_cursor.execute.call_args_list
            cash_call = any('cash' in str(call) for call in calls)
            assert cash_call is True
    
    @patch('phase4_generate_recommendations.mysql.connector.connect')
    def test_database_connection_handling(self, mock_connect):
        """Test database connection - critical for reliability"""
        from phase4_generate_recommendations import RecommendationGenerator
        
        generator = RecommendationGenerator()
        
        # Test successful connection
        mock_connection = Mock()
        mock_connect.return_value = mock_connection
        
        result = generator.connect_db()
        assert result is True
        assert generator.db == mock_connection
        
        # Test connection failure
        mock_connect.side_effect = Exception("DB Error")
        result = generator.connect_db()
        assert result is False


class TestRecommendationAPI:
    """Test API endpoints - simple integration tests"""
    
    @pytest.mark.asyncio
    @patch('api.main.get_current_user')
    @patch('api.main.get_db_connection')
    async def test_get_recommendations_basic(self, mock_db, mock_get_user):
        """Test basic recommendations endpoint - most important API test"""
        from api.main import get_recommendations
        
        # Setup mocks
        mock_user = {"user_id": 1}
        mock_get_user.return_value = mock_user
        
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {'total': 1}
        mock_cursor.fetchall.return_value = [{
            'asin': 'B001',
            'title': 'Test Book',
            'subtitle': None,
            'runtime_length_min': 480,
            'language': 'english',
            'suggestion_type': 'author',
            'source_name': 'Test Author',
            'confidence_score': 0.8,
            'purchase_method': 'credits',
            'generated_at': datetime.now(),
            'authors': 'Test Author',
            'narrators': 'Test Narrator',
            'series': None
        }]
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__.return_value = mock_connection
        
        mock_request = Mock()
        
        # Test the endpoint
        result = await get_recommendations(mock_request)
        
        # Verify basic functionality
        assert result.total_count == 1
        assert len(result.recommendations) == 1
        assert result.recommendations[0].title == 'Test Book'
        assert result.recommendations[0].confidence_score == 0.8
    
    @pytest.mark.asyncio
    @patch('api.main.get_current_user')
    async def test_recommendations_requires_auth(self, mock_get_user):
        """Test authentication requirement - security critical"""
        from api.main import get_recommendations
        from fastapi import HTTPException
        
        mock_get_user.return_value = None
        mock_request = Mock()
        
        # Should raise authentication error
        with pytest.raises(HTTPException) as exc_info:
            await get_recommendations(mock_request)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    @patch('api.main.get_current_user')
    @patch('api.main.get_user_recommendation_status')
    async def test_generate_recommendations_trigger(self, mock_status, mock_get_user):
        """Test recommendation generation trigger - core workflow"""
        from api.main import generate_recommendations
        
        mock_user = {"user_id": 1}
        mock_get_user.return_value = mock_user
        mock_status.return_value = {'is_generating': False}
        
        mock_request = Mock()
        
        with patch('api.main.threading.Thread') as mock_thread:
            result = await generate_recommendations(mock_request)
        
        # Verify generation was triggered
        assert result['success'] is True
        assert 'started' in result['message']
        mock_thread.assert_called_once()


class TestRecommendationData:
    """Test data structures - ensure API compatibility"""
    
    def test_recommendation_book_model(self):
        """Test RecommendationBook data model - API contract"""
        from api.main import RecommendationBook
        
        # Test creating recommendation with required fields
        rec = RecommendationBook(
            asin='B001',
            title='Test Book',
            authors=['Author 1'],
            narrators=['Narrator 1'],
            recommendation_type='author',
            source_name='Author 1',
            confidence_score=0.8,
            purchase_method='credits',
            generated_at='2023-01-01T00:00:00Z'
        )
        
        # Verify essential fields
        assert rec.asin == 'B001'
        assert rec.title == 'Test Book'
        assert rec.recommendation_type == 'author'
        assert rec.confidence_score == 0.8
        assert len(rec.authors) == 1
    
    def test_recommendations_response_model(self):
        """Test RecommendationsResponse structure - API contract"""
        from api.main import RecommendationsResponse, RecommendationBook
        
        # Create sample recommendation
        rec = RecommendationBook(
            asin='B001',
            title='Test',
            authors=[],
            narrators=[],
            recommendation_type='author',
            source_name='Test',
            confidence_score=0.8,
            purchase_method='credits',
            generated_at='2023-01-01T00:00:00Z'
        )
        
        # Test response structure
        response = RecommendationsResponse(
            recommendations=[rec],
            total_count=1,
            page=1,
            page_size=20,
            has_next=False
        )
        
        assert len(response.recommendations) == 1
        assert response.total_count == 1
        assert response.has_next is False


# Simple integration test
@pytest.mark.integration
def test_recommendation_system_components_exist():
    """Test that all recommendation system components can be imported"""
    # Test core generator
    from phase4_generate_recommendations import RecommendationGenerator
    generator = RecommendationGenerator()
    assert generator is not None
    
    # Test API models
    from api.main import RecommendationBook, RecommendationsResponse
    assert RecommendationBook is not None
    assert RecommendationsResponse is not None
    
    # Test API endpoints exist
    from api.main import get_recommendations, generate_recommendations
    assert get_recommendations is not None
    assert generate_recommendations is not None 