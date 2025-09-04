#!/usr/bin/env python3
"""
Unit tests for cache functionality

This module contains comprehensive tests for the ScraperCache class,
verifying all aspects of the caching system including initialization,
key generation, memory and file caching, expiration, clearing, and
statistics reporting.

Test coverage includes:
- Cache initialization and configuration
- Key generation algorithm
- Memory cache operations (get/set)
- File cache operations (get/set)
- Cache expiration functionality
- Clearing specific URLs from cache
- Clearing all cache entries
- Cache statistics reporting
"""
import pytest
import os
import json
import time
from unittest.mock import patch, mock_open, MagicMock

from utils.cache import ScraperCache, get_default_cache

class TestCache:
    @pytest.fixture
    def cache_instance(self):
        """Create a cache instance for testing
        
        Sets up a ScraperCache instance with a test directory and
        60-second expiration time for use in tests. Uses mocking
        to avoid actual filesystem operations during testing.
        """
        with patch('utils.cache.os.makedirs'):
            with patch('utils.cache.requests_cache.install_cache'):
                cache = ScraperCache(cache_dir='test_cache', expiration=60)
                return cache
    
    def test_init(self, cache_instance):
        """Test cache initialization
        
        Verifies that the cache is properly initialized with the
        correct cache directory, expiration time, and an empty
        memory cache dictionary.
        """
        assert cache_instance.cache_dir == 'test_cache'
        assert cache_instance.expiration == 60
        assert cache_instance.memory_cache == {}
    
    def test_generate_key(self, cache_instance):
        """Test key generation algorithm
        
        Verifies that the key generation method produces consistent,
        non-empty string keys for URLs. The keys are used as identifiers
        for cached content in both memory and file caches.
        """
        # Test with URL only
        key1 = cache_instance._generate_key('https://example.com')
        assert isinstance(key1, str)
        assert len(key1) > 0
        
        # Test with URL and params
        key2 = cache_instance._generate_key('https://example.com', {'param': 'value'})
        assert isinstance(key2, str)
        assert len(key2) > 0
        
        # Different URLs should generate different keys
        key3 = cache_instance._generate_key('https://different.com')
        assert key1 != key3
        
        # Same URL with different params should generate different keys
        key4 = cache_instance._generate_key('https://example.com', {'param': 'different'})
        assert key2 != key4
    
    def test_set_and_get_memory_cache(self, cache_instance):
        """Test setting and getting from memory cache
        
        Verifies that the memory cache correctly stores and retrieves data.
        Tests that after setting data, the cache returns the correct data
        when requested using the same URL.
        """
        url = 'https://example.com'
        data = {'result': 'test_data'}
        
        # Set cache
        cache_instance.set(url, data)
        
        # Get from cache
        cached_data = cache_instance.get(url)
        assert cached_data == data
    
    @patch('utils.cache.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"url": "https://example.com", "data": {"result": "test_data"}, "expiry": 9999999999, "timestamp": "2023-01-01T00:00:00", "params": null}')
    def test_get_file_cache(self, mock_file, mock_exists, cache_instance):
        """Test getting from file cache
        
        Verifies that the file cache correctly retrieves data from disk.
        Uses mocking to simulate file operations without actual filesystem access.
        Tests that data is properly deserialized when retrieved from the file cache.
        """
        mock_exists.return_value = True
        
        url = 'https://example.com'
        cached_data = cache_instance.get(url)
        
        assert cached_data == {"result": "test_data"}
        mock_exists.assert_called_once()
        mock_file.assert_called_once()
    
    def test_cache_expiration(self, cache_instance):
        """Test cache expiration functionality
        
        Verifies that expired cache entries are correctly identified and not returned.
        Sets a very short expiration time (100ms), adds data to the cache,
        waits for the expiration period to pass, then verifies the data
        is no longer returned from the cache.
        """
        url = 'https://example.com'
        data = {'result': 'test_data'}
        
        # Set cache with short expiration
        cache_instance.expiration = 0.1  # 100ms
        cache_instance.set(url, data)
        
        # Verify it's in cache initially
        assert cache_instance.get(url) == data
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Should be expired now
        assert cache_instance.get(url) is None
    
    @patch('utils.cache.os.path.exists')
    @patch('utils.cache.os.remove')
    def test_clear_specific_url(self, mock_remove, mock_exists, cache_instance):
        """Test clearing specific URL from cache
        
        Verifies that the clear method correctly removes a specific URL from both
        memory and file caches. Tests that after clearing, the URL is no longer
        present in the memory cache and the corresponding cache file is removed.
        """
        url = 'https://example.com'
        data = {'result': 'test_data'}
        
        # Set cache
        cache_instance.set(url, data)
        
        # Verify it's in memory cache
        assert url in [cache_instance.memory_cache[k]['url'] for k in cache_instance.memory_cache]
        
        # Mock file existence
        mock_exists.return_value = True
        
        # Clear cache for specific URL
        cache_instance.clear(url)
        
        # Verify it's removed from memory cache
        assert url not in [cache_instance.memory_cache.get(k, {}).get('url') for k in cache_instance.memory_cache]
        
        # Verify file was removed
        mock_exists.assert_called_once()
        mock_remove.assert_called_once()
    
    @patch('utils.cache.os.listdir')
    @patch('utils.cache.os.remove')
    @patch('utils.cache.requests_cache.clear')
    def test_clear_all(self, mock_requests_clear, mock_remove, mock_listdir, cache_instance):
        """Test clearing all cache entries
        
        Verifies that the clear method without a URL parameter correctly removes
        all entries from memory cache, file cache, and requests cache. Tests that
        after clearing, the memory cache is empty, all JSON cache files are removed,
        and the requests_cache is cleared.
        """
        # Set up memory cache
        cache_instance.memory_cache = {
            'key1': {'url': 'https://example1.com', 'data': 'data1'},
            'key2': {'url': 'https://example2.com', 'data': 'data2'}
        }
        
        # Mock file listing
        mock_listdir.return_value = ['file1.json', 'file2.json', 'other.txt']
        
        # Clear all cache
        cache_instance.clear()
        
        # Verify memory cache is cleared
        assert cache_instance.memory_cache == {}
        
        # Verify files were removed (only .json files)
        assert mock_remove.call_count == 2
        
        # Verify requests_cache was cleared
        mock_requests_clear.assert_called_once()
    
    @patch('utils.cache.os.listdir')
    @patch('utils.cache.requests_cache.get_stats')
    def test_get_stats(self, mock_get_stats, mock_listdir, cache_instance):
        """Test cache statistics reporting
        
        Verifies that the get_stats method correctly reports statistics about
        the cache, including the number of memory entries, file entries,
        HTTP request hits and misses, cache directory path, and expiration time.
        Tests that the reported statistics match the expected values based on
        the current cache state.
        """
        # Set up memory cache
        cache_instance.memory_cache = {
            'key1': {'url': 'https://example1.com', 'data': 'data1'},
            'key2': {'url': 'https://example2.com', 'data': 'data2'}
        }
        
        # Mock file listing
        mock_listdir.return_value = ['file1.json', 'file2.json', 'file3.json', 'other.txt']
        
        # Mock requests_cache stats
        mock_get_stats.return_value = {'hits': 10, 'misses': 5, 'urls': 15}
        
        # Get stats
        stats = cache_instance.get_stats()
        
        # Verify stats
        assert stats['memory_cache_entries'] == 2
        assert stats['file_cache_entries'] == 3  # Only .json files
        assert stats['http_requests']['hits'] == 10
        assert stats['http_requests']['misses'] == 5
        assert stats['http_requests']['total'] == 15
        assert stats['cache_dir'] == 'test_cache'
        assert stats['expiration'] == 60
    
    @patch('utils.cache.ScraperCache')
    def test_get_default_cache(self, mock_scraper_cache):
        """Test getting default cache instance"""
        mock_instance = MagicMock()
        mock_scraper_cache.return_value = mock_instance
        
        # First call should create a new instance
        with patch('utils.cache._default_cache', None):
            cache1 = get_default_cache()
            mock_scraper_cache.assert_called_once()
            assert cache1 == mock_instance
        
        # Second call should return the same instance
        with patch('utils.cache._default_cache', mock_instance):
            cache2 = get_default_cache()
            # Should not create a new instance
            assert mock_scraper_cache.call_count == 1
            assert cache2 == mock_instance