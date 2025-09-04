#!/usr/bin/env python3
"""
Caching module for web scraping bot

This module provides a multi-level caching system to improve performance
by storing and retrieving previously fetched web content and parsed data.

Features:
- HTTP request caching using requests-cache with SQLite backend
- In-memory caching for faster access to frequently used data
- File-based persistent caching for data between application restarts
- Automatic cache expiration and management
- Cache statistics tracking and reporting

Usage:
    from utils.cache import get_default_cache
    
    # Get the default cache instance
    cache = get_default_cache()
    
    # Try to get data from cache
    data = cache.get(url)
    if data is None:
        # Fetch and process data
        data = fetch_and_process(url)
        # Store in cache
        cache.set(url, data)
"""
import os
import json
import time
from datetime import datetime, timedelta
import hashlib
import requests_cache
from typing import Dict, Any, Optional, Union

from utils.logger import get_default_logger

class ScraperCache:
    """
    Caching system for web scraping operations
    
    This class provides three levels of caching:
    1. HTTP request caching using requests-cache with SQLite backend
    2. In-memory caching for fast access to frequently used data
    3. File-based JSON caching for persistence between application restarts
    
    The caching system automatically handles expiration of cached items
    and provides methods for clearing specific URLs or the entire cache.
    
    Attributes:
        cache_dir (str): Directory to store cache files
        expiration (int): Cache expiration time in seconds
        memory_cache (dict): In-memory cache for parsed content
        logger: Logger instance for logging cache operations
    
    Example:
        cache = ScraperCache(cache_dir='cache', expiration=3600)
        
        # Try to get data from cache
        data = cache.get('https://example.com')
        
        # If not in cache, fetch and store
        if data is None:
            data = fetch_data('https://example.com')
            cache.set('https://example.com', data)
    """
    
    def __init__(self, cache_dir: str = 'cache', expiration: int = 3600):
        """
        Initialize the cache system
        
        Args:
            cache_dir (str): Directory to store cache files
            expiration (int): Cache expiration time in seconds (default: 1 hour)
        """
        self.cache_dir = cache_dir
        self.expiration = expiration
        self.memory_cache = {}
        self.logger = get_default_logger('cache')
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize requests-cache
        self._setup_requests_cache()
    
    def _setup_requests_cache(self):
        """
        Set up requests-cache for HTTP request caching
        """
        cache_file = os.path.join(self.cache_dir, 'http_cache')
        requests_cache.install_cache(
            cache_file,
            backend='sqlite',
            expire_after=self.expiration
        )
        self.logger.info(f"HTTP request cache initialized at {cache_file}")
    
    def _generate_key(self, url: str, params: Optional[Dict] = None) -> str:
        """
        Generate a unique cache key for a URL and parameters
        
        Args:
            url (str): The URL to cache
            params (dict, optional): Additional parameters that affect the content
        
        Returns:
            str: A unique hash key for the URL and parameters
        """
        # Create a string representation of the URL and parameters
        key_data = url
        if params:
            key_data += json.dumps(params, sort_keys=True)
        
        # Generate a hash of the key data
        return hashlib.md5(key_data.encode('utf-8')).hexdigest()
    
    def get(self, url: str, params: Optional[Dict] = None) -> Optional[Any]:
        """
        Get cached content for a URL and parameters
        
        Args:
            url (str): The URL to retrieve from cache
            params (dict, optional): Additional parameters that affect the content
        
        Returns:
            Any: The cached content, or None if not found or expired
        """
        key = self._generate_key(url, params)
        
        # Check memory cache first
        if key in self.memory_cache:
            cache_entry = self.memory_cache[key]
            # Check if the entry is still valid
            if time.time() < cache_entry['expiry']:
                self.logger.debug(f"Cache hit for {url} (memory cache)")
                return cache_entry['data']
            else:
                # Remove expired entry
                del self.memory_cache[key]
        
        # Check file cache
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache_entry = json.load(f)
                
                # Check if the entry is still valid
                if time.time() < cache_entry['expiry']:
                    # Add to memory cache for faster access next time
                    self.memory_cache[key] = cache_entry
                    self.logger.debug(f"Cache hit for {url} (file cache)")
                    return cache_entry['data']
            except (json.JSONDecodeError, KeyError) as e:
                self.logger.warning(f"Error reading cache file {cache_file}: {e}")
        
        self.logger.debug(f"Cache miss for {url}")
        return None
    
    def set(self, url: str, data: Any, params: Optional[Dict] = None) -> None:
        """Store content in cache for a URL and parameters
        
        Args:
            url (str): The URL to cache
            data (Any): The data to cache
            params (dict, optional): Additional parameters that affect the content
        """
        key = self._generate_key(url, params)
        expiry = time.time() + self.expiration
        
        # Convert datetime objects to ISO format strings for JSON serialization
        serializable_data = self._prepare_for_serialization(data)
        
        # Create cache entry
        cache_entry = {
            'url': url,
            'params': params,
            'data': serializable_data,
            'expiry': expiry,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in memory cache
        self.memory_cache[key] = cache_entry
        
        # Store in file cache
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_entry, f)
            self.logger.debug(f"Cached content for {url}")
        except Exception as e:
            self.logger.error(f"Error writing to cache file {cache_file}: {e}")
            
    def _prepare_for_serialization(self, data):
        """Prepare data for JSON serialization by converting non-serializable types
        
        This method recursively processes data structures (dictionaries and lists)
        and converts non-serializable types like datetime objects to serializable
        formats (ISO 8601 strings).
        
        Args:
            data: The data to prepare for serialization, can be any Python object
            
        Returns:
            The serializable version of the data with all non-serializable types converted
            
        Example:
            data = {'timestamp': datetime.now(), 'values': [1, 2, 3]}
            serializable_data = self._prepare_for_serialization(data)
            # Result: {'timestamp': '2023-01-01T12:00:00', 'values': [1, 2, 3]}
        """
        if isinstance(data, dict):
            return {k: self._prepare_for_serialization(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._prepare_for_serialization(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            return data
    
    def clear(self, url: Optional[str] = None, params: Optional[Dict] = None) -> None:
        """
        Clear cache entries
        
        Args:
            url (str, optional): Specific URL to clear from cache
            params (dict, optional): Additional parameters for the URL
        
        If URL is provided, only that specific cache entry is cleared.
        If URL is None, the entire cache is cleared.
        """
        if url:
            # Clear specific URL
            key = self._generate_key(url, params)
            
            # Clear from memory cache
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            # Clear from file cache
            cache_file = os.path.join(self.cache_dir, f"{key}.json")
            if os.path.exists(cache_file):
                os.remove(cache_file)
            
            self.logger.info(f"Cleared cache for {url}")
        else:
            # Clear all memory cache
            self.memory_cache = {}
            
            # Clear all file cache
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    os.remove(os.path.join(self.cache_dir, filename))
            
            # Clear requests-cache
            requests_cache.clear()
            
            self.logger.info("Cleared all cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            dict: Statistics about the cache usage
        """
        # Count file cache entries
        file_count = sum(1 for f in os.listdir(self.cache_dir) if f.endswith('.json'))
        
        # Get requests-cache stats - newer versions of requests_cache don't have get_stats()
        # so we'll provide default values
        try:
            # Try to get stats from the CachedSession if available
            if hasattr(requests_cache, 'CachedSession'):
                session = requests_cache.CachedSession()
                hits = getattr(session, 'cache_hits', 0)
                misses = getattr(session, 'cache_misses', 0)
                requests_stats = {'hits': hits, 'misses': misses, 'urls': hits + misses}
            else:
                # Fallback to default values
                requests_stats = {'hits': 0, 'misses': 0, 'urls': 0}
        except Exception as e:
            self.logger.warning(f"Could not get requests-cache stats: {e}")
            requests_stats = {'hits': 0, 'misses': 0, 'urls': 0}
        
        return {
            'memory_cache_entries': len(self.memory_cache),
            'file_cache_entries': file_count,
            'http_requests': {
                'hits': requests_stats.get('hits', 0),
                'misses': requests_stats.get('misses', 0),
                'total': requests_stats.get('urls', 0)
            },
            'cache_dir': self.cache_dir,
            'expiration': self.expiration
        }

# Create a default cache instance (singleton pattern)
_default_cache = None

def get_default_cache(cache_dir: str = 'cache', expiration: int = 3600) -> ScraperCache:
    """
    Get or create the default cache instance (singleton pattern)
    
    This function implements the singleton pattern to ensure only one
    cache instance is created and reused throughout the application.
    The first call creates the instance with the provided parameters,
    and subsequent calls return the same instance regardless of parameters.
    
    Args:
        cache_dir (str): Directory to store cache files (only used on first call)
        expiration (int): Cache expiration time in seconds (only used on first call)
    
    Returns:
        ScraperCache: The default cache instance
        
    Example:
        # In module A
        cache = get_default_cache(cache_dir='custom_cache')
        
        # In module B - returns the same instance created in module A
        cache = get_default_cache()  # Parameters are ignored after first call
    """
    global _default_cache
    if _default_cache is None:
        _default_cache = ScraperCache(cache_dir, expiration)
    return _default_cache