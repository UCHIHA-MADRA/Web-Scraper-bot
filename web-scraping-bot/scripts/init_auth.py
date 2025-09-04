#!/usr/bin/env python3
"""
Initialize authentication system with admin user
"""

import os
import sys
import json
import getpass
import argparse
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import custom modules
from utils.auth import UserAuth
from utils.logger import get_default_logger
from utils.security import Security

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
            print(f"Error: Configuration file not found at {config_path}")
            sys.exit(1)
        
        # Load config
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        return config
    
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

def initialize_auth(config, username=None, password=None, force=False):
    """
    Initialize authentication system with admin user
    
    Args:
        config (dict): Configuration
        username (str, optional): Admin username
        password (str, optional): Admin password
        force (bool, optional): Force initialization even if users exist
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Initialize logger
        logger = get_default_logger('init_auth')
        logger.info("Initializing authentication system")
        
        # Initialize security module
        security_config = config.get('security', {})
        security = Security(security_config)
        
        # Ensure encryption key exists
        key_file = security_config.get('encryption_key_file', 'config/encryption.key')
        key_path = Path(project_root) / key_file
        
        if not key_path.parent.exists():
            key_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not key_path.exists() or force:
            logger.info(f"Generating new encryption key at {key_path}")
            security.generate_key(str(key_path))
        
        # Initialize authentication module
        auth_config = config.get('auth', {})
        auth = UserAuth(auth_config)
        
        # Check if users exist
        if auth.users and not force:
            logger.info("Users already exist, use --force to reinitialize")
            return True
        
        # Get admin username
        if not username:
            username = input("Enter admin username [admin]: ").strip() or "admin"
        
        # Get admin password
        if not password:
            while True:
                password = getpass.getpass("Enter admin password: ")
                if not password:
                    print("Password cannot be empty")
                    continue
                    
                confirm = getpass.getpass("Confirm admin password: ")
                if password != confirm:
                    print("Passwords do not match")
                    continue
                    
                break
        
        # Create admin user
        result = auth.create_user(username, password, role='admin', metadata={'created_by': 'init_auth'})
        
        if result:
            logger.info(f"Admin user '{username}' created successfully")
            print(f"Admin user '{username}' created successfully")
            return True
        else:
            logger.error(f"Failed to create admin user '{username}'")
            print(f"Failed to create admin user '{username}'")
            return False
    
    except Exception as e:
        print(f"Error initializing authentication: {e}")
        return False

def main():
    """
    Main function
    """
    # Parse arguments
    parser = argparse.ArgumentParser(description='Initialize authentication system with admin user')
    parser.add_argument('--username', '-u', help='Admin username')
    parser.add_argument('--password', '-p', help='Admin password (not recommended, use interactive prompt)')
    parser.add_argument('--force', '-f', action='store_true', help='Force initialization even if users exist')
    args = parser.parse_args()
    
    # Get project root directory
    global project_root
    project_root = Path(__file__).parent.parent
    
    # Load configuration
    config = load_config()
    
    # Initialize authentication
    initialize_auth(config, args.username, args.password, args.force)

if __name__ == '__main__':
    main()