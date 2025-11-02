# monitor.py - Monitoring module for endpoint agent

import os
import time
import psutil
from datetime import datetime
from threading import Thread, Event
from backend.utils.logging import get_logger
import logging
from typing import Dict, List, Any, Optional, Union, Callable
import queue
import json
import win32file
import win32con
import win32event
import win32api
import win32security
import win32process
import win32service
import wmi
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = get_logger(__name__)

class SystemMonitor(Thread):
    def __init__(self, agent, interval=60):
        """Initialize the system monitor"""
        super().__init__()
        self.agent = agent
        self.interval = interval
        self.stop_event = Event()
        self.daemon = True
    
    def run(self):
        """Main monitoring loop"""
        logger.info("Starting system monitor")
        while not self.stop_event.is_set():
            try:
                self.check_system()
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Error in system monitor: {str(e)}")
                time.sleep(self.interval)
    
    def stop(self):
        """Stop the monitor"""
        self.stop_event.set()
        logger.info("Stopping system monitor")
    
    def check_system(self):
        """Check system metrics and send events if thresholds are exceeded"""
        try:
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                self.agent.add_event('high_cpu', {
                    'cpu_percent': cpu_percent,
                    'threshold': 90
                })
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                self.agent.add_event('high_memory', {
                    'memory_percent': memory.percent,
                    'threshold': 90
                })
            
            # Check disk usage
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                self.agent.add_event('high_disk', {
                    'disk_percent': disk.percent,
                    'threshold': 90
                })
            
            # Check network connections
            connections = psutil.net_connections()
            if len(connections) > 1000:
                self.agent.add_event('high_connections', {
                    'connection_count': len(connections),
                    'threshold': 1000
                })
            
            # Check process count
            process_count = len(psutil.pids())
            if process_count > 500:
                self.agent.add_event('high_process_count', {
                    'process_count': process_count,
                    'threshold': 500
                })
            
        except Exception as e:
            logger.error(f"Error checking system: {str(e)}")

class FileMonitor(Thread):
    def __init__(self, agent, interval=300):
        """Initialize the file monitor"""
        super().__init__()
        self.agent = agent
        self.interval = interval
        self.stop_event = Event()
        self.daemon = True
        self.watched_files = set()
    
    def run(self):
        """Main monitoring loop"""
        logger.info("Starting file monitor")
        while not self.stop_event.is_set():
            try:
                self.check_files()
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Error in file monitor: {str(e)}")
                time.sleep(self.interval)
    
    def stop(self):
        """Stop the monitor"""
        self.stop_event.set()
        logger.info("Stopping file monitor")
    
    def add_file(self, file_path):
        """Add a file to monitor"""
        if os.path.exists(file_path):
            self.watched_files.add(file_path)
            logger.info(f"Added file to monitor: {file_path}")
    
    def remove_file(self, file_path):
        """Remove a file from monitoring"""
        if file_path in self.watched_files:
            self.watched_files.remove(file_path)
            logger.info(f"Removed file from monitor: {file_path}")
    
    def check_files(self):
        """Check monitored files for changes"""
        for file_path in self.watched_files:
            try:
                if not os.path.exists(file_path):
                    self.agent.add_event('file_deleted', {
                        'file_path': file_path
                    })
                    continue
                
                stat = os.stat(file_path)
                file_info = {
                    'file_path': file_path,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'accessed': datetime.fromtimestamp(stat.st_atime).isoformat()
                }
                
                self.agent.add_event('file_changed', file_info)
                
            except Exception as e:
                logger.error(f"Error checking file {file_path}: {str(e)}")

class ProcessMonitor(Thread):
    def __init__(self, agent, interval=60):
        """Initialize the process monitor"""
        super().__init__()
        self.agent = agent
        self.interval = interval
        self.stop_event = Event()
        self.daemon = True
        self.watched_processes = set()
    
    def run(self):
        """Main monitoring loop"""
        logger.info("Starting process monitor")
        while not self.stop_event.is_set():
            try:
                self.check_processes()
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Error in process monitor: {str(e)}")
                time.sleep(self.interval)
    
    def stop(self):
        """Stop the monitor"""
        self.stop_event.set()
        logger.info("Stopping process monitor")
    
    def add_process(self, process_name):
        """Add a process to monitor"""
        self.watched_processes.add(process_name)
        logger.info(f"Added process to monitor: {process_name}")
    
    def remove_process(self, process_name):
        """Remove a process from monitoring"""
        if process_name in self.watched_processes:
            self.watched_processes.remove(process_name)
            logger.info(f"Removed process from monitor: {process_name}")
    
    def check_processes(self):
        """Check monitored processes"""
        for process_name in self.watched_processes:
            try:
                found = False
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    if proc.info['name'] == process_name:
                        found = True
                        process_info = {
                            'process_name': process_name,
                            'pid': proc.info['pid'],
                            'cpu_percent': proc.info['cpu_percent'],
                            'memory_percent': proc.info['memory_percent']
                        }
                        self.agent.add_event('process_running', process_info)
                        break
                
                if not found:
                    self.agent.add_event('process_not_found', {
                        'process_name': process_name
                    })
                
            except Exception as e:
                logger.error(f"Error checking process {process_name}: {str(e)}")

