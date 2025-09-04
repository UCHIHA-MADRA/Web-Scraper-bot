#!/usr/bin/env python3
"""
Project setup and installation script
"""
import os
import subprocess
import sys

def install_requirements():
    """Install Python requirements"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install requirements")

def create_directories():
    """Create necessary directories"""
    directories = [
        "data/raw", "data/processed", "data/historical",
        "reports/daily", "reports/weekly", 
        "logs", "database"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def main():
    print("🚀 Setting up Web Scraping Bot...")
    create_directories()
    install_requirements()
    print("✅ Setup complete!")

if __name__ == "__main__":
    main()
