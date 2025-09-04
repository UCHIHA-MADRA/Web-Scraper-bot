#!/usr/bin/env python3
"""
Data backup and archival system
"""
import os
import shutil
import zipfile
from datetime import datetime, timedelta
import argparse

class BackupManager:
    def __init__(self, source_dirs=None, backup_dir='backups'):
        self.source_dirs = source_dirs or ['data', 'reports', 'logs', 'config']
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
    
    def create_backup(self, backup_name=None):
        """Create a backup of all important data"""
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = os.path.join(self.backup_dir, f"{backup_name}.zip")
        
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for source_dir in self.source_dirs:
                if os.path.exists(source_dir):
                    for root, dirs, files in os.walk(source_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, '.')
                            zipf.write(file_path, arcname)
                            print(f"Added {arcname}")
        
        print(f"✅ Backup created: {backup_path}")
        return backup_path
    
    def cleanup_old_backups(self, keep_days=30):
        """Remove backups older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        for filename in os.listdir(self.backup_dir):
            if filename.startswith('backup_') and filename.endswith('.zip'):
                filepath = os.path.join(self.backup_dir, filename)
                file_date = datetime.fromtimestamp(os.path.getctime(filepath))
                
                if file_date < cutoff_date:
                    os.remove(filepath)
                    print(f"🗑️ Removed old backup: {filename}")
    
    def restore_backup(self, backup_filename, restore_dir='restored'):
        """Restore from a backup file"""
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        if not os.path.exists(backup_path):
            print(f"❌ Backup file not found: {backup_path}")
            return False
        
        os.makedirs(restore_dir, exist_ok=True)
        
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            zipf.extractall(restore_dir)
            print(f"✅ Backup restored to: {restore_dir}")
        
        return True
    
    def list_backups(self):
        """List all available backups"""
        backups = []
        for filename in os.listdir(self.backup_dir):
            if filename.startswith('backup_') and filename.endswith('.zip'):
                filepath = os.path.join(self.backup_dir, filename)
                size = os.path.getsize(filepath)
                created = datetime.fromtimestamp(os.path.getctime(filepath))
                backups.append({
                    'filename': filename,
                    'size': size,
                    'created': created
                })
        
        backups.sort(key=lambda x: x['created'], reverse=True)
        return backups

def main():
    parser = argparse.ArgumentParser(description='Backup Manager for Web Scraping Bot')
    parser.add_argument('action', choices=['create', 'list', 'cleanup', 'restore'], 
                       help='Action to perform')
    parser.add_argument('--name', help='Backup name for create action')
    parser.add_argument('--days', type=int, default=30, help='Days to keep for cleanup')
    parser.add_argument('--file', help='Backup file to restore')
    
    args = parser.parse_args()
    
    manager = BackupManager()
    
    if args.action == 'create':
        manager.create_backup(args.name)
    elif args.action == 'list':
        backups = manager.list_backups()
        print(f"\n📦 Available Backups ({len(backups)}):")
        for backup in backups:
            size_mb = backup['size'] / (1024 * 1024)
            print(f"  {backup['filename']} - {size_mb:.1f}MB - {backup['created']}")
    elif args.action == 'cleanup':
        manager.cleanup_old_backups(args.days)
    elif args.action == 'restore':
        if args.file:
            manager.restore_backup(args.file)
        else:
            print("❌ Please specify --file for restore action")

if __name__ == "__main__":
    main()