class EndpointMonitor:
    """Monitor endpoint for security-relevant events"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.wmi = wmi.WMI()
        self.event_queue = queue.Queue()
        self.running = False
        self.observers = []
        self.monitoring_threads = []
        
        # Initialize monitoring components
        self._init_file_monitor()
        self._init_process_monitor()
        self._init_network_monitor()
        self._init_registry_monitor()
        self._init_service_monitor()
    
    def _init_file_monitor(self):
        """Initialize file system monitoring"""
        try:
            class FileEventHandler(FileSystemEventHandler):
                def __init__(self, queue):
                    self.queue = queue
                
                def on_any_event(self, event: FileSystemEvent):
                    try:
                        event_info = {
                            'type': 'file_event',
                            'event_type': event.event_type,
                            'path': event.src_path,
                            'timestamp': datetime.now().isoformat()
                        }
                        self.queue.put(event_info)
                    except Exception as e:
                        logger.error(f"Error processing file event: {e}")
            
            self.file_handler = FileEventHandler(self.event_queue)
            self.file_observer = Observer()
            
            # Add paths to monitor from config
            paths_to_monitor = self.config.get('file_monitor_paths', [])
            for path in paths_to_monitor:
                if os.path.exists(path):
                    self.file_observer.schedule(
                        self.file_handler,
                        path,
                        recursive=True
                    )
            
            self.observers.append(self.file_observer)
        except Exception as e:
            logger.error(f"Error initializing file monitor: {e}")
    
    def _init_process_monitor(self):
        """Initialize process monitoring"""
        try:
            def process_monitor_thread():
                last_processes = set()
                while self.running:
                    try:
                        current_processes = set()
                        for proc in psutil.process_iter(['pid', 'name', 'username']):
                            try:
                                process_info = {
                                    'pid': proc.info['pid'],
                                    'name': proc.info['name'],
                                    'username': proc.info['username'],
                                    'command_line': ' '.join(proc.cmdline()),
                                    'create_time': datetime.fromtimestamp(
                                        proc.create_time()
                                    ).isoformat()
                                }
                                current_processes.add(proc.info['pid'])
                                
                                # Check for new processes
                                if proc.info['pid'] not in last_processes:
                                    event_info = {
                                        'type': 'process_event',
                                        'event_type': 'process_started',
                                        'process_info': process_info,
                                        'timestamp': datetime.now().isoformat()
                                    }
                                    self.event_queue.put(event_info)
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
                        
                        # Check for terminated processes
                        for pid in last_processes - current_processes:
                            event_info = {
                                'type': 'process_event',
                                'event_type': 'process_terminated',
                                'pid': pid,
                                'timestamp': datetime.now().isoformat()
                            }
                            self.event_queue.put(event_info)
                        
                        last_processes = current_processes
                        time.sleep(1)  # Check every second
                    except Exception as e:
                        logger.error(f"Error in process monitor thread: {e}")
                        time.sleep(5)  # Wait before retrying
            
            self.monitoring_threads.append(threading.Thread(
                target=process_monitor_thread,
                daemon=True
            ))
        except Exception as e:
            logger.error(f"Error initializing process monitor: {e}")
    
    def _init_network_monitor(self):
        """Initialize network monitoring"""
        try:
            def network_monitor_thread():
                last_connections = set()
                while self.running:
                    try:
                        current_connections = set()
                        for conn in psutil.net_connections(kind='inet'):
                            try:
                                conn_id = f"{conn.laddr.ip}:{conn.laddr.port}-{conn.raddr.ip}:{conn.raddr.port}"
                                current_connections.add(conn_id)
                                
                                # Check for new connections
                                if conn_id not in last_connections:
                                    event_info = {
                                        'type': 'network_event',
                                        'event_type': 'connection_established',
                                        'connection_info': {
                                            'local_address': f"{conn.laddr.ip}:{conn.laddr.port}",
                                            'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}",
                                            'status': conn.status,
                                            'pid': conn.pid,
                                            'type': 'tcp' if conn.type == socket.SOCK_STREAM else 'udp'
                                        },
                                        'timestamp': datetime.now().isoformat()
                                    }
                                    self.event_queue.put(event_info)
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
                        
                        # Check for closed connections
                        for conn_id in last_connections - current_connections:
                            event_info = {
                                'type': 'network_event',
                                'event_type': 'connection_closed',
                                'connection_id': conn_id,
                                'timestamp': datetime.now().isoformat()
                            }
                            self.event_queue.put(event_info)
                        
                        last_connections = current_connections
                        time.sleep(1)  # Check every second
                    except Exception as e:
                        logger.error(f"Error in network monitor thread: {e}")
                        time.sleep(5)  # Wait before retrying
            
            self.monitoring_threads.append(threading.Thread(
                target=network_monitor_thread,
                daemon=True
            ))
        except Exception as e:
            logger.error(f"Error initializing network monitor: {e}")
    
    def _init_registry_monitor(self):
        """Initialize registry monitoring"""
        try:
            def registry_monitor_thread():
                while self.running:
                    try:
                        # Monitor specific registry keys for changes
                        registry_paths = self.config.get('registry_monitor_paths', [])
                        for path in registry_paths:
                            try:
                                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                                    # Get initial values
                                    values = {}
                                    for i in range(winreg.QueryInfoKey(key)[1]):
                                        name, value, _ = winreg.EnumValue(key, i)
                                        values[name] = value
                                    
                                    # Monitor for changes
                                    while self.running:
                                        try:
                                            for i in range(winreg.QueryInfoKey(key)[1]):
                                                name, value, _ = winreg.EnumValue(key, i)
                                                if name not in values or values[name] != value:
                                                    event_info = {
                                                        'type': 'registry_event',
                                                        'event_type': 'value_changed',
                                                        'key_path': path,
                                                        'value_name': name,
                                                        'old_value': values.get(name),
                                                        'new_value': value,
                                                        'timestamp': datetime.now().isoformat()
                                                    }
                                                    self.event_queue.put(event_info)
                                                    values[name] = value
                                        except WindowsError:
                                            continue
                                        time.sleep(1)  # Check every second
                            except WindowsError:
                                continue
                    except Exception as e:
                        logger.error(f"Error in registry monitor thread: {e}")
                        time.sleep(5)  # Wait before retrying
            
            self.monitoring_threads.append(threading.Thread(
                target=registry_monitor_thread,
                daemon=True
            ))
        except Exception as e:
            logger.error(f"Error initializing registry monitor: {e}")
    
    def _init_service_monitor(self):
        """Initialize service monitoring"""
        try:
            def service_monitor_thread():
                last_services = {}
                while self.running:
                    try:
                        current_services = {}
                        for service in self.wmi.Win32_Service():
                            try:
                                service_info = {
                                    'name': service.Name,
                                    'state': service.State,
                                    'start_mode': service.StartMode
                                }
                                current_services[service.Name] = service_info
                                
                                # Check for service state changes
                                if service.Name in last_services:
                                    if service_info['state'] != last_services[service.Name]['state']:
                                        event_info = {
                                            'type': 'service_event',
                                            'event_type': 'state_changed',
                                            'service_name': service.Name,
                                            'old_state': last_services[service.Name]['state'],
                                            'new_state': service_info['state'],
                                            'timestamp': datetime.now().isoformat()
                                        }
                                        self.event_queue.put(event_info)
                                else:
                                    event_info = {
                                        'type': 'service_event',
                                        'event_type': 'service_created',
                                        'service_info': service_info,
                                        'timestamp': datetime.now().isoformat()
                                    }
                                    self.event_queue.put(event_info)
                            except:
                                continue
                        
                        # Check for removed services
                        for service_name in last_services:
                            if service_name not in current_services:
                                event_info = {
                                    'type': 'service_event',
                                    'event_type': 'service_removed',
                                    'service_name': service_name,
                                    'timestamp': datetime.now().isoformat()
                                }
                                self.event_queue.put(event_info)
                        
                        last_services = current_services
                        time.sleep(1)  # Check every second
                    except Exception as e:
                        logger.error(f"Error in service monitor thread: {e}")
                        time.sleep(5)  # Wait before retrying
            
            self.monitoring_threads.append(threading.Thread(
                target=service_monitor_thread,
                daemon=True
            ))
        except Exception as e:
            logger.error(f"Error initializing service monitor: {e}")
    
    def start(self):
        """Start monitoring"""
        try:
            self.running = True
            
            # Start file system observers
            for observer in self.observers:
                observer.start()
            
            # Start monitoring threads
            for thread in self.monitoring_threads:
                thread.start()
            
            logger.info("Endpoint monitoring started")
        except Exception as e:
            logger.error(f"Error starting endpoint monitoring: {e}")
            self.stop()
    
    def stop(self):
        """Stop monitoring"""
        try:
            self.running = False
            
            # Stop file system observers
            for observer in self.observers:
                observer.stop()
                observer.join()
            
            # Wait for monitoring threads to finish
            for thread in self.monitoring_threads:
                thread.join(timeout=5)
            
            logger.info("Endpoint monitoring stopped")
        except Exception as e:
            logger.error(f"Error stopping endpoint monitoring: {e}")
    
    def get_events(self, timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get monitored events from the queue"""
        try:
            events = []
            while True:
                try:
                    event = self.event_queue.get(timeout=timeout)
                    events.append(event)
                    self.event_queue.task_done()
                except queue.Empty:
                    break
            return events
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            return []
