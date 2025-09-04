#!/usr/bin/env python3
"""
Pytest configuration file for web scraping bot tests

This file contains fixtures and configuration for pytest to use across all test files.
It sets up common test resources, mocks, and utilities to make testing more efficient.
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import project modules
from utils.logger import get_default_logger
from utils.security import Security
from utils.auth import UserAuth

@pytest.fixture
def mock_logger():
    """
    Fixture that provides a mock logger for testing
    
    Returns:
        MagicMock: A mock logger object that can be used to verify logging calls
    """
    logger = MagicMock()
    logger.debug = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    logger.critical = MagicMock()
    return logger

@pytest.fixture
def test_config():
    """
    Fixture that provides a test configuration
    
    Returns:
        dict: A configuration dictionary for testing
    """
    return {
        'security': {
            'secret_key': 'test_secret_key',
            'encryption_key_file': 'test_encryption.key',
            'jwt_algorithm': 'HS256',
            'jwt_expiration': 1  # 1 hour for testing
        },
        'auth': {
            'users_file': 'test_users.json',
            'session_timeout': 5,  # 5 minutes for testing
            'max_failed_attempts': 3,
            'lockout_duration': 5  # 5 minutes for testing
        },
        'scraper': {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'request_timeout': 5,
            'retry_count': 2,
            'retry_delay': 1
        },
        'targets': [
            {
                'name': 'test_target',
                'url': 'https://example.com',
                'selectors': {
                    'product': '.product',
                    'price': '.price',
                    'description': '.description'
                }
            }
        ]
    }

@pytest.fixture
def mock_security(test_config):
    """
    Fixture that provides a mock security module
    
    Args:
        test_config: The test configuration fixture
        
    Returns:
        MagicMock: A mock security object
    """
    with patch('utils.security.Security') as mock:
        security = Security(test_config['security'])
        # Mock security methods as needed
        security.encrypt_data = MagicMock(return_value='encrypted_data')
        security.decrypt_data = MagicMock(return_value={'test': 'data'})
        security.hash_password = MagicMock(return_value='hashed_password')
        security.verify_password = MagicMock(return_value=True)
        security.generate_token = MagicMock(return_value='test_token')
        security.verify_token = MagicMock(return_value={'username': 'test_user', 'role': 'user'})
        yield security

@pytest.fixture
def mock_response():
    """
    Fixture that provides a mock HTTP response
    
    Returns:
        MagicMock: A mock response object with common attributes
    """
    response = MagicMock()
    response.status_code = 200
    response.text = '<html><body><div class="product">Test Product</div></body></html>'
    response.json = MagicMock(return_value={'status': 'success'})
    return response