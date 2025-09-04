#!/usr/bin/env python3
"""
Quick start script for Web Scraping Bot
"""
import subprocess
import sys
import os

def run_command(command, description):
    """Run command and print status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        return False

def main():
    print("🚀 Web Scraping Bot - Quick Start Setup")
    print("=" * 50)
    
    # Install requirements
    if run_command("pip install -r requirements.txt", "Installing Python requirements"):
        print("📦 Dependencies installed successfully")
    
    # Run setup script
    if run_command("python scripts/setup.py", "Running setup script"):
        print("🛠️ Project setup completed")
    
    # Test the bot
    print("\n🧪 Testing the bot with demo configuration...")
    if run_command("python Web_Scraper.py", "Testing scraper functionality"):
        print("✅ Bot is working correctly!")
        
        # Show generated files
        print("\n📁 Generated files:")
        if os.path.exists("reports/daily"):
            reports = [f for f in os.listdir("reports/daily") if f.endswith('.xlsx')]
            for report in reports:
                print(f"  📊 {report}")
        
        if os.path.exists("logs"):
            logs = [f for f in os.listdir("logs") if f.endswith('.log')]
            for log in logs:
                print(f"  📋 logs/{log}")
    
    print("\n🎉 Setup completed! Your web scraping bot is ready to use.")
    print("\nNext steps:")
    print("1. Edit config/config.json with your target websites")
    print("2. Run: python Web_Scraper.py")
    print("3. Check reports in the reports/daily folder")
    print("4. View dashboard at: python web/app.py")

if __name__ == "__main__":
    main()
