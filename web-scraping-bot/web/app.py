#!/usr/bin/env python3
"""
Web Dashboard for Scraping Bot
"""
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
import os
import json
import pandas as pd
from datetime import datetime, timedelta
import sys
import secrets

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import custom modules
from utils.auth import UserAuth
from utils.logger import get_default_logger
from utils.security import Security
from web.middleware import require_auth, require_role, setup_middleware, load_config

# Initialize logger
logger = get_default_logger('web_app')

# Load configuration
config = load_config()

# Initialize authentication module
auth_config = config.get('auth', {})
auth = UserAuth(auth_config) if auth_config.get('enabled', False) else None

# Initialize security module
security_config = config.get('security', {})
security = Security(security_config)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = security.generate_random_key()

# Set up middleware
setup_middleware(app)

@app.route('/')
@require_auth
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html', user=request.user)

@app.route('/api/stats')
@require_auth
def get_stats():
    """Get scraping statistics"""
    try:
        # Load config to get total products
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(project_root, 'config', 'config.json')
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        total_products = sum(len(target['products']) for target in config['targets'])
        active_stores = len(config['targets'])
        
        # Check recent reports
        reports_dir = os.path.join(project_root, 'reports', 'daily')
        reports = []
        if os.path.exists(reports_dir):
            reports = [f for f in os.listdir(reports_dir) if f.endswith('.xlsx')]
        
        last_run = "Never"
        if reports:
            latest_report = max(reports)
            # Extract timestamp from filename
            try:
                timestamp_str = latest_report.split('_')[2].replace('.xlsx', '')
                dt = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                last_run = dt.strftime('%Y-%m-%d %H:%M')
            except:
                last_run = "Unknown"
        
        # Log access
        logger.info(f"Stats accessed by {request.user['username']}")
        
        return jsonify({
            'total_products': total_products,
            'active_stores': active_stores,
            'success_rate': 95,  # Mock data
            'last_run': last_run,
            'total_reports': len(reports)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports')
@require_auth
def get_reports():
    """Get list of generated reports"""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        reports_dir = os.path.join(project_root, 'reports', 'daily')
        reports = []
        
        if os.path.exists(reports_dir):
            for filename in os.listdir(reports_dir):
                if filename.endswith('.xlsx'):
                    filepath = os.path.join(reports_dir, filename)
                    stat = os.stat(filepath)
                    reports.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M'),
                        'download_url': f'/download/{filename}'
                    })
        
        # Sort by creation time (newest first)
        reports.sort(key=lambda x: x['created'], reverse=True)
        
        # Log access
        logger.info(f"Reports list accessed by {request.user['username']}")
        
        return jsonify(reports)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
@require_auth
def download_report(filename):
    """Download report file"""
    try:
        from flask import send_file
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        reports_dir = os.path.join(project_root, 'reports', 'daily')
        filepath = os.path.join(reports_dir, filename)
        
        # Validate filename to prevent path traversal
        if '..' in filename or filename.startswith('/'):
            logger.warning(f"Attempted path traversal: {filename} by {request.user['username']}")
            return "Invalid filename", 400
        
        if os.path.exists(filepath):
            # Log download
            logger.info(f"Report {filename} downloaded by {request.user['username']}")
            return send_file(filepath, as_attachment=True)
        else:
            return "File not found", 404
    
    except Exception as e:
        return f"Error downloading file: {str(e)}", 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    # Check if authentication is enabled
    if not auth_config.get('enabled', False):
        return redirect(url_for('dashboard'))
    
    # Check if already logged in
    if session.get('session_id'):
        user_session = auth.validate_session(session['session_id'])
        if user_session:
            return redirect(url_for('dashboard'))
    
    # Handle login form
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Sanitize input
        username = security.sanitize_input(username) if username else ''
        
        # Authenticate user
        session_id = auth.authenticate(username, password)
        
        if session_id:
            # Set session
            session['session_id'] = session_id
            
            # Get next URL
            next_url = request.args.get('next') or url_for('dashboard')
            
            # Log login
            logger.info(f"User {username} logged in successfully")
            
            return redirect(next_url)
        else:
            # Log failed login
            logger.warning(f"Failed login attempt for user {username}")
            
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    # Check if authentication is enabled
    if not auth_config.get('enabled', False):
        return redirect(url_for('dashboard'))
    
    # Get session ID
    session_id = session.get('session_id')
    
    if session_id:
        # Log logout
        user_session = auth.validate_session(session_id)
        if user_session:
            logger.info(f"User {user_session['username']} logged out")
        
        # Logout user
        auth.logout(session_id)
    
    # Clear session
    session.clear()
    
    return redirect(url_for('login'))

@app.route('/admin')
@require_auth
@require_role('admin')
def admin_panel():
    """Admin panel"""
    return render_template('admin.html', user=request.user)

@app.route('/api/users', methods=['GET'])
@require_auth
@require_role('admin')
def get_users():
    """Get list of users (admin only)"""
    try:
        # Get session ID
        session_id = session.get('session_id')
        
        # Get users
        users = auth.list_users(session_id)
        
        if users is None:
            return jsonify({'error': 'Failed to get users'}), 500
        
        return jsonify(users)
    
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['POST'])
@require_auth
@require_role('admin')
def create_user():
    """Create new user (admin only)"""
    try:
        # Get request data
        data = request.get_json()
        
        # Validate data
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Create user
        result = auth.create_user(
            data['username'],
            data['password'],
            role=data.get('role', 'user'),
            metadata=data.get('metadata', {})
        )
        
        if result:
            logger.info(f"User {data['username']} created by {request.user['username']}")
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to create user'}), 500
    
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create login template directory if it doesn't exist
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    templates_dir = os.path.join(project_root, 'web', 'templates')
    os.makedirs(templates_dir, exist_ok=True)
    
    # Run app
    app.run(debug=False, host='0.0.0.0', port=5000)
