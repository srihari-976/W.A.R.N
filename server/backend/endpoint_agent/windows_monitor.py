"""
Windows monitoring agent using WMI and ETW for W.A.R.N
Implements real-time endpoint monitoring as described in the paper
"""
import asyncio
import json
import logging
import wmi
import win32evtlog
import psutil
import requests
from datetime import datetime
from typing import Dict, List, Any
import threading

logger = logging.getLogger(__name__)

class WindowsMonitorAgent:
    """Windows endpoint monitoring agent using WMI and ETW"""
    
    def __init__(self, server_url: str = "http://localhost:5000"):
        self.server_url = server_url
        self.wmi_client = wmi.WMI()
        self.is_running = False
        self.monitoring_threads = []
        
    async def start_monitoring(self):
        """Start all monitoring components"""
        self.is_running = True
        logger.info("🔍 Starting Windows monitoring agent")
        
        # Start monitoring threads
        monitors = [
            self._monitor_processes,
            self._monitor_network,
            self._monitor_file_system,
            self._monitor_registry,
            self._monitor_etw_events
        ]
        
        for monitor in monitors:
            thread = threading.Thread(target=monitor, daemon=True)
            thread.start()
            self.monitoring_threads.append(thread)
        
        logger.info("✅ All monitoring components started")
    
    def _monitor_processes(self):
        """Monitor process creation and termination"""
        try:
            # Monitor process creation
            process_watcher = self.wmi_client.Win32_Process.watch_for("creation")
            
            while self.is_running:
                try:
                    new_process = process_watcher(timeout_ms=1000)
                    if new_process:
                        event = self._create_process_event(new_process)
                        self._send_event(event)
                except Exception as e:
                    if "timed out" not in str(e).lower():
                        logger.error(f"Process monitoring error: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to start process monitoring: {e}")
    
    def _monitor_network(self):
        """Monitor network connections"""
        while self.is_running:
            try:
                connections = psutil.net_connections(kind='inet')
                active_connections = []
                
                for conn in connections:
                    if conn.status == 'ESTABLISHED':
                        active_connections.append({
                            'local_address': f"{conn.laddr.ip}:{conn.laddr.port}",
                            'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                            'pid': conn.pid,
                            'status': conn.status
                        })
                
                if active_connections:
                    event = {
                        'type': 'network_activity',
                        'timestamp': datetime.utcnow().isoformat(),
                        'connections': active_connections,
                        'source': 'windows_agent'
                    }
                    self._send_event(event)
                
                asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Network monitoring error: {e}")
                asyncio.sleep(5)
    
    def _monitor_file_system(self):
        """Monitor file system changes"""
        try:
            # Monitor file creation/modification in sensitive directories
            sensitive_dirs = [
                "C:\\Windows\\System32",
                "C:\\Windows\\SysWOW64",
                "C:\\Users\\*\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
            ]
            
            file_watcher = self.wmi_client.Win32_VolumeChangeEvent.watch_for("creation")
            
            while self.is_running:
                try:
                    file_event = file_watcher(timeout_ms=5000)
                    if file_event:
                        event = {
                            'type': 'file_system_change',
                            'timestamp': datetime.utcnow().isoformat(),
                            'event_type': file_event.EventType,
                            'drive_name': getattr(file_event, 'DriveName', 'Unknown'),
                            'source': 'windows_agent'
                        }
                        self._send_event(event)
                        
                except Exception as e:
                    if "timed out" not in str(e).lower():
                        logger.error(f"File system monitoring error: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to start file system monitoring: {e}")
    
    def _monitor_registry(self):
        """Monitor registry changes"""
        try:
            # Monitor registry changes in critical keys
            registry_watcher = self.wmi_client.RegistryTreeChangeEvent.watch_for("creation")
            
            while self.is_running:
                try:
                    reg_event = registry_watcher(timeout_ms=5000)
                    if reg_event:
                        event = {
                            'type': 'registry_change',
                            'timestamp': datetime.utcnow().isoformat(),
                            'hive': getattr(reg_event, 'Hive', 'Unknown'),
                            'root_path': getattr(reg_event, 'RootPath', 'Unknown'),
                            'source': 'windows_agent'
                        }
                        self._send_event(event)
                        
                except Exception as e:
                    if "timed out" not in str(e).lower():
                        logger.error(f"Registry monitoring error: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to start registry monitoring: {e}")
    
    def _monitor_etw_events(self):
        """Monitor Windows Event Log (ETW) security events"""
        try:
            # Monitor Security event log
            security_events = [4624, 4625, 4688, 4689, 4720, 4726]  # Login, process, account events
            
            while self.is_running:
                try:
                    hand = win32evtlog.OpenEventLog(None, "Security")
                    
                    events = win32evtlog.ReadEventLog(
                        hand,
                        win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ,
                        0
                    )
                    
                    for event in events[-5:]:  # Process last 5 events
                        if event.EventID in security_events:
                            security_event = {
                                'type': 'etw_security',
                                'timestamp': datetime.utcnow().isoformat(),
                                'event_id': event.EventID,
                                'source_name': event.SourceName,
                                'computer_name': event.ComputerName,
                                'data': event.StringInserts[:5] if event.StringInserts else [],  # Limit data
                                'source': 'windows_agent'
                            }
                            self._send_event(security_event)
                    
                    win32evtlog.CloseEventLog(hand)
                    asyncio.sleep(15)  # Check every 15 seconds
                    
                except Exception as e:
                    logger.error(f"ETW monitoring error: {e}")
                    asyncio.sleep(10)
                    
        except Exception as e:
            logger.error(f"Failed to start ETW monitoring: {e}")
    
    def _create_process_event(self, process) -> Dict[str, Any]:
        """Create standardized process event"""
        try:
            # Get additional process info
            pid = process.ProcessId
            process_info = {}
            
            try:
                ps_process = psutil.Process(pid)
                process_info = {
                    'cpu_percent': ps_process.cpu_percent(),
                    'memory_info': ps_process.memory_info()._asdict(),
                    'connections': len(ps_process.connections()),
                    'num_threads': ps_process.num_threads()
                }
            except:
                pass
            
            return {
                'type': 'process_creation',
                'timestamp': datetime.utcnow().isoformat(),
                'process_name': process.Name,
                'process_id': process.ProcessId,
                'command_line': process.CommandLine,
                'parent_process_id': process.ParentProcessId,
                'executable_path': getattr(process, 'ExecutablePath', None),
                'process_info': process_info,
                'source': 'windows_agent'
            }
            
        except Exception as e:
            logger.error(f"Error creating process event: {e}")
            return {
                'type': 'process_creation',
                'timestamp': datetime.utcnow().isoformat(),
                'process_name': getattr(process, 'Name', 'Unknown'),
                'process_id': getattr(process, 'ProcessId', 0),
                'source': 'windows_agent',
                'error': str(e)
            }
    
    def _send_event(self, event: Dict[str, Any]):
        """Send event to W.A.R.N backend"""
        try:
            # Add agent metadata
            event['agent_id'] = 'windows_agent_001'
            event['agent_version'] = '1.0.0'
            
            # Send to backend API
            response = requests.post(
                f"{self.server_url}/api/events/",
                json=event,
                timeout=5,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 201:
                logger.debug(f"Event sent successfully: {event['type']}")
            else:
                logger.warning(f"Failed to send event: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error sending event: {e}")
        except Exception as e:
            logger.error(f"Error sending event: {e}")
    
    def stop_monitoring(self):
        """Stop all monitoring"""
        self.is_running = False
        logger.info("🛑 Stopping Windows monitoring agent")
        
        # Wait for threads to finish
        for thread in self.monitoring_threads:
            thread.join(timeout=5)
        
        logger.info("✅ Windows monitoring agent stopped")

def main():
    """Main entry point for the Windows monitoring agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description='W.A.R.N Windows Monitoring Agent')
    parser.add_argument('--server', default='http://localhost:5000', 
                       help='W.A.R.N server URL')
    parser.add_argument('--log-level', default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start agent
    agent = WindowsMonitorAgent(server_url=args.server)
    
    try:
        asyncio.run(agent.start_monitoring())
        
        # Keep running until interrupted
        while True:
            asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        agent.stop_monitoring()

if __name__ == "__main__":
    main()