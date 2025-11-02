# collector.py - Data collection module for endpoint agent

import os
import logging
from typing import Dict, List, Any, Optional, Union
import psutil
import platform
import socket
import json
from datetime import datetime
import winreg
import subprocess
import hashlib
import re
import win32security
import win32file
import win32con
import win32api
import win32process
import win32service
import win32event
import win32com.client
import wmi

logger = logging.getLogger(__name__)

class EndpointDataCollector:
    """Collect security-relevant data from endpoint"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.wmi = wmi.WMI()
    
    def collect_system_info(self) -> Dict[str, Any]:
        """Collect basic system information"""
        try:
            return {
                'hostname': socket.gethostname(),
                'os': {
                    'system': platform.system(),
                    'release': platform.release(),
                    'version': platform.version(),
                    'machine': platform.machine()
                },
                'cpu': {
                    'physical_cores': psutil.cpu_count(logical=False),
                    'total_cores': psutil.cpu_count(logical=True),
                    'usage_percent': psutil.cpu_percent(interval=1)
                },
                'memory': {
                    'total': psutil.virtual_memory().total,
                    'available': psutil.virtual_memory().available,
                    'used_percent': psutil.virtual_memory().percent
                },
                'disk': {
                    'total': psutil.disk_usage('/').total,
                    'used': psutil.disk_usage('/').used,
                    'free': psutil.disk_usage('/').free
                },
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error collecting system info: {e}")
            return {}
    
    def collect_process_info(self) -> List[Dict[str, Any]]:
        """Collect information about running processes"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                try:
                    process_info = proc.info
                    process_info['command_line'] = ' '.join(proc.cmdline())
                    process_info['create_time'] = datetime.fromtimestamp(proc.create_time()).isoformat()
                    processes.append(process_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return processes
        except Exception as e:
            logger.error(f"Error collecting process info: {e}")
            return []
    
    def collect_network_connections(self) -> List[Dict[str, Any]]:
        """Collect network connection information"""
        try:
            connections = []
            for conn in psutil.net_connections(kind='inet'):
                try:
                    connection_info = {
                        'local_address': f"{conn.laddr.ip}:{conn.laddr.port}",
                        'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                        'status': conn.status,
                        'pid': conn.pid,
                        'type': 'tcp' if conn.type == socket.SOCK_STREAM else 'udp'
                    }
                    connections.append(connection_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return connections
        except Exception as e:
            logger.error(f"Error collecting network connections: {e}")
            return []
    
    def collect_installed_software(self) -> List[Dict[str, Any]]:
        """Collect information about installed software"""
        try:
            software_list = []
            
            # Query Windows registry for installed software
            registry_paths = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
            ]
            
            for path in registry_paths:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                with winreg.OpenKey(key, subkey_name) as subkey:
                                    try:
                                        name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                        version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                        install_date = winreg.QueryValueEx(subkey, "InstallDate")[0]
                                        publisher = winreg.QueryValueEx(subkey, "Publisher")[0]
                                        
                                        software_list.append({
                                            'name': name,
                                            'version': version,
                                            'install_date': install_date,
                                            'publisher': publisher
                                        })
                                    except WindowsError:
                                        continue
                            except WindowsError:
                                continue
                except WindowsError:
                    continue
            
            return software_list
        except Exception as e:
            logger.error(f"Error collecting installed software: {e}")
            return []
    
    def collect_security_events(self) -> List[Dict[str, Any]]:
        """Collect security-related events"""
        try:
            events = []
            
            # Collect Windows Security events
            for event in self.wmi.Win32_NTLogEvent(LogFile="Security"):
                try:
                    event_info = {
                        'event_id': event.EventCode,
                        'event_type': event.Type,
                        'source': event.SourceName,
                        'message': event.Message,
                        'time_generated': event.TimeGenerated,
                        'time_written': event.TimeWritten,
                        'category': event.Category
                    }
                    events.append(event_info)
                except:
                    continue
            
            return events
        except Exception as e:
            logger.error(f"Error collecting security events: {e}")
            return []
    
    def collect_file_integrity(self, paths: List[str]) -> List[Dict[str, Any]]:
        """Collect file integrity information"""
        try:
            integrity_info = []
            
            for path in paths:
                try:
                    if os.path.exists(path):
                        file_info = {
                            'path': path,
                            'size': os.path.getsize(path),
                            'modified_time': datetime.fromtimestamp(
                                os.path.getmtime(path)
                            ).isoformat(),
                            'created_time': datetime.fromtimestamp(
                                os.path.getctime(path)
                            ).isoformat(),
                            'attributes': win32file.GetFileAttributes(path)
                        }
                        
                        # Calculate file hash
                        with open(path, 'rb') as f:
                            file_hash = hashlib.sha256(f.read()).hexdigest()
                            file_info['hash'] = file_hash
                        
                        integrity_info.append(file_info)
                except Exception as e:
                    logger.error(f"Error collecting integrity info for {path}: {e}")
                    continue
            
            return integrity_info
        except Exception as e:
            logger.error(f"Error collecting file integrity: {e}")
            return []
    
    def collect_user_accounts(self) -> List[Dict[str, Any]]:
        """Collect user account information"""
        try:
            users = []
            
            for user in self.wmi.Win32_UserAccount():
                try:
                    user_info = {
                        'name': user.Name,
                        'full_name': user.FullName,
                        'description': user.Description,
                        'disabled': user.Disabled,
                        'account_type': user.AccountType,
                        'sid': user.SID,
                        'domain': user.Domain
                    }
                    users.append(user_info)
                except:
                    continue
            
            return users
        except Exception as e:
            logger.error(f"Error collecting user accounts: {e}")
            return []
    
    def collect_services(self) -> List[Dict[str, Any]]:
        """Collect service information"""
        try:
            services = []
            
            for service in self.wmi.Win32_Service():
                try:
                    service_info = {
                        'name': service.Name,
                        'display_name': service.DisplayName,
                        'state': service.State,
                        'start_mode': service.StartMode,
                        'path_name': service.PathName,
                        'start_name': service.StartName,
                        'description': service.Description
                    }
                    services.append(service_info)
                except:
                    continue
            
            return services
        except Exception as e:
            logger.error(f"Error collecting services: {e}")
            return []
    
    def collect_all_data(self) -> Dict[str, Any]:
        """Collect all endpoint data"""
        try:
            return {
                'system_info': self.collect_system_info(),
                'processes': self.collect_process_info(),
                'network_connections': self.collect_network_connections(),
                'installed_software': self.collect_installed_software(),
                'security_events': self.collect_security_events(),
                'user_accounts': self.collect_user_accounts(),
                'services': self.collect_services(),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error collecting all data: {e}")
            return {}
