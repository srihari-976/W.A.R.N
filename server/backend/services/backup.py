import os
import shutil
import json
from datetime import datetime, timedelta
import logging
from backend.db import db
from backend.models.event import SecurityEvent
from backend.models.alert import Alert
from backend.models.asset import Asset

logger = logging.getLogger(__name__)

class BackupService:
    def __init__(self, backup_dir='backups'):
        self.backup_dir = backup_dir
        self._ensure_backup_dir()
    
    def _ensure_backup_dir(self):
        """Ensure backup directory exists"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def backup_database(self):
        """Create a backup of the database"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(self.backup_dir, f'backup_{timestamp}.db')
            
            # Copy database file
            shutil.copy2('instance/cybersecurity.db', backup_path)
            
            # Create metadata file
            metadata = {
                'timestamp': timestamp,
                'type': 'database',
                'size': os.path.getsize(backup_path)
            }
            
            with open(f'{backup_path}.meta', 'w') as f:
                json.dump(metadata, f)
            
            logger.info(f"Database backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Error backing up database: {str(e)}")
            raise
    
    def archive_old_data(self, days=30):
        """Archive data older than specified days"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_path = os.path.join(self.backup_dir, f'archive_{timestamp}.json')
            
            # Get old data
            cutoff_date = datetime.now() - timedelta(days=days)
            
            old_events = SecurityEvent.query.filter(
                SecurityEvent.created_at < cutoff_date
            ).all()
            
            old_alerts = Alert.query.filter(
                Alert.created_at < cutoff_date
            ).all()
            
            # Create archive
            archive_data = {
                'events': [event.to_dict() for event in old_events],
                'alerts': [alert.to_dict() for alert in old_alerts],
                'timestamp': timestamp
            }
            
            with open(archive_path, 'w') as f:
                json.dump(archive_data, f)
            
            # Delete archived data
            for event in old_events:
                event.delete()
            
            for alert in old_alerts:
                alert.delete()
            
            logger.info(f"Data archived: {archive_path}")
            return archive_path
            
        except Exception as e:
            logger.error(f"Error archiving data: {str(e)}")
            raise
    
    def restore_from_backup(self, backup_path):
        """Restore database from backup"""
        try:
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            # Stop any running processes
            db.session.close()
            
            # Restore database
            shutil.copy2(backup_path, 'instance/cybersecurity.db')
            
            logger.info(f"Database restored from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring from backup: {str(e)}")
            raise
    
    def list_backups(self):
        """List all available backups"""
        try:
            backups = []
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.db'):
                    backup_path = os.path.join(self.backup_dir, filename)
                    meta_path = f'{backup_path}.meta'
                    
                    metadata = {}
                    if os.path.exists(meta_path):
                        with open(meta_path, 'r') as f:
                            metadata = json.load(f)
                    
                    backups.append({
                        'path': backup_path,
                        'timestamp': metadata.get('timestamp'),
                        'type': metadata.get('type'),
                        'size': os.path.getsize(backup_path)
                    })
            
            return sorted(backups, key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing backups: {str(e)}")
            raise 