# endpoint_agent.py - Main agent file

import argparse
import json
import os
import platform
import socket
import sys
import time
import uuid
from datetime import datetime
from threading import Thread, Event

import psutil
import requests
from flask import Flask, request, jsonify
from backend.utils.logging import get_logger

# Configure logging
logger = get_logger("CyberSecAgent")

class EndpointAgent:
    def __init__(self, server_url, api_key=None, check_interval=60):
        """
        Initialize the endpoint agent
        
        Args:
            server_url (str): URL of the central server
            api_key (str, optional): API key for authentication
            check_interval (int, optional): Interval in seconds between checks
        """
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.check_interval = check_interval
        self.agent_id = None
        self.hostname = socket.gethostname()
        self.stop_event = Event()
        self.config = {}
        
        # System information
        self.system_info = {
            "hostname": self.hostname,
            "ip_address": self._get_ip_address(),
            "os_type": platform.system(),
            "os_version": platform.version(),
            "agent_version": "1.0.0"
        }
        
        # Initialize components
        self.file_monitor = FileMonitor(self)
        self.process_monitor = ProcessMonitor(self)
        self.network_monitor = NetworkMonitor(self)
        
        # Initialize event queue
        self.event_queue = []
        
    def _get_ip_address(self):
        """Get the primary IP address of the machine"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def register(self):
        """Register the agent with the central server"""
        try:
            response = requests.post(
                f"{self.server_url}/api/agent/register",
                json=self.system_info,
                headers=self._get_headers()
            )
            
            if response.status_code == 201:
                data = response.json()
                self.agent_id = data.get("agent_id")
                logger.info(f"Successfully registered agent with ID: {self.agent_id}")
                return True
            else:
                logger.error(f"Failed to register agent. Status code: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error registering agent: {e}")
            return False
    
    def send_heartbeat(self):
        """Send heartbeat to central server"""
        if not self.agent_id:
            logger.warning("Agent not registered. Cannot send heartbeat.")
            return False
            
        try:
            response = requests.post(
                f"{self.server_url}/api/agent/heartbeat",
                json={"agent_id": self.agent_id},
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                logger.debug("Heartbeat sent successfully")
                return True
            else:
                logger.warning(f"Failed to send heartbeat. Status code: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
            return False
    
    def get_config(self):
        """Get configuration from central server"""
        try:
            response = requests.get(
                f"{self.server_url}/api/agent/config",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                self.config = response.json()
                logger.info("Successfully retrieved configuration")
                return True
            else:
                logger.warning(f"Failed to get configuration. Status code: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error getting configuration: {e}")
            return False
    
    def send_events(self):
        """Send queued events to central server"""
        if not self.event_queue:
            logger.debug("No events to send")
            return True
            
        events_to_send = self.event_queue.copy()
        self.event_queue = []
        
        try:
            response = requests.post(
                f"{self.server_url}/api/agent/events",
                json={"events": events_to_send},
                headers=self._get_headers()
            )
            
            if response.status_code == 201:
                logger.info(f"Successfully sent {len(events_to_send)} events")
                return True
            else:
                # Put the events back in the queue if there was an error
                self.event_queue.extend(events_to_send)
                logger.warning(f"Failed to send events. Status code: {response.status_code}")
                return False
        except Exception as e:
            # Put the events back in the queue if there was an exception
            self.event_queue.extend(events_to_send)
            logger.error(f"Error sending events: {e}")
            return False
    
    def add_event(self, event_type, data):
        """Add an event to the queue"""
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "hostname": self.hostname,
            "agent_id": self.agent_id,
            "event_type": event_type,
            "data": data
        }
        
        self.event_queue.append(event)
        logger.debug(f"Added event to queue: {event_type}")
        
        # Send events immediately if the queue is getting large
        if len(self.event_queue) >= 100:
            self.send_events()
    
    def run(self):
        """Main agent loop"""
        if not self.register():
            logger.error("Failed to register agent. Exiting.")
            return
            
        if not self.get_config():
            logger.warning("Failed to get configuration. Using defaults.")
        
        # Start monitoring threads
        self.file_monitor.start()
        self.process_monitor.start()
        self.network_monitor.start()
        
        last_heartbeat = 0
        last_events_sent = 0
        last_config_check = 0
        
        while not self.stop_event.is_set():
            current_time = time.time()
            
            # Send heartbeat every 5 minutes
            if current_time - last_heartbeat >= 300:
                self.send_heartbeat()
                last_heartbeat = current_time
            
            # Send events every minute
            if current_time - last_events_sent >= 60:
                self.send_events()
                last_events_sent = current_time
            
            # Check config every 15 minutes
            if current_time - last_config_check >= 900:
                self.get_config()
                last_config_check = current_time
            
            # Sleep for a bit
            time.sleep(self.check_interval)
    
    def stop(self):
        """Stop the agent"""
        logger.info("Stopping agent...")
        self.stop_event.set()
        
        # Stop monitoring threads
        self.file_monitor.stop()
        self.process_monitor.stop()
        self.network_monitor.stop()
        
        # Send any remaining events
        self.send_events()
        
        logger.info("Agent stopped")
    
    def _get_headers(self):
        """Get headers for API requests"""
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["X-API-Key"] = self.api_key
            
        return headers

class FileMonitor(Thread):
    def __init__(self, agent):
        """
        Initialize the file monitor
        
        Args:
            agent (EndpointAgent): The agent instance
        """
        super().__init__()
        self.daemon = True
        self.agent = agent
        self.stop_event = Event()
        self.watched_paths = []
        self.last_check = {}
    
    def update_config(self):
        """Update the file monitor configuration"""
        config = self.agent.config.get("monitoring", {}).get("file_integrity", {})
        
        if config.get("enabled", False):
            self.watched_paths = config.get("paths", [])
            self.exclude_paths = config.get("exclude", [])
        else:
            self.watched_paths = []
            self.exclude_paths = []
    
    def run(self):
        """Run the file monitor"""
        logger.info("File monitor started")
        
        self.update_config()
        
        while not self.stop_event.is_set():
            try:
                # Update configuration
                self.update_config()
                
                # Check files if enabled
                if self.watched_paths:
                    self.check_files()
                
                # Sleep for a bit
                time.sleep(60)
            except Exception as e:
                logger.error(f"Error in file monitor: {e}")
                time.sleep(60)
    
    def check_files(self):
        """Check files for changes"""
        for path in self.watched_paths:
            try:
                if not os.path.exists(path):
                    continue
                    
                # Skip excluded paths
                if any(path.startswith(excluded) for excluded in self.exclude_paths):
                    continue
                
                # Get file stats
                stat = os.stat(path)
                mtime = stat.st_mtime
                size = stat.st_size
                
                # Check if file has changed
                if path in self.last_check:
                    last_mtime, last_size = self.last_check[path]
                    
                    if mtime != last_mtime or size != last_size:
                        self.agent.add_event("file_change", {
                            "path": path,
                            "previous_mtime": last_mtime,
                            "current_mtime": mtime,
                            "previous_size": last_size,
                            "current_size": size
                        })
                
                # Update last check
                self.last_check[path] = (mtime, size)
            except Exception as e:
                logger.error(f"Error checking file {path}: {e}")
    
    def stop(self):
        """Stop the file monitor"""
        logger.info("Stopping file monitor...")
        self.stop_event.set()

class ProcessMonitor(Thread):
    def __init__(self, agent):
        """
        Initialize the process monitor
        
        Args:
            agent (EndpointAgent): The agent instance
        """
        super().__init__()
        self.daemon = True
        self.agent = agent
        self.stop_event = Event()
        self.suspicious_paths = []
        self.suspicious_names = []
        self.process_whitelist = []
        self.last_processes = {}
    
    def update_config(self):
        """Update the process monitor configuration"""
        config = self.agent.config.get("monitoring", {}).get("process", {})
        
        if config.get("enabled", False):
            self.suspicious_paths = config.get("suspicious_paths", [])
            self.suspicious_names = config.get("suspicious_names", [])
            self.process_whitelist = config.get("whitelist", [])
        else:
            self.suspicious_paths = []
            self.suspicious_names = []
            self.process_whitelist = []
    
    def run(self):
        """Run the process monitor"""
        logger.info("Process monitor started")
        
        self.update_config()
        
        while not self.stop_event.is_set():
            try:
                # Update configuration
                self.update_config()
                
                # Check processes
                self.check_processes()
                
                # Sleep for a bit
                time.sleep(10)
            except Exception as e:
                logger.error(f"Error in process monitor: {e}")
                time.sleep(10)
    
    def check_processes(self):
        """Check for suspicious processes"""
        current_processes = {}
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'username', 'create_time']):
                try:
                    process_info = proc.info
                    pid = process_info['pid']
                    current_processes[pid] = process_info
                    
                    # Skip whitelisted processes
                    if (process_info['name'] in self.process_whitelist or 
                        process_info['exe'] in self.process_whitelist):
                        continue
                    
                    # Check for suspicious
# Check for new processes
                    if pid not in self.last_processes:
                        # Check for suspicious paths
                        if process_info['exe'] and any(sus_path in process_info['exe'] for sus_path in self.suspicious_paths):
                            self.agent.add_event("suspicious_process", {
                                "pid": pid,
                                "name": process_info['name'],
                                "path": process_info['exe'],
                                "cmdline": process_info['cmdline'],
                                "username": process_info['username'],
                                "reason": "suspicious_path"
                            })
                        
                        # Check for suspicious names
                        if process_info['name'] and any(sus_name in process_info['name'].lower() for sus_name in self.suspicious_names):
                            self.agent.add_event("suspicious_process", {
                                "pid": pid,
                                "name": process_info['name'],
                                "path": process_info['exe'],
                                "cmdline": process_info['cmdline'],
                                "username": process_info['username'],
                                "reason": "suspicious_name"
                            })
                        
                        # Log new process
                        self.agent.add_event("new_process", {
                            "pid": pid,
                            "name": process_info['name'],
                            "path": process_info['exe'],
                            "cmdline": process_info['cmdline'],
                            "username": process_info['username']
                        })
                except Exception as e:
                    logger.error(f"Error checking process {pid}: {e}")
            
            # Check for terminated processes
            for pid in self.last_processes:
                if pid not in current_processes:
                    process_info = self.last_processes[pid]
                    self.agent.add_event("process_terminated", {
                        "pid": pid,
                        "name": process_info['name'],
                        "path": process_info['exe']
                    })
            
            # Update last processes
            self.last_processes = current_processes
        except Exception as e:
            logger.error(f"Error checking processes: {e}")
    
    def stop(self):
        """Stop the process monitor"""
        logger.info("Stopping process monitor...")
        self.stop_event.set()

class NetworkMonitor(Thread):
    def __init__(self, agent):
        """
        Initialize the network monitor
        
        Args:
            agent (EndpointAgent): The agent instance
        """
        super().__init__()
        self.daemon = True
        self.agent = agent
        self.stop_event = Event()
        self.suspicious_ips = []
        self.suspicious_ports = []
        self.connection_whitelist = []
        self.last_connections = {}
    
    def update_config(self):
        """Update the network monitor configuration"""
        config = self.agent.config.get("monitoring", {}).get("network", {})
        
        if config.get("enabled", False):
            self.suspicious_ips = config.get("suspicious_ips", [])
            self.suspicious_ports = config.get("suspicious_ports", [])
            self.connection_whitelist = config.get("whitelist", [])
        else:
            self.suspicious_ips = []
            self.suspicious_ports = []
            self.connection_whitelist = []
    
    def run(self):
        """Run the network monitor"""
        logger.info("Network monitor started")
        
        self.update_config()
        
        while not self.stop_event.is_set():
            try:
                # Update configuration
                self.update_config()
                
                # Check network connections
                self.check_connections()
                
                # Sleep for a bit
                time.sleep(20)
            except Exception as e:
                logger.error(f"Error in network monitor: {e}")
                time.sleep(20)
    
    def check_connections(self):
        """Check for suspicious network connections"""
        current_connections = {}
        
        try:
            for conn in psutil.net_connections(kind='inet'):
                # Skip connections without remote address
                if not conn.raddr:
                    continue
                
                # Build connection key
                conn_key = f"{conn.laddr.ip}:{conn.laddr.port}-{conn.raddr.ip}:{conn.raddr.port}"
                current_connections[conn_key] = conn
                
                # Skip if already seen
                if conn_key in self.last_connections:
                    continue
                
                # Skip whitelisted connections
                if any(whitelist in conn_key for whitelist in self.connection_whitelist):
                    continue
                
                # Check for suspicious IPs
                if any(sus_ip in conn.raddr.ip for sus_ip in self.suspicious_ips):
                    try:
                        # Get process info
                        proc = psutil.Process(conn.pid) if conn.pid else None
                        proc_name = proc.name() if proc else "unknown"
                        proc_exe = proc.exe() if proc else "unknown"
                    except:
                        proc_name = "unknown"
                        proc_exe = "unknown"
                    
                    self.agent.add_event("suspicious_connection", {
                        "local_address": f"{conn.laddr.ip}:{conn.laddr.port}",
                        "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}",
                        "status": conn.status,
                        "pid": conn.pid,
                        "process_name": proc_name,
                        "process_path": proc_exe,
                        "reason": "suspicious_ip"
                    })
                
                # Check for suspicious ports
                if conn.raddr.port in self.suspicious_ports:
                    try:
                        # Get process info
                        proc = psutil.Process(conn.pid) if conn.pid else None
                        proc_name = proc.name() if proc else "unknown"
                        proc_exe = proc.exe() if proc else "unknown"
                    except:
                        proc_name = "unknown"
                        proc_exe = "unknown"
                    
                    self.agent.add_event("suspicious_connection", {
                        "local_address": f"{conn.laddr.ip}:{conn.laddr.port}",
                        "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}",
                        "status": conn.status,
                        "pid": conn.pid,
                        "process_name": proc_name,
                        "process_path": proc_exe,
                        "reason": "suspicious_port"
                    })
                
                # Log new connection
                self.agent.add_event("new_connection", {
                    "local_address": f"{conn.laddr.ip}:{conn.laddr.port}",
                    "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}",
                    "status": conn.status,
                    "pid": conn.pid
                })
            
            # Update last connections
            self.last_connections = current_connections
        except Exception as e:
            logger.error(f"Error checking connections: {e}")
    
    def stop(self):
        """Stop the network monitor"""
        logger.info("Stopping network monitor...")
        self.stop_event.set()

# Create Flask application for API server
app = Flask(__name__)
agent = None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route('/api/task', methods=['POST'])
def receive_task():
    """Receive a task from the central server"""
    # Check API key
    api_key = request.headers.get('X-API-Key')
    if not api_key or api_key != agent.api_key:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        data = request.json
        task_type = data.get('task_type')
        task_data = data.get('data', {})
        task_id = data.get('task_id')
        
        logger.info(f"Received task: {task_type} (ID: {task_id})")
        
        # Handle task
        result = handle_task(task_type, task_data, task_id)
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error handling task: {e}")
        return jsonify({"error": str(e)}), 500

def handle_task(task_type, task_data, task_id):
    """Handle a task from the central server"""
    result = {
        "task_id": task_id,
        "status": "completed",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        if task_type == "scan_file":
            path = task_data.get('path')
            if os.path.exists(path):
                stat = os.stat(path)
                result["data"] = {
                    "exists": True,
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                    "ctime": stat.st_ctime
                }
            else:
                result["data"] = {"exists": False}
                
        elif task_type == "process_list":
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'username', 'create_time']):
                processes.append(proc.info)
            result["data"] = {"processes": processes}
            
        elif task_type == "network_scan":
            connections = []
            for conn in psutil.net_connections(kind='inet'):
                conn_info = {
                    "local_address": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                    "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                    "status": conn.status,
                    "pid": conn.pid
                }
                connections.append(conn_info)
            result["data"] = {"connections": connections}
            
        elif task_type == "system_info":
            result["data"] = {
                "hostname": socket.gethostname(),
                "ip_address": agent._get_ip_address(),
                "os_type": platform.system(),
                "os_version": platform.version(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "disk_total": psutil.disk_usage('/').total,
                "disk_free": psutil.disk_usage('/').free
            }
            
        elif task_type == "update_config":
            agent.config = task_data
            agent.file_monitor.update_config()
            agent.process_monitor.update_config()
            agent.network_monitor.update_config()
            result["data"] = {"updated": True}
            
        else:
            result["status"] = "error"
            result["error"] = f"Unknown task type: {task_type}"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

def start_api_server(host='0.0.0.0', port=5000):
    """Start the API server"""
    logger.info(f"Starting API server on {host}:{port}")
    app.run(host=host, port=port, debug=False)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Cybersecurity Endpoint Agent")
    parser.add_argument("--server", required=True, help="Central server URL")
    parser.add_argument("--key", help="API key for authentication")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds")
    parser.add_argument("--api-host", default="0.0.0.0", help="API server host")
    parser.add_argument("--api-port", type=int, default=5000, help="API server port")
    args = parser.parse_args()
    
    global agent
    agent = EndpointAgent(args.server, args.key, args.interval)
    
    # Start API server in a separate thread
    api_thread = Thread(target=start_api_server, args=(args.api_host, args.api_port))
    api_thread.daemon = True
    api_thread.start()
    
    try:
        # Run the agent
        agent.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Stopping agent...")
        agent.stop()
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        agent.stop()

if __name__ == "__main__":
    main()
