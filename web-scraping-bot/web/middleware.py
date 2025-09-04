#!/usr/bin/env python3
"""
Middleware for web application
"""

import os
import json
import functools
from pathlib import Path
from flask import request, redirect, url_for, session, abort, jsonify

# Import custom modules
from utils.auth import UserAuth
from utils.logger import get_default_logger
from utils.security import Security

# Initialize logger
logger = get_default_logger('web_middleware')

def load_config():
    """
    Load configuration from config file
    
    Returns:
        dict: Configuration
    """
    try:
        # Get project root directory
        project_root = Path(__file__).parent.parent
        config_path = project_root / 'config' / 'config.json'
        
        # Check if config file exists
        if not config_path.exists():
            logger.error(f"Configuration file not found at {config_path}")
            return {}
        
        # Load config
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        return config
    
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}

# Load configuration
config = load_config()

# Initialize authentication module
auth_config = config.get('auth', {})
auth = UserAuth(auth_config) if auth_config.get('enabled', False) else None

# Initialize security module
security_config = config.get('security', {})
security = Security(security_config)

def require_auth(f):
    """
    Decorator to require authentication for routes
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if authentication is enabled
        if not auth_config.get('enabled', False):
            return f(*args, **kwargs)
        
        # Check if user is authenticated
        session_id = session.get('session_id')
        if not session_id:
            # Redirect to login page for HTML requests
            if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
                return redirect(url_for('login', next=request.path))
            else:
                # Return 401 for AJAX requests
                return jsonify({'error': 'Authentication required'}), 401
        
        # Validate session
        user_session = auth.validate_session(session_id)
        if not user_session:
            # Clear session
            session.clear()
            
            # Redirect to login page for HTML requests
            if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
                return redirect(url_for('login', next=request.path))
            else:
                # Return 401 for AJAX requests
                return jsonify({'error': 'Authentication required'}), 401
        
        # Store user info in request
        request.user = user_session
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_role(role):
    """
    Decorator to require specific role for routes
    
    Args:
        role (str): Required role
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if authentication is enabled
            if not auth_config.get('enabled', False):
                return f(*args, **kwargs)
            
            # Check if user is authenticated
            if not hasattr(request, 'user'):
                # Redirect to login page for HTML requests
                if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
                    return redirect(url_for('login', next=request.path))
                else:
                    # Return 401 for AJAX requests
                    return jsonify({'error': 'Authentication required'}), 401
            
            # Check if user has required role
            if request.user.get('role') != role:
                # Return 403 for all requests
                if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
                    abort(403)
                else:
                    return jsonify({'error': 'Insufficient privileges'}), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator

def secure_headers(response):
    """
    Add secure headers to response
    
    Args:
        response: Flask response
        
    Returns:
        response: Modified response
    """
    # Check if secure headers are enabled
    if not security_config.get('secure_headers', True):
        return response
    
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Add Content-Security-Policy if configured
    csp = security_config.get('content_security_policy')
    if csp:
        response.headers['Content-Security-Policy'] = csp
    
    return response

def rate_limiter(key_func=None, limit=None, period=None):
    """
    Decorator to limit request rate
    
    Args:
        key_func (callable, optional): Function to generate rate limit key
        limit (int, optional): Maximum number of requests
        period (int, optional): Time window in seconds
    """
    # Use configured values if not provided
    rate_config = security_config.get('rate_limiting', {})
    if limit is None:
        limit = rate_config.get('max_requests', 100)
    if period is None:
        period = rate_config.get('time_window', 3600)
    
    # Default key function uses IP address
    if key_func is None:
        key_func = lambda: request.remote_addr
    
    def decorator(f):
        # Skip if rate limiting is disabled
        if not rate_config.get('enabled', True):
            return f
        
        # Use in-memory storage for simplicity
        # In production, use Redis or similar for distributed rate limiting
        if not hasattr(decorator, 'storage'):
            decorator.storage = {}
        
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if rate limiting is enabled
            if not rate_config.get('enabled', True):
                return f(*args, **kwargs)
            
            # Get rate limit key
            key = key_func()
            
            # Get current time
            import time
            now = time.time()
            
            # Initialize or clean up old requests
            if key not in decorator.storage:
                decorator.storage[key] = []
            
            # Remove expired timestamps
            decorator.storage[key] = [ts for ts in decorator.storage[key] if now - ts < period]
            
            # Check if limit exceeded
            if len(decorator.storage[key]) >= limit:
                logger.warning(f"Rate limit exceeded for {key}")
                
                # Return 429 Too Many Requests
                response = jsonify({'error': 'Rate limit exceeded'})
                response.status_code = 429
                response.headers['Retry-After'] = str(period)
                return response
            
            # Add current timestamp
            decorator.storage[key].append(now)
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator

def sanitize_input(f):
    """
    Decorator to sanitize request input
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Sanitize form data
        if request.form:
            for key, value in request.form.items():
                if isinstance(value, str):
                    request.form[key] = security.sanitize_input(value)
        
        # Sanitize query parameters
        if request.args:
            for key, value in request.args.items():
                if isinstance(value, str):
                    request.args[key] = security.sanitize_input(value)
        
        # Sanitize JSON data
        if request.is_json:
            data = request.get_json()
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, str):
                        data[key] = security.sanitize_input(value)
        
        return f(*args, **kwargs)
    
    return decorated_function

def setup_middleware(app):
    """
    Set up middleware for Flask application
    
    Args:
        app: Flask application
    """
    # Add secure headers to all responses
    app.after_request(secure_headers)
    
    # Log all requests
    @app.before_request
    def log_request():
        logger.info(f"{request.method} {request.path} from {request.remote_addr}")
    
    # Log all responses
    @app.after_request
    def log_response(response):
        logger.info(f"Response: {response.status_code}")
        return response
    
    # Handle errors
    @app.errorhandler(404)
    def not_found(e):
        logger.warning(f"404 Not Found: {request.path}")
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(403)
    def forbidden(e):
        logger.warning(f"403 Forbidden: {request.path}")
        return jsonify({'error': 'Forbidden'}), 403
    
    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"500 Server Error: {str(e)}")
        return jsonify({'error': 'Server error'}), 500