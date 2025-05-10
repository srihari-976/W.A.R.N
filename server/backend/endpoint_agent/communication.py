import os
import logging
from typing import Dict, List, Any, Optional, Union, Callable
import json
import time
import threading
import queue
import requests
import websockets
import asyncio
import ssl
import certifi
from datetime import datetime
import hashlib
import hmac
import base64
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class EndpointCommunicator:
    """Handle communication between endpoint agent and server"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.server_url = self.config.get('server_url', 'https://localhost:8000')
        self.websocket_url = self.config.get('websocket_url', 'wss://localhost:8000/ws')
        self.api_key = self.config.get('api_key')
        self.agent_id = self.config.get('agent_id')
        self.event_queue = queue.Queue()
        self.command_queue = queue.Queue()
        self.running = False
        self.websocket = None
        self.websocket_thread = None
        self.heartbeat_thread = None
        
        # Initialize SSL context
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.ssl_context.verify_mode = ssl.CERT_REQUIRED
        self.ssl_context.check_hostname = True
    
    def _generate_signature(self, data: str, timestamp: str) -> str:
        """Generate HMAC signature for authentication"""
        try:
            message = f"{data}{timestamp}"
            signature = hmac.new(
                self.api_key.encode(),
                message.encode(),
                hashlib.sha256
            ).digest()
            return base64.b64encode(signature).decode()
        except Exception as e:
            logger.error(f"Error generating signature: {e}")
            return ""
    
    def _get_headers(self, data: str = "") -> Dict[str, str]:
        """Get headers for API requests"""
        try:
            timestamp = datetime.utcnow().isoformat()
            signature = self._generate_signature(data, timestamp)
            return {
                'Content-Type': 'application/json',
                'X-API-Key': self.api_key,
                'X-Agent-ID': self.agent_id,
                'X-Timestamp': timestamp,
                'X-Signature': signature
            }
        except Exception as e:
            logger.error(f"Error getting headers: {e}")
            return {}
    
    async def _handle_websocket(self):
        """Handle WebSocket connection and messages"""
        try:
            while self.running:
                try:
                    async with websockets.connect(
                        self.websocket_url,
                        ssl=self.ssl_context,
                        extra_headers=self._get_headers()
                    ) as websocket:
                        self.websocket = websocket
                        logger.info("WebSocket connection established")
                        
                        # Start heartbeat
                        asyncio.create_task(self._send_heartbeat())
                        
                        # Handle incoming messages
                        while self.running:
                            try:
                                message = await websocket.recv()
                                await self._handle_message(message)
                            except websockets.exceptions.ConnectionClosed:
                                logger.warning("WebSocket connection closed")
                                break
                            except Exception as e:
                                logger.error(f"Error handling WebSocket message: {e}")
                                break
                except Exception as e:
                    logger.error(f"Error in WebSocket connection: {e}")
                    await asyncio.sleep(5)  # Wait before retrying
        except Exception as e:
            logger.error(f"Error in WebSocket handler: {e}")
        finally:
            self.websocket = None
    
    async def _send_heartbeat(self):
        """Send periodic heartbeat to server"""
        try:
            while self.running and self.websocket:
                try:
                    heartbeat = {
                        'type': 'heartbeat',
                        'agent_id': self.agent_id,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    await self.websocket.send(json.dumps(heartbeat))
                    await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                except Exception as e:
                    logger.error(f"Error sending heartbeat: {e}")
                    break
        except Exception as e:
            logger.error(f"Error in heartbeat sender: {e}")
    
    async def _handle_message(self, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'command':
                # Handle command from server
                command = data.get('command')
                params = data.get('params', {})
                self.command_queue.put({
                    'command': command,
                    'params': params,
                    'timestamp': datetime.utcnow().isoformat()
                })
            elif message_type == 'config_update':
                # Handle configuration update
                new_config = data.get('config', {})
                self._update_config(new_config)
            else:
                logger.warning(f"Unknown message type: {message_type}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    def _update_config(self, new_config: Dict[str, Any]):
        """Update agent configuration"""
        try:
            self.config.update(new_config)
            logger.info("Configuration updated")
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
    
    def send_event(self, event: Dict[str, Any]):
        """Send event to server"""
        try:
            self.event_queue.put(event)
        except Exception as e:
            logger.error(f"Error queueing event: {e}")
    
    async def _send_events(self):
        """Send queued events to server"""
        try:
            while self.running:
                try:
                    # Get events from queue
                    events = []
                    while not self.event_queue.empty():
                        try:
                            event = self.event_queue.get_nowait()
                            events.append(event)
                            self.event_queue.task_done()
                        except queue.Empty:
                            break
                    
                    if events:
                        # Send events to server
                        data = json.dumps({
                            'type': 'events',
                            'agent_id': self.agent_id,
                            'events': events,
                            'timestamp': datetime.utcnow().isoformat()
                        })
                        
                        response = requests.post(
                            urljoin(self.server_url, '/api/events'),
                            data=data,
                            headers=self._get_headers(data),
                            verify=certifi.where()
                        )
                        
                        if response.status_code != 200:
                            logger.error(f"Error sending events: {response.text}")
                            # Put events back in queue
                            for event in events:
                                self.event_queue.put(event)
                    
                    await asyncio.sleep(1)  # Check queue every second
                except Exception as e:
                    logger.error(f"Error sending events: {e}")
                    await asyncio.sleep(5)  # Wait before retrying
        except Exception as e:
            logger.error(f"Error in event sender: {e}")
    
    def get_command(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Get command from queue"""
        try:
            return self.command_queue.get(timeout=timeout)
        except queue.Empty:
            return None
        except Exception as e:
            logger.error(f"Error getting command: {e}")
            return None
    
    def start(self):
        """Start communication"""
        try:
            self.running = True
            
            # Start WebSocket handler
            self.websocket_thread = threading.Thread(
                target=lambda: asyncio.run(self._handle_websocket()),
                daemon=True
            )
            self.websocket_thread.start()
            
            # Start event sender
            self.event_thread = threading.Thread(
                target=lambda: asyncio.run(self._send_events()),
                daemon=True
            )
            self.event_thread.start()
            
            logger.info("Endpoint communication started")
        except Exception as e:
            logger.error(f"Error starting endpoint communication: {e}")
            self.stop()
    
    def stop(self):
        """Stop communication"""
        try:
            self.running = False
            
            # Wait for threads to finish
            if self.websocket_thread:
                self.websocket_thread.join(timeout=5)
            if self.event_thread:
                self.event_thread.join(timeout=5)
            
            logger.info("Endpoint communication stopped")
        except Exception as e:
            logger.error(f"Error stopping endpoint communication: {e}")
    
    def send_command_response(self, command_id: str, success: bool, result: Any = None, error: str = None):
        """Send command response to server"""
        try:
            data = json.dumps({
                'type': 'command_response',
                'agent_id': self.agent_id,
                'command_id': command_id,
                'success': success,
                'result': result,
                'error': error,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            response = requests.post(
                urljoin(self.server_url, '/api/command/response'),
                data=data,
                headers=self._get_headers(data),
                verify=certifi.where()
            )
            
            if response.status_code != 200:
                logger.error(f"Error sending command response: {response.text}")
        except Exception as e:
            logger.error(f"Error sending command response: {e}") 