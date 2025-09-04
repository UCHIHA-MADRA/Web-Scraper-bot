#!/usr/bin/env python3
"""
Authentication module for web scraping bot
"""

import os
import json
import uuid
from datetime import datetime, timedelta

# Import custom modules
from utils.logger import get_default_logger
from utils.exceptions import SecurityError
from utils.security import Security

class UserAuth:
    """
    User authentication and management class
    """
    def __init__(self, config=None):
        """
        Initialize authentication module
        
        Args:
            config (dict, optional): Authentication configuration
        """
        self.config = config or {}
        self.logger = get_default_logger('auth')
        
        # Initialize security module
        self.security = Security(self.config.get('security', {}))
        
        # Set up configuration
        self.users_file = self.config.get('users_file', 'users.json')
        self.users_dir = self.config.get('users_dir', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config'))
        self.users_path = os.path.join(self.users_dir, self.users_file)
        
        # Session settings
        self.session_timeout = self.config.get('session_timeout', 30)  # minutes
        self.max_failed_attempts = self.config.get('max_failed_attempts', 5)
        self.lockout_duration = self.config.get('lockout_duration', 15)  # minutes
        
        # Load users
        self.users = self._load_users()
        self.sessions = {}
        
        self.logger.info("Authentication module initialized")
    
    def _load_users(self):
        """
        Load users from file
        
        Returns:
            dict: User data
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(self.users_dir, exist_ok=True)
            
            # Check if users file exists
            if os.path.exists(self.users_path):
                with open(self.users_path, 'r') as f:
                    encrypted_data = f.read().strip()
                    
                    # Check if data is encrypted
                    if encrypted_data.startswith('{'):
                        # Legacy unencrypted data
                        users = json.loads(encrypted_data)
                        self.logger.warning("Loaded unencrypted user data, will encrypt on next save")
                    else:
                        # Decrypt data
                        users = self.security.decrypt_data(encrypted_data)
                    
                    self.logger.info(f"Loaded {len(users)} users from {self.users_path}")
                    return users
            
            # Create empty users file
            users = {}
            self._save_users(users)
            return users
            
        except Exception as e:
            self.logger.error(f"Failed to load users: {e}")
            return {}
    
    def _save_users(self, users=None):
        """
        Save users to file
        
        Args:
            users (dict, optional): User data to save
        """
        try:
            # Use provided users or current users
            users_to_save = users if users is not None else self.users
            
            # Create directory if it doesn't exist
            os.makedirs(self.users_dir, exist_ok=True)
            
            # Encrypt user data
            encrypted_data = self.security.encrypt_data(users_to_save)
            
            # Save to file
            with open(self.users_path, 'w') as f:
                f.write(encrypted_data)
            
            self.logger.info(f"Saved {len(users_to_save)} users to {self.users_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save users: {e}")
            raise SecurityError(f"Failed to save users: {str(e)}")
    
    def create_user(self, username, password, role='user', metadata=None):
        """
        Create a new user
        
        Args:
            username (str): Username
            password (str): Password
            role (str, optional): User role
            metadata (dict, optional): Additional user metadata
            
        Returns:
            bool: True if user created, False otherwise
        """
        try:
            # Check if username already exists
            if username in self.users:
                self.logger.warning(f"User {username} already exists")
                return False
            
            # Hash password
            password_hash = self.security.hash_password(password)
            
            # Create user
            self.users[username] = {
                'password': password_hash,
                'role': role,
                'created_at': datetime.now().isoformat(),
                'last_login': None,
                'failed_attempts': 0,
                'locked_until': None,
                'metadata': metadata or {}
            }
            
            # Save users
            self._save_users()
            
            self.logger.info(f"Created user {username} with role {role}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create user {username}: {e}")
            return False
    
    def authenticate(self, username, password):
        """
        Authenticate user
        
        Args:
            username (str): Username
            password (str): Password
            
        Returns:
            str: Session token if authenticated, None otherwise
        """
        try:
            # Check if user exists
            if username not in self.users:
                self.logger.warning(f"Authentication failed: User {username} not found")
                return None
            
            user = self.users[username]
            
            # Check if account is locked
            if user.get('locked_until'):
                locked_until = datetime.fromisoformat(user['locked_until'])
                if datetime.now() < locked_until:
                    self.logger.warning(f"Authentication failed: User {username} is locked until {locked_until}")
                    return None
                else:
                    # Reset failed attempts if lock has expired
                    user['failed_attempts'] = 0
                    user['locked_until'] = None
            
            # Verify password
            if not self.security.verify_password(user['password'], password):
                # Increment failed attempts
                user['failed_attempts'] = user.get('failed_attempts', 0) + 1
                
                # Check if account should be locked
                if user['failed_attempts'] >= self.max_failed_attempts:
                    locked_until = datetime.now() + timedelta(minutes=self.lockout_duration)
                    user['locked_until'] = locked_until.isoformat()
                    self.logger.warning(f"User {username} locked until {locked_until} due to too many failed attempts")
                
                # Save users
                self._save_users()
                
                self.logger.warning(f"Authentication failed: Invalid password for user {username}")
                return None
            
            # Reset failed attempts
            user['failed_attempts'] = 0
            user['locked_until'] = None
            
            # Update last login
            user['last_login'] = datetime.now().isoformat()
            
            # Save users
            self._save_users()
            
            # Generate session token
            session_id = str(uuid.uuid4())
            session_expiry = datetime.now() + timedelta(minutes=self.session_timeout)
            
            # Store session
            self.sessions[session_id] = {
                'username': username,
                'role': user['role'],
                'expires': session_expiry
            }
            
            self.logger.info(f"User {username} authenticated successfully")
            return session_id
            
        except Exception as e:
            self.logger.error(f"Authentication error for user {username}: {e}")
            return None
    
    def validate_session(self, session_id):
        """
        Validate session
        
        Args:
            session_id (str): Session ID
            
        Returns:
            dict: Session data if valid, None otherwise
        """
        try:
            # Check if session exists
            if session_id not in self.sessions:
                return None
            
            session = self.sessions[session_id]
            
            # Check if session has expired
            if datetime.now() > session['expires']:
                # Remove expired session
                del self.sessions[session_id]
                return None
            
            # Extend session expiry
            session['expires'] = datetime.now() + timedelta(minutes=self.session_timeout)
            
            return session
            
        except Exception as e:
            self.logger.error(f"Session validation error: {e}")
            return None
    
    def logout(self, session_id):
        """
        Logout user
        
        Args:
            session_id (str): Session ID
            
        Returns:
            bool: True if logged out, False otherwise
        """
        try:
            # Check if session exists
            if session_id in self.sessions:
                # Remove session
                del self.sessions[session_id]
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Logout error: {e}")
            return False
    
    def change_password(self, username, current_password, new_password):
        """
        Change user password
        
        Args:
            username (str): Username
            current_password (str): Current password
            new_password (str): New password
            
        Returns:
            bool: True if password changed, False otherwise
        """
        try:
            # Check if user exists
            if username not in self.users:
                self.logger.warning(f"Password change failed: User {username} not found")
                return False
            
            user = self.users[username]
            
            # Verify current password
            if not self.security.verify_password(user['password'], current_password):
                self.logger.warning(f"Password change failed: Invalid current password for user {username}")
                return False
            
            # Hash new password
            password_hash = self.security.hash_password(new_password)
            
            # Update password
            user['password'] = password_hash
            
            # Save users
            self._save_users()
            
            self.logger.info(f"Password changed for user {username}")
            return True
            
        except Exception as e:
            self.logger.error(f"Password change error for user {username}: {e}")
            return False
    
    def reset_password(self, username, new_password, admin_session_id=None):
        """
        Reset user password (admin only)
        
        Args:
            username (str): Username
            new_password (str): New password
            admin_session_id (str, optional): Admin session ID
            
        Returns:
            bool: True if password reset, False otherwise
        """
        try:
            # Check admin privileges if session ID provided
            if admin_session_id:
                admin_session = self.validate_session(admin_session_id)
                if not admin_session or admin_session['role'] != 'admin':
                    self.logger.warning(f"Password reset failed: Insufficient privileges")
                    return False
            
            # Check if user exists
            if username not in self.users:
                self.logger.warning(f"Password reset failed: User {username} not found")
                return False
            
            # Hash new password
            password_hash = self.security.hash_password(new_password)
            
            # Update password
            self.users[username]['password'] = password_hash
            
            # Reset failed attempts and lock
            self.users[username]['failed_attempts'] = 0
            self.users[username]['locked_until'] = None
            
            # Save users
            self._save_users()
            
            self.logger.info(f"Password reset for user {username}")
            return True
            
        except Exception as e:
            self.logger.error(f"Password reset error for user {username}: {e}")
            return False
    
    def delete_user(self, username, admin_session_id):
        """
        Delete user (admin only)
        
        Args:
            username (str): Username
            admin_session_id (str): Admin session ID
            
        Returns:
            bool: True if user deleted, False otherwise
        """
        try:
            # Check admin privileges
            admin_session = self.validate_session(admin_session_id)
            if not admin_session or admin_session['role'] != 'admin':
                self.logger.warning(f"User deletion failed: Insufficient privileges")
                return False
            
            # Check if user exists
            if username not in self.users:
                self.logger.warning(f"User deletion failed: User {username} not found")
                return False
            
            # Delete user
            del self.users[username]
            
            # Remove any active sessions for this user
            for session_id, session in list(self.sessions.items()):
                if session['username'] == username:
                    del self.sessions[session_id]
            
            # Save users
            self._save_users()
            
            self.logger.info(f"User {username} deleted")
            return True
            
        except Exception as e:
            self.logger.error(f"User deletion error for user {username}: {e}")
            return False
    
    def get_user_info(self, username, include_sensitive=False):
        """
        Get user information
        
        Args:
            username (str): Username
            include_sensitive (bool, optional): Include sensitive information
            
        Returns:
            dict: User information
        """
        try:
            # Check if user exists
            if username not in self.users:
                return None
            
            user = self.users[username]
            
            # Create a copy of user data
            user_info = user.copy()
            
            # Remove sensitive information if not requested
            if not include_sensitive:
                user_info.pop('password', None)
            
            return user_info
            
        except Exception as e:
            self.logger.error(f"Error getting user info for {username}: {e}")
            return None
    
    def list_users(self, admin_session_id):
        """
        List all users (admin only)
        
        Args:
            admin_session_id (str): Admin session ID
            
        Returns:
            list: List of users
        """
        try:
            # Check admin privileges
            admin_session = self.validate_session(admin_session_id)
            if not admin_session or admin_session['role'] != 'admin':
                self.logger.warning(f"User listing failed: Insufficient privileges")
                return None
            
            # Create list of users with non-sensitive information
            user_list = []
            for username, user in self.users.items():
                user_info = {
                    'username': username,
                    'role': user['role'],
                    'created_at': user['created_at'],
                    'last_login': user['last_login'],
                    'metadata': user.get('metadata', {})
                }
                user_list.append(user_info)
            
            return user_list
            
        except Exception as e:
            self.logger.error(f"User listing error: {e}")
            return None
    
    def update_user_role(self, username, new_role, admin_session_id):
        """
        Update user role (admin only)
        
        Args:
            username (str): Username
            new_role (str): New role
            admin_session_id (str): Admin session ID
            
        Returns:
            bool: True if role updated, False otherwise
        """
        try:
            # Check admin privileges
            admin_session = self.validate_session(admin_session_id)
            if not admin_session or admin_session['role'] != 'admin':
                self.logger.warning(f"Role update failed: Insufficient privileges")
                return False
            
            # Check if user exists
            if username not in self.users:
                self.logger.warning(f"Role update failed: User {username} not found")
                return False
            
            # Update role
            self.users[username]['role'] = new_role
            
            # Update any active sessions for this user
            for session in self.sessions.values():
                if session['username'] == username:
                    session['role'] = new_role
            
            # Save users
            self._save_users()
            
            self.logger.info(f"Role updated for user {username} to {new_role}")
            return True
            
        except Exception as e:
            self.logger.error(f"Role update error for user {username}: {e}")
            return False
    
    def update_user_metadata(self, username, metadata, session_id):
        """
        Update user metadata
        
        Args:
            username (str): Username
            metadata (dict): Metadata to update
            session_id (str): Session ID
            
        Returns:
            bool: True if metadata updated, False otherwise
        """
        try:
            # Validate session
            session = self.validate_session(session_id)
            if not session:
                self.logger.warning(f"Metadata update failed: Invalid session")
                return False
            
            # Check if user is updating their own metadata or is an admin
            if session['username'] != username and session['role'] != 'admin':
                self.logger.warning(f"Metadata update failed: Insufficient privileges")
                return False
            
            # Check if user exists
            if username not in self.users:
                self.logger.warning(f"Metadata update failed: User {username} not found")
                return False
            
            # Update metadata
            current_metadata = self.users[username].get('metadata', {})
            current_metadata.update(metadata)
            self.users[username]['metadata'] = current_metadata
            
            # Save users
            self._save_users()
            
            self.logger.info(f"Metadata updated for user {username}")
            return True
            
        except Exception as e:
            self.logger.error(f"Metadata update error for user {username}: {e}")
            return False