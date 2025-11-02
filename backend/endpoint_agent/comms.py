# comms.py - Communication module for endpoint agent

import json
import requests
from datetime import datetime
from threading import Thread, Event
from backend.utils.logging import get_logger

logger = get_logger(__name__)

class AgentCommunicator(Thread):
    def __init__(self, agent, interval=60):
        """Initialize the agent communicator"""
        super().__init__()
        self.agent = agent
        self.interval = interval
        self.stop_event = Event()
        self.daemon = True
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': f'CyberSecAgent/{agent.system_info["agent_version"]}'
        })
        
        if agent.api_key:
            self.session.headers['Authorization'] = f'Bearer {agent.api_key}'
    
    def run(self):
        """Main communication loop"""
        logger.info("Starting agent communicator")
        while not self.stop_event.is_set():
            try:
                self.send_heartbeat()
                self.send_events()
                self.get_tasks()
                Event().wait(self.interval)
            except Exception as e:
                logger.error(f"Error in communication loop: {str(e)}")
                Event().wait(self.interval)
    
    def stop(self):
        """Stop the communicator"""
        self.stop_event.set()
        logger.info("Stopping agent communicator")
    
    def send_heartbeat(self):
        """Send heartbeat to server"""
        try:
            data = {
                'agent_id': self.agent.agent_id,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'active',
                'metrics': {
                    'cpu_percent': self.agent.process_monitor.cpu_percent,
                    'memory_percent': self.agent.process_monitor.memory_percent,
                    'disk_percent': self.agent.process_monitor.disk_percent,
                    'connection_count': self.agent.process_monitor.connection_count
                }
            }
            
            response = self.session.post(
                f"{self.agent.server_url}/api/agent/heartbeat",
                json=data
            )
            
            if response.status_code == 200:
                logger.debug("Heartbeat sent successfully")
                return True
            else:
                logger.warning(f"Failed to send heartbeat: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending heartbeat: {str(e)}")
            return False
    
    def send_events(self):
        """Send queued events to server"""
        if not self.agent.event_queue:
            return True
            
        try:
            events = self.agent.event_queue.copy()
            self.agent.event_queue.clear()
            
            response = self.session.post(
                f"{self.agent.server_url}/api/agent/events",
                json={'events': events}
            )
            
            if response.status_code == 201:
                logger.info(f"Successfully sent {len(events)} events")
                return True
            else:
                logger.warning(f"Failed to send events: {response.status_code}")
                self.agent.event_queue.extend(events)
                return False
                
        except Exception as e:
            logger.error(f"Error sending events: {str(e)}")
            self.agent.event_queue.extend(events)
            return False
    
    def get_tasks(self):
        """Get pending tasks from server"""
        try:
            response = self.session.get(
                f"{self.agent.server_url}/api/agent/tasks",
                params={'agent_id': self.agent.agent_id}
            )
            
            if response.status_code == 200:
                tasks = response.json().get('tasks', [])
                for task in tasks:
                    self.handle_task(task)
                return True
            else:
                logger.warning(f"Failed to get tasks: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error getting tasks: {str(e)}")
            return False
    
    def handle_task(self, task):
        """Handle a task from the server"""
        try:
            task_id = task.get('task_id')
            task_type = task.get('type')
            task_data = task.get('data', {})
            
            logger.info(f"Handling task {task_id} of type {task_type}")
            
            result = None
            if task_type == 'scan_file':
                result = self.agent.actions.scan_file(task_data.get('file_path'))
            elif task_type == 'kill_process':
                result = self.agent.actions.kill_process(task_data.get('pid'))
            elif task_type == 'block_ip':
                result = self.agent.actions.block_ip(task_data.get('ip_address'))
            elif task_type == 'collect_info':
                result = self.agent.collector.collect_all()
            else:
                logger.warning(f"Unknown task type: {task_type}")
                result = {'success': False, 'error': 'Unknown task type'}
            
            # Send task result back to server
            response = self.session.post(
                f"{self.agent.server_url}/api/agent/task_result",
                json={
                    'task_id': task_id,
                    'result': result,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to send task result: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error handling task {task.get('task_id')}: {str(e)}")
            try:
                # Try to send error back to server
                self.session.post(
                    f"{self.agent.server_url}/api/agent/task_result",
                    json={
                        'task_id': task.get('task_id'),
                        'result': {'success': False, 'error': str(e)},
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
            except:
                pass
