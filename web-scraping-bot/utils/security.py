#!/usr/bin/env python3
"""
Security module for web scraping bot providing authentication, encryption, and data protection
"""

import os
import base64
import hashlib
import secrets
import json
from datetime import datetime, timedelta
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Import custom modules
from utils.logger import get_default_logger
from utils.exceptions import SecurityError

class Security:
    """
    Security class providing authentication, encryption, and data protection
    """
    def __init__(self, config=None):
        """
        Initialize security module
        
        Args:
            config (dict, optional): Security configuration
        """
        self.config = config or {}
        self.logger = get_default_logger('security')
        
        # Set up configuration
        self.secret_key = self.config.get('secret_key', os.environ.get('SECRET_KEY'))
        if not self.secret_key:
            self.secret_key = secrets.token_hex(32)
            self.logger.warning("No secret key provided, generated a temporary one")
        
        # Initialize encryption key
        self.encryption_key = self._get_or_create_encryption_key()
        
        # JWT settings
        self.jwt_algorithm = self.config.get('jwt_algorithm', 'HS256')
        self.jwt_expiration = self.config.get('jwt_expiration', 24)  # hours
        
        self.logger.info("Security module initialized")
    
    def _get_or_create_encryption_key(self):
        """
        Get or create encryption key
        
        Returns:
            bytes: Encryption key
        """
        key_file = self.config.get('encryption_key_file', 'encryption.key')
        key_dir = self.config.get('key_dir', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config'))
        key_path = os.path.join(key_dir, key_file)
        
        # Create directory if it doesn't exist
        os.makedirs(key_dir, exist_ok=True)
        
        try:
            # Try to load existing key
            if os.path.exists(key_path):
                with open(key_path, 'rb') as f:
                    key = f.read()
                    self.logger.info("Loaded existing encryption key")
                    return key
            
            # Generate new key
            key = Fernet.generate_key()
            
            # Save key to file with restricted permissions
            with open(key_path, 'wb') as f:
                f.write(key)
            
            # Set file permissions to be restrictive (owner read-only)
            try:
                os.chmod(key_path, 0o400)
            except Exception as e:
                self.logger.warning(f"Could not set restrictive permissions on key file: {e}")
            
            self.logger.info("Generated and saved new encryption key")
            return key
            
        except Exception as e:
            self.logger.error(f"Error handling encryption key: {e}")
            # Fallback to derived key if file operations fail
            salt = b'web_scraper_salt'
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.secret_key.encode()))
            self.logger.warning("Using derived encryption key as fallback")
            return key
    
    def encrypt_data(self, data):
        """
        Encrypt data
        
        Args:
            data (str, dict, list): Data to encrypt
            
        Returns:
            str: Encrypted data as base64 string
        """
        try:
            # Convert data to JSON string if it's a dict or list
            if isinstance(data, (dict, list)):
                data = json.dumps(data)
            
            # Ensure data is a string
            if not isinstance(data, str):
                data = str(data)
            
            # Encrypt data
            f = Fernet(self.encryption_key)
            encrypted_data = f.encrypt(data.encode())
            
            # Return as base64 string
            return base64.urlsafe_b64encode(encrypted_data).decode()
            
        except Exception as e:
            self.logger.error(f"Encryption error: {e}")
            raise SecurityError(f"Failed to encrypt data: {str(e)}")
    
    def decrypt_data(self, encrypted_data):
        """
        Decrypt data
        
        Args:
            encrypted_data (str): Encrypted data as base64 string
            
        Returns:
            str/dict/list: Decrypted data
        """
        try:
            # Decode base64 string
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data)
            
            # Decrypt data
            f = Fernet(self.encryption_key)
            decrypted_data = f.decrypt(encrypted_bytes).decode()
            
            # Try to parse as JSON
            try:
                return json.loads(decrypted_data)
            except json.JSONDecodeError:
                # Return as string if not valid JSON
                return decrypted_data
                
        except Exception as e:
            self.logger.error(f"Decryption error: {e}")
            raise SecurityError(f"Failed to decrypt data: {str(e)}")
    
    def hash_password(self, password):
        """
        Hash password using PBKDF2 with SHA-256
        
        Args:
            password (str): Password to hash
            
        Returns:
            str: Password hash and salt as string
        """
        try:
            # Generate random salt
            salt = os.urandom(32)
            
            # Hash password
            hash_bytes = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode(),
                salt,
                100000  # 100,000 iterations
            )
            
            # Combine salt and hash
            storage = salt + hash_bytes
            
            # Return as base64 string
            return base64.b64encode(storage).decode()
            
        except Exception as e:
            self.logger.error(f"Password hashing error: {e}")
            raise SecurityError(f"Failed to hash password: {str(e)}")
    
    def verify_password(self, stored_password, provided_password):
        """
        Verify password against stored hash
        
        Args:
            stored_password (str): Stored password hash
            provided_password (str): Password to verify
            
        Returns:
            bool: True if password matches, False otherwise
        """
        try:
            # Decode stored password
            storage = base64.b64decode(stored_password)
            
            # Extract salt and hash
            salt = storage[:32]
            stored_hash = storage[32:]
            
            # Hash provided password with same salt
            hash_bytes = hashlib.pbkdf2_hmac(
                'sha256',
                provided_password.encode(),
                salt,
                100000  # 100,000 iterations
            )
            
            # Compare hashes using constant-time comparison
            return secrets.compare_digest(stored_hash, hash_bytes)
            
        except Exception as e:
            self.logger.error(f"Password verification error: {e}")
            raise SecurityError(f"Failed to verify password: {str(e)}")
    
    def generate_token(self, user_data):
        """
        Generate JWT token
        
        Args:
            user_data (dict): User data to encode in token
            
        Returns:
            str: JWT token
        """
        try:
            # Set expiration time
            expiration = datetime.utcnow() + timedelta(hours=self.jwt_expiration)
            
            # Create payload
            payload = {
                **user_data,
                'exp': expiration
            }
            
            # Generate token
            token = jwt.encode(
                payload,
                self.secret_key,
                algorithm=self.jwt_algorithm
            )
            
            return token
            
        except Exception as e:
            self.logger.error(f"Token generation error: {e}")
            raise SecurityError(f"Failed to generate token: {str(e)}")
    
    def verify_token(self, token):
        """
        Verify JWT token
        
        Args:
            token (str): JWT token to verify
            
        Returns:
            dict: Decoded token payload
        """
        try:
            # Decode and verify token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.jwt_algorithm]
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            self.logger.warning("Token expired")
            raise SecurityError("Token expired")
            
        except jwt.InvalidTokenError as e:
            self.logger.warning(f"Invalid token: {e}")
            raise SecurityError(f"Invalid token: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Token verification error: {e}")
            raise SecurityError(f"Failed to verify token: {str(e)}")
    
    def sanitize_input(self, input_data):
        """
        Sanitize input data to prevent injection attacks
        
        Args:
            input_data (str): Input data to sanitize
            
        Returns:
            str: Sanitized input data
        """
        if not isinstance(input_data, str):
            return input_data
        
        # Basic sanitization
        sanitized = input_data
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", ';', '(', ')', '&', '|', '`']
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized
    
    def mask_sensitive_data(self, data, sensitive_fields=None):
        """
        Mask sensitive data in logs and outputs
        
        Args:
            data (dict): Data containing sensitive information
            sensitive_fields (list, optional): List of sensitive field names
            
        Returns:
            dict: Data with sensitive fields masked
        """
        if not isinstance(data, dict):
            return data
        
        # Default sensitive fields
        default_sensitive = [
            'password', 'token', 'secret', 'key', 'auth', 'credential',
            'api_key', 'apikey', 'access_token', 'refresh_token',
            'credit_card', 'card_number', 'cvv', 'ssn', 'social_security'
        ]
        
        # Combine with custom sensitive fields
        sensitive_fields = sensitive_fields or []
        all_sensitive = default_sensitive + sensitive_fields
        
        # Create a copy to avoid modifying the original
        masked_data = data.copy()
        
        # Mask sensitive fields
        for key in masked_data:
            if any(sensitive in key.lower() for sensitive in all_sensitive):
                if isinstance(masked_data[key], str):
                    # Show first and last character, mask the rest
                    value = masked_data[key]
                    if len(value) > 4:
                        masked_data[key] = value[0] + '*' * (len(value) - 2) + value[-1]
                    else:
                        masked_data[key] = '****'
        
        return masked_data
    
    def secure_headers(self):
        """
        Generate secure HTTP headers
        
        Returns:
            dict: Secure HTTP headers
        """
        return {
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; object-src 'none';",
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        
    def generate_key(self, key_path):
        """
        Generate and save a new encryption key
        
        Args:
            key_path (str): Path to save the key
            
        Returns:
            bytes: Generated encryption key
        """
        try:
            # Generate new key
            key = Fernet.generate_key()
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(key_path), exist_ok=True)
            
            # Save key to file with restricted permissions
            with open(key_path, 'wb') as f:
                f.write(key)
            
            # Set file permissions to be restrictive (owner read-only)
            try:
                os.chmod(key_path, 0o400)
            except Exception as e:
                self.logger.warning(f"Could not set restrictive permissions on key file: {e}")
            
            self.logger.info(f"Generated and saved new encryption key to {key_path}")
            return key
            
        except Exception as e:
            self.logger.error(f"Error generating encryption key: {e}")
            raise SecurityError(f"Failed to generate encryption key: {str(e)}")