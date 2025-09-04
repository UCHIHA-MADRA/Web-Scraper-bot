#!/usr/bin/env python3
"""
Unit tests for scraper functionality

This module contains comprehensive tests for the WebScrapingBot class,
including configuration loading, request handling, parsing logic,
and error handling during the scraping process.
"""
import pytest
import requests
from unittest.mock import patch, MagicMock

from Web_Scraper import WebScrapingBot
from utils.exceptions import ScraperError, RequestError

@pytest.fixture
def web_scraper(test_config, mock_logger):
    """
    Fixture that provides a configured WebScrapingBot instance
    
    Args:
        test_config: The test configuration fixture
        mock_logger: The mock logger fixture
        
    Returns:
        WebScrapingBot: A configured scraper instance for testing
    """
    with patch('Web_Scraper.get_default_logger', return_value=mock_logger):
        bot = WebScrapingBot(config=test_config)
        return bot

class TestScraper:
    def test_config_loading(self, web_scraper, test_config):
        """Test configuration loading"""
        assert web_scraper.config is not None
        assert 'targets' in web_scraper.config
        assert web_scraper.config['targets'][0]['name'] == 'test_target'
        assert web_scraper.config['scraper']['user_agent'] == test_config['scraper']['user_agent']
    
    @patch('requests.get')
    def test_fetch_url_success(self, mock_get, web_scraper, mock_response):
        """Test successful URL fetching"""
        mock_get.return_value = mock_response
        response = web_scraper.fetch_url('https://example.com')
        
        mock_get.assert_called_once()
        assert response.status_code == 200
        assert '<div class="product">Test Product</div>' in response.text
    
    @patch('requests.get')
    def test_fetch_url_retry(self, mock_get, web_scraper):
        """Test URL fetching with retries"""
        # First call raises exception, second succeeds
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.side_effect = [requests.exceptions.RequestException, mock_response]
        
        response = web_scraper.fetch_url('https://example.com')
        
        assert mock_get.call_count == 2
        assert response.status_code == 200
    
    @patch('requests.get')
    def test_fetch_url_failure(self, mock_get, web_scraper):
        """Test URL fetching failure"""
        mock_get.side_effect = requests.exceptions.RequestException('Connection error')
        
        with pytest.raises(RequestError):
            web_scraper.fetch_url('https://example.com')
        
        assert mock_get.call_count == web_scraper.config['scraper']['retry_count'] + 1
    
    def test_parse_content(self, web_scraper, mock_response):
        """Test content parsing"""
        results = web_scraper.parse_content(
            mock_response, 
            selectors={
                'product': '.product'
            }
        )
        
        assert results is not None
        assert 'product' in results
        assert results['product'] == 'Test Product'
    
    def test_parse_content_missing_selector(self, web_scraper, mock_response):
        """Test content parsing with missing selector"""
        results = web_scraper.parse_content(
            mock_response, 
            selectors={
                'nonexistent': '.nonexistent'
            }
        )
        
        assert results is not None
        assert 'nonexistent' in results
        assert results['nonexistent'] is None
    
    @patch('Web_Scraper.WebScrapingBot.fetch_url')
    @patch('Web_Scraper.WebScrapingBot.parse_content')
    def test_scrape_target(self, mock_parse, mock_fetch, web_scraper, mock_response):
        """Test scraping a target"""
        mock_fetch.return_value = mock_response
        mock_parse.return_value = {'product': 'Test Product'}
        
        target = web_scraper.config['targets'][0]
        result = web_scraper.scrape_target(target)
        
        mock_fetch.assert_called_once_with(target['url'])
        mock_parse.assert_called_once()
        assert result == {'product': 'Test Product'}
    
    @patch('Web_Scraper.WebScrapingBot.fetch_url')
    def test_scrape_target_fetch_error(self, mock_fetch, web_scraper):
        """Test scraping a target with fetch error"""
        mock_fetch.side_effect = RequestError('Failed to fetch URL')
        
        target = web_scraper.config['targets'][0]
        with pytest.raises(ScraperError):
            web_scraper.scrape_target(target)