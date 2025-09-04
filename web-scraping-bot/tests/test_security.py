#!/usr/bin/env python3
"""
Unit tests for security functionality

This module contains tests for the Security class, including encryption,
decryption, password hashing, token generation, and validation.
"""
import pytest
import os
import json
from unittest.mock import patch, mock_open, MagicMock

from utils.security import Security
from utils.exceptions import SecurityError

class TestSecurity:
    def test_init(self, test_config):
        """Test security initialization"""
        security = Security(test_config['security'])
        assert security.config is not None
        assert security.config['secret_key'] == test_config['security']['secret_key']
    
    @patch('utils.security.Fernet')
    @patch('utils.security.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data=b'test_key')
    def test_get_or_create_encryption_key_existing(self, mock_file, mock_exists, mock_fernet, test_config):
        """Test getting existing encryption key"""
        mock_exists.return_value = True
        
        security = Security(test_config['security'])
        key = security._get_or_create_encryption_key()
        
        mock_exists.assert_called_once()
        mock_file.assert_called_once()
        assert key == b'test_key'
    
    @patch('utils.security.Fernet.generate_key')
    @patch('utils.security.os.path.exists')
    @patch('utils.security.os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_or_create_encryption_key_new(self, mock_file, mock_makedirs, mock_exists, mock_generate_key, test_config):
        """Test creating new encryption key"""
        mock_exists.return_value = False
        mock_generate_key.return_value = b'new_test_key'
        
        security = Security(test_config['security'])
        key = security._get_or_create_encryption_key()
        
        mock_exists.assert_called_once()
        mock_makedirs.assert_called_once()
        mock_file.assert_called_once()
        mock_file().write.assert_called_once_with(b'new_test_key')
        assert key == b'new_test_key'
    
    def test_encrypt_data_string(self, test_config):
        """Test encrypting string data"""
        with patch.object(Security, '_get_or_create_encryption_key', return_value=b'test_key'):
            with patch('utils.security.Fernet') as mock_fernet:
                mock_fernet_instance = MagicMock()
                mock_fernet.return_value = mock_fernet_instance
                mock_fernet_instance.encrypt.return_value = b'encrypted_data'
                
                security = Security(test_config['security'])
                result = security.encrypt_data('test_data')
                
                mock_fernet_instance.encrypt.assert_called_once()
                assert result == 'ZW5jcnlwdGVkX2RhdGE='
    
    def test_encrypt_data_dict(self, test_config):
        """Test encrypting dictionary data"""
        with patch.object(Security, '_get_or_create_encryption_key', return_value=b'test_key'):
            with patch('utils.security.Fernet') as mock_fernet:
                mock_fernet_instance = MagicMock()
                mock_fernet.return_value = mock_fernet_instance
                mock_fernet_instance.encrypt.return_value = b'encrypted_data'
                
                security = Security(test_config['security'])
                result = security.encrypt_data({'key': 'value'})
                
                mock_fernet_instance.encrypt.assert_called_once()
                assert result == 'ZW5jcnlwdGVkX2RhdGE='
    
    def test_decrypt_data(self, test_config):
        """Test decrypting data"""
        with patch.object(Security, '_get_or_create_encryption_key', return_value=b'test_key'):
            with patch('utils.security.Fernet') as mock_fernet:
                mock_fernet_instance = MagicMock()
                mock_fernet.return_value = mock_fernet_instance
                mock_fernet_instance.decrypt.return_value = b'{"key": "value"}'
                
                security = Security(test_config['security'])
                result = security.decrypt_data('ZW5jcnlwdGVkX2RhdGE=')
                
                mock_fernet_instance.decrypt.assert_called_once()
                assert result == {"key": "value"}
    
    def test_decrypt_data_error(self, test_config):
        """Test decryption error handling"""
        with patch.object(Security, '_get_or_create_encryption_key', return_value=b'test_key'):
            with patch('utils.security.Fernet') as mock_fernet:
                mock_fernet_instance = MagicMock()
                mock_fernet.return_value = mock_fernet_instance
                mock_fernet_instance.decrypt.side_effect = Exception('Decryption error')
                
                security = Security(test_config['security'])
                
                with pytest.raises(SecurityError):
                    security.decrypt_data('invalid_data')
    
    def test_hash_password(self, test_config):
        """Test password hashing"""
        with patch('utils.security.bcrypt.hashpw') as mock_hashpw:
            mock_hashpw.return_value = b'hashed_password'
            
            security = Security(test_config['security'])
            result = security.hash_password('password123')
            
            mock_hashpw.assert_called_once()
            assert result == 'hashed_password'
    
    def test_verify_password(self, test_config):
        """Test password verification"""
        with patch('utils.security.bcrypt.checkpw') as mock_checkpw:
            mock_checkpw.return_value = True
            
            security = Security(test_config['security'])
            result = security.verify_password('password123', 'hashed_password')
            
            mock_checkpw.assert_called_once()
            assert result is True
    
    def test_generate_token(self, test_config):
        """Test token generation"""
        with patch('utils.security.jwt.encode') as mock_encode:
            mock_encode.return_value = 'test_token'
            
            security = Security(test_config['security'])
            result = security.generate_token({'username': 'test_user'})
            
            mock_encode.assert_called_once()
            assert result == 'test_token'
    
    def test_verify_token_valid(self, test_config):
        """Test valid token verification"""
        with patch('utils.security.jwt.decode') as mock_decode:
            mock_decode.return_value = {'username': 'test_user', 'exp': 1000000000}
            
            security = Security(test_config['security'])
            result = security.verify_token('valid_token')
            
            mock_decode.assert_called_once()
            assert result == {'username': 'test_user', 'exp': 1000000000}
    
    def test_verify_token_invalid(self, test_config):
        """Test invalid token verification"""
        with patch('utils.security.jwt.decode') as mock_decode:
            mock_decode.side_effect = Exception('Invalid token')
            
            security = Security(test_config['security'])
            
            with pytest.raises(SecurityError):
                security.verify_token('invalid_token')
    
    def test_secure_headers(self, test_config):
        """Test secure headers generation"""
        security = Security(test_config['security'])
        headers = security.secure_headers()
        
        assert headers is not None
        assert 'X-Content-Type-Options' in headers
        assert 'X-Frame-Options' in headers
        assert 'X-XSS-Protection' in headers
        assert 'Content-Security-Policy' in headers