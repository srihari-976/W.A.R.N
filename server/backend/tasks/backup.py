from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from backend.services.backup import BackupService
import logging

logger = logging.getLogger(__name__)

class BackupScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.backup_service = BackupService()
    
    def start(self):
        """Start the backup scheduler"""
        try:
            # Schedule daily backup at 2 AM
            self.scheduler.add_job(
                self.backup_service.backup_database,
                CronTrigger(hour=2, minute=0),
                id='daily_backup'
            )
            
            # Schedule weekly data archival on Sunday at 3 AM
            self.scheduler.add_job(
                self.backup_service.archive_old_data,
                CronTrigger(day_of_week='sun', hour=3, minute=0),
                id='weekly_archive',
                kwargs={'days': 30}
            )
            
            self.scheduler.start()
            logger.info("Backup scheduler started")
            
        except Exception as e:
            logger.error(f"Error starting backup scheduler: {str(e)}")
            raise
    
    def stop(self):
        """Stop the backup scheduler"""
        try:
            self.scheduler.shutdown()
            logger.info("Backup scheduler stopped")
            
        except Exception as e:
            logger.error(f"Error stopping backup scheduler: {str(e)}")
            raise 