import os
import sys
import logging

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.app import create_app, socketio
from backend.tasks.backup import BackupScheduler

app = create_app()
backup_scheduler = BackupScheduler()

if __name__ == '__main__':
    try:
        # Start backup scheduler
        backup_scheduler.start()
        
        # Start WebSocket server
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False  # Disable reloader to prevent duplicate scheduler
        )
    except Exception as e:
        logging.error(f"Error starting application: {str(e)}")
        backup_scheduler.stop()
        raise 