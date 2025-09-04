#!/usr/bin/env python3
"""
Unit tests for authentication functionality

This module contains tests for the UserAuth class, including user creation,
validation, authentication, and session management.
"""
import pytest
import os
import json
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime, timedelta

from utils.auth import UserAuth
from utils.exceptions import AuthError

class TestUserAuth:
    @pytest.fixture
    def mock_security(self):
        """Mock security module for testing"""
        security = MagicMock()
        security.encrypt_data.return_value = 'encrypted_data'
        security.decrypt_data.return_value = {'test_user': {'password': 'hashed_password', 'role': 'user'}}
        security.hash_password.return_value = 'hashed_password'
        security.verify_password.return_value = True
        security.generate_token.return_value = 'test_token'
        return security
    
    @pytest.fixture
    def user_auth(self, test_config, mock_security, mock_logger):
        """UserAuth instance for testing"""
        with patch('utils.auth.Security', return_value=mock_security):
            auth = UserAuth(test_config['auth'], mock_logger)
            return auth
    
    def test_init(self, user_auth, test_config):
        """Test UserAuth initialization"""
        assert user_auth.config is not None
        assert user_auth.users_file == test_config['auth']['users_file']
        assert user_auth.session_timeout == test_config['auth']['session_timeout']
    
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open, read_data='{"test_user": {"password": "hashed_password", "role": "user"}}')
    def test_load_users_existing(self, mock_file, mock_makedirs, mock_exists, user_auth):
        """Test loading existing users"""
        mock_exists.return_value = True
        
        user_auth._load_users()
        
        mock_exists.assert_called_once()
        mock_file.assert_called_once()
        assert 'test_user' in user_auth.users
    
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_users_new(self, mock_file, mock_makedirs, mock_exists, user_auth):
        """Test creating new users file"""
        mock_exists.return_value = False
        
        user_auth._load_users()
        
        mock_exists.assert_called_once()
        mock_makedirs.assert_called_once()
        mock_file.assert_called_once()
        mock_file().write.assert_called_once_with('{}')
        assert user_auth.users == {}
    
    def test_create_user(self, user_auth, mock_security):
        """Test user creation"""
        with patch.object(UserAuth, '_save_users') as mock_save:
            result = user_auth.create_user('new_user', 'password123')
            
            mock_security.hash_password.assert_called_once_with('password123')
            mock_save.assert_called_once()
            assert result is True
            assert 'new_user' in user_auth.users
            assert user_auth.users['new_user']['password'] == 'hashed_password'
            assert user_auth.users['new_user']['role'] == 'user'
    
    def test_create_user_exists(self, user_auth):
        """Test creating user that already exists"""
        user_auth.users = {'existing_user': {'password': 'hashed_password', 'role': 'user'}}
        
        with pytest.raises(AuthError):
            user_auth.create_user('existing_user', 'password123')
    
    def test_authenticate_user_success(self, user_auth, mock_security):
        """Test successful user authentication"""
        user_auth.users = {'test_user': {'password': 'hashed_password', 'role': 'user', 'failed_attempts': 0}}
        
        result = user_auth.authenticate_user('test_user', 'password123')
        
        mock_security.verify_password.assert_called_once()
        mock_security.generate_token.assert_called_once()
        assert result == 'test_token'
        assert user_auth.users['test_user']['failed_attempts'] == 0
        assert 'last_login' in user_auth.users['test_user']
    
    def test_authenticate_user_not_found(self, user_auth):
        """Test authentication with non-existent user"""
        user_auth.users = {}
        
        with pytest.raises(AuthError):
            user_auth.authenticate_user('nonexistent', 'password123')
    
    def test_authenticate_user_wrong_password(self, user_auth, mock_security):
        """Test authentication with wrong password"""
        user_auth.users = {'test_user': {'password': 'hashed_password', 'role': 'user', 'failed_attempts': 0}}
        mock_security.verify_password.return_value = False
        
        with pytest.raises(AuthError):
            user_auth.authenticate_user('test_user', 'wrong_password')
        
        assert user_auth.users['test_user']['failed_attempts'] == 1
    
    def test_authenticate_user_locked(self, user_auth):
        """Test authentication with locked account"""
        user_auth.users = {
            'locked_user': {
                'password': 'hashed_password', 
                'role': 'user', 
                'failed_attempts': 3,
                'lockout_time': (datetime.now() + timedelta(minutes=5)).isoformat()
            }
        }
        
        with pytest.raises(AuthError):
            user_auth.authenticate_user('locked_user', 'password123')
    
    def test_validate_token_valid(self, user_auth, mock_security):
        """Test validating a valid token"""
        mock_security.verify_token.return_value = {'username': 'test_user', 'role': 'user'}
        
        result = user_auth.validate_token('valid_token')
        
        mock_security.verify_token.assert_called_once_with('valid_token')
        assert result == {'username': 'test_user', 'role': 'user'}
    
    def test_validate_token_invalid(self, user_auth, mock_security):
        """Test validating an invalid token"""
        mock_security.verify_token.side_effect = Exception('Invalid token')
        
        with pytest.raises(AuthError):
            user_auth.validate_token('invalid_token')
    
    def test_change_password(self, user_auth, mock_security):
        """Test changing user password"""
        user_auth.users = {'test_user': {'password': 'old_hash', 'role': 'user'}}
        
        with patch.object(UserAuth, '_save_users') as mock_save:
            result = user_auth.change_password('test_user', 'new_password')
            
            mock_security.hash_password.assert_called_once_with('new_password')
            mock_save.assert_called_once()
            assert result is True
            assert user_auth.users['test_user']['password'] == 'hashed_password'
    
    def test_change_password_user_not_found(self, user_auth):
        """Test changing password for non-existent user"""
        user_auth.users = {}
        
        with pytest.raises(AuthError):
            user_auth.change_password('nonexistent', 'new_password')