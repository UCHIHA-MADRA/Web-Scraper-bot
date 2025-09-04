#!/usr/bin/env python3
"""
Test helper utilities for web scraping bot tests

This module provides common utilities and helper functions for test cases,
including mock data generation, test data loading, and assertion helpers.
"""

import os
import json
import random
import string
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# Constants for test data
TEST_URLS = [
    'https://example.com/product/1',
    'https://example.com/product/2',
    'https://example.com/category/electronics',
    'https://otherdomain.com/search?q=test'
]

TEST_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
</head>
<body>
    <div class="product" id="product-1">
        <h2 class="title">Test Product 1</h2>
        <span class="price">$99.99</span>
        <div class="description">This is a test product description</div>
        <div class="stock">In Stock</div>
    </div>
    <div class="product" id="product-2">
        <h2 class="title">Test Product 2</h2>
        <span class="price">$149.99</span>
        <div class="description">Another test product description</div>
        <div class="stock">Out of Stock</div>
    </div>
</body>
</html>
"""

def generate_test_html(num_products=2, include_errors=False):
    """
    Generate test HTML with a variable number of products
    
    Args:
        num_products (int): Number of products to include in the HTML
        include_errors (bool): Whether to include malformed HTML for error testing
        
    Returns:
        str: Generated HTML content
    """
    soup = BeautifulSoup('<html><head><title>Test Page</title></head><body></body></html>', 'html.parser')
    body = soup.find('body')
    
    for i in range(1, num_products + 1):
        product_div = soup.new_tag('div', attrs={'class': 'product', 'id': f'product-{i}'})
        
        # Add title
        title = soup.new_tag('h2', attrs={'class': 'title'})
        title.string = f'Test Product {i}'
        product_div.append(title)
        
        # Add price
        price = soup.new_tag('span', attrs={'class': 'price'})
        price.string = f'${random.randint(10, 200)}.{random.randint(0, 99):02d}'
        product_div.append(price)
        
        # Add description
        desc = soup.new_tag('div', attrs={'class': 'description'})
        desc.string = f'Description for test product {i}'
        product_div.append(desc)
        
        # Add stock status
        stock = soup.new_tag('div', attrs={'class': 'stock'})
        stock.string = 'In Stock' if random.choice([True, False]) else 'Out of Stock'
        product_div.append(stock)
        
        body.append(product_div)
    
    # Add malformed HTML if requested
    if include_errors:
        error_div = soup.new_tag('div')
        error_div.append('<span>Unclosed span')
        body.append(error_div)
    
    return str(soup)

def generate_random_string(length=10):
    """
    Generate a random string of specified length
    
    Args:
        length (int): Length of the string to generate
        
    Returns:
        str: Random string
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def create_test_file(directory, filename, content):
    """
    Create a test file with specified content
    
    Args:
        directory (str): Directory to create the file in
        filename (str): Name of the file
        content (str): Content to write to the file
        
    Returns:
        str: Full path to the created file
    """
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    return filepath

def generate_test_config(num_targets=2):
    """
    Generate a test configuration with specified number of targets
    
    Args:
        num_targets (int): Number of scraping targets to include
        
    Returns:
        dict: Test configuration dictionary
    """
    config = {
        'security': {
            'secret_key': generate_random_string(32),
            'encryption_key_file': 'test_encryption.key',
            'jwt_algorithm': 'HS256',
            'jwt_expiration': 1
        },
        'auth': {
            'users_file': 'test_users.json',
            'session_timeout': 5,
            'max_failed_attempts': 3,
            'lockout_duration': 5
        },
        'scraper': {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'request_timeout': 5,
            'retry_count': 2,
            'retry_delay': 1,
            'cache_expiration': 3600
        },
        'targets': []
    }
    
    for i in range(1, num_targets + 1):
        target = {
            'name': f'test_target_{i}',
            'url': f'https://example.com/category/{i}',
            'selectors': {
                'product': '.product',
                'title': '.title',
                'price': '.price',
                'description': '.description',
                'stock': '.stock'
            }
        }
        config['targets'].append(target)
    
    return config

def assert_dict_contains_subset(subset, full_dict, path=''):
    """
    Assert that a dictionary contains all key-value pairs from a subset
    
    Args:
        subset (dict): The subset dictionary with expected key-value pairs
        full_dict (dict): The full dictionary to check against
        path (str): Current path for nested dictionaries (for error messages)
        
    Raises:
        AssertionError: If any key-value pair in subset is not in full_dict
    """
    for key, value in subset.items():
        current_path = f"{path}.{key}" if path else key
        assert key in full_dict, f"Key '{current_path}' not found in dictionary"
        
        if isinstance(value, dict) and isinstance(full_dict[key], dict):
            assert_dict_contains_subset(value, full_dict[key], current_path)
        else:
            assert full_dict[key] == value, f"Value mismatch at '{current_path}': expected {value}, got {full_dict[key]}"