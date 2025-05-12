import psutil
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

class ProcessMonitor:
    def __init__(self, socketio):
        self.socketio = socketio
        self.previous_processes = set()
        self.current_processes = set()
        self.update_interval = 1  # seconds

    def get_running_processes(self):
        processes = set()
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status']):
            try:
                pinfo = proc.info
                processes.add((pinfo['pid'], pinfo['name']))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return processes

    def emit_process_event(self, event_type, process_info):
        try:
            self.socketio.emit('process_event', {
                'type': event_type,
                'process': {
                    'pid': process_info[0],
                    'name': process_info[1],
                    'timestamp': datetime.now().isoformat()
                }
            })
            logger.debug(f"Emitted {event_type} event for process {process_info[1]} (PID: {process_info[0]})")
        except Exception as e:
            logger.error(f"Error emitting process event: {e}")

    def monitor_processes(self):
        while True:
            try:
                self.current_processes = self.get_running_processes()
                
                # Check for terminated processes
                terminated = self.previous_processes - self.current_processes
                for process in terminated:
                    self.emit_process_event('process_terminated', process)

                # Check for new processes
                new = self.current_processes - self.previous_processes
                for process in new:
                    self.emit_process_event('process_started', process)

                self.previous_processes = self.current_processes
                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in process monitoring: {e}")
                time.sleep(self.update_interval)

class SystemEventHandler(FileSystemEventHandler):
    def __init__(self, socketio):
        self.socketio = socketio

    def on_any_event(self, event):
        try:
            event_type = event.event_type
            src_path = event.src_path
            
            # Filter out temporary and system files
            if any(pattern in src_path.lower() for pattern in ['.tmp', '.temp', '$recycle.bin', 'system volume information']):
                return

            self.socketio.emit('system_event', {
                'type': event_type,
                'path': src_path,
                'timestamp': datetime.now().isoformat()
            })
            logger.debug(f"Emitted system event: {event_type} for {src_path}")
        except Exception as e:
            logger.error(f"Error handling system event: {e}")

def setup_system_monitoring(socketio):
    try:
        # Initialize process monitor
        process_monitor = ProcessMonitor(socketio)
        
        # Initialize file system observer
        observer = Observer()
        event_handler = SystemEventHandler(socketio)
        
        # Monitor system directories
        paths_to_watch = [
            os.path.expanduser('~'),  # User's home directory
            os.environ.get('TEMP', '/tmp'),  # Temp directory
            os.path.join(os.environ.get('SystemRoot', '/'), 'System32')  # System directory
        ]

        for path in paths_to_watch:
            if os.path.exists(path):
                observer.schedule(event_handler, path, recursive=False)
        
        return process_monitor, observer
    except Exception as e:
        logger.error(f"Error setting up system monitoring: {e}")
        raise 