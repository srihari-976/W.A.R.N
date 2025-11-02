import os
import logging
from typing import Dict, List, Any, Optional, Union, Callable
import json
import time
import threading
import queue
import signal
import sys
from datetime import datetime
import yaml

from .collector import EndpointDataCollector
from .monitor import EndpointMonitor
from .communication import EndpointCommunicator

logger = logging.getLogger(__name__)

class EndpointAgent:
    """Main endpoint agent that coordinates all components"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or 'config/endpoint_agent.yaml'
        self.config = self._load_config()
        self.running = False
        self.collector = None
        self.monitor = None
        self.communicator = None
        self.event_processor_thread = None
        
        # Initialize components
        self._init_components()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load agent configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}
    
    def _init_components(self):
        """Initialize agent components"""
        try:
            # Initialize data collector
            self.collector = EndpointDataCollector(self.config.get('collector', {}))
            
            # Initialize monitor
            self.monitor = EndpointMonitor(self.config.get('monitor', {}))
            
            # Initialize communicator
            self.communicator = EndpointCommunicator(self.config.get('communication', {}))
            
            logger.info("Agent components initialized")
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    def _process_events(self):
        """Process and forward monitored events"""
        try:
            while self.running:
                try:
                    # Get events from monitor
                    events = self.monitor.get_events(timeout=1)
                    
                    if events:
                        # Process each event
                        for event in events:
                            try:
                                # Add agent context
                                event['agent_id'] = self.communicator.agent_id
                                event['hostname'] = self.collector.collect_system_info().get('hostname')
                                
                                # Forward event to server
                                self.communicator.send_event(event)
                            except Exception as e:
                                logger.error(f"Error processing event: {e}")
                except Exception as e:
                    logger.error(f"Error in event processor: {e}")
                    time.sleep(5)  # Wait before retrying
        except Exception as e:
            logger.error(f"Error in event processor thread: {e}")
    
    def _handle_command(self, command: Dict[str, Any]):
        """Handle command from server"""
        try:
            command_type = command.get('command')
            params = command.get('params', {})
            command_id = command.get('command_id')
            
            result = None
            success = True
            error = None
            
            try:
                if command_type == 'collect_data':
                    # Collect specific data
                    data_type = params.get('type')
                    if data_type == 'system_info':
                        result = self.collector.collect_system_info()
                    elif data_type == 'processes':
                        result = self.collector.collect_process_info()
                    elif data_type == 'network':
                        result = self.collector.collect_network_connections()
                    elif data_type == 'software':
                        result = self.collector.collect_installed_software()
                    elif data_type == 'security_events':
                        result = self.collector.collect_security_events()
                    elif data_type == 'users':
                        result = self.collector.collect_user_accounts()
                    elif data_type == 'services':
                        result = self.collector.collect_services()
                    elif data_type == 'all':
                        result = self.collector.collect_all_data()
                    else:
                        raise ValueError(f"Unknown data type: {data_type}")
                
                elif command_type == 'check_file_integrity':
                    # Check file integrity
                    paths = params.get('paths', [])
                    result = self.collector.collect_file_integrity(paths)
                
                elif command_type == 'update_config':
                    # Update agent configuration
                    new_config = params.get('config', {})
                    self.config.update(new_config)
                    self._init_components()  # Reinitialize components with new config
                    result = {'status': 'Configuration updated'}
                
                else:
                    raise ValueError(f"Unknown command type: {command_type}")
            
            except Exception as e:
                success = False
                error = str(e)
                logger.error(f"Error executing command {command_type}: {e}")
            
            # Send command response
            self.communicator.send_command_response(
                command_id=command_id,
                success=success,
                result=result,
                error=error
            )
        
        except Exception as e:
            logger.error(f"Error handling command: {e}")
    
    def _command_processor(self):
        """Process commands from server"""
        try:
            while self.running:
                try:
                    # Get command from communicator
                    command = self.communicator.get_command(timeout=1)
                    
                    if command:
                        self._handle_command(command)
                except Exception as e:
                    logger.error(f"Error in command processor: {e}")
                    time.sleep(5)  # Wait before retrying
        except Exception as e:
            logger.error(f"Error in command processor thread: {e}")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def start(self):
        """Start the endpoint agent"""
        try:
            self.running = True
            
            # Setup signal handlers
            self._setup_signal_handlers()
            
            # Start components
            self.monitor.start()
            self.communicator.start()
            
            # Start event processor
            self.event_processor_thread = threading.Thread(
                target=self._process_events,
                daemon=True
            )
            self.event_processor_thread.start()
            
            # Start command processor
            self.command_processor_thread = threading.Thread(
                target=self._command_processor,
                daemon=True
            )
            self.command_processor_thread.start()
            
            logger.info("Endpoint agent started")
            
            # Keep main thread alive
            while self.running:
                time.sleep(1)
        
        except Exception as e:
            logger.error(f"Error starting endpoint agent: {e}")
            self.stop()
    
    def stop(self):
        """Stop the endpoint agent"""
        try:
            self.running = False
            
            # Stop components
            if self.monitor:
                self.monitor.stop()
            if self.communicator:
                self.communicator.stop()
            
            # Wait for threads to finish
            if self.event_processor_thread:
                self.event_processor_thread.join(timeout=5)
            if self.command_processor_thread:
                self.command_processor_thread.join(timeout=5)
            
            logger.info("Endpoint agent stopped")
        
        except Exception as e:
            logger.error(f"Error stopping endpoint agent: {e}")

def main():
    """Main entry point for the endpoint agent"""
    try:
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create and start agent
        agent = EndpointAgent()
        agent.start()
    
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 