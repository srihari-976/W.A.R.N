"""
Response service for handling automated security responses
"""
from typing import Dict, List, Any, Optional, Callable
import logging
from datetime import datetime
import json
from dataclasses import dataclass
from enum import Enum
import threading
import queue
import time

logger = logging.getLogger(__name__)

class ResponseStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ResponsePriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ResponseAction:
    name: str
    description: str
    priority: ResponsePriority
    handler: Callable
    required_params: List[str]
    timeout: int = 300  # seconds

class ResponseService:
    def __init__(self):
        """Initialize response service"""
        self.actions = {}
        self.response_queue = queue.PriorityQueue()
        self.active_responses = {}
        self.response_history = []
        self.lock = threading.Lock()
        
        # Start response worker thread
        self.worker_thread = threading.Thread(target=self._process_responses, daemon=True)
        self.worker_thread.start()
        
        # Register default actions
        self._register_default_actions()

    def _register_default_actions(self):
        """Register default response actions"""
        self.register_action(
            name="block_ip",
            description="Block IP address in firewall",
            priority=ResponsePriority.HIGH,
            handler=self._block_ip,
            required_params=["ip_address", "duration"],
            timeout=60
        )
        
        self.register_action(
            name="isolate_asset",
            description="Isolate asset from network",
            priority=ResponsePriority.CRITICAL,
            handler=self._isolate_asset,
            required_params=["asset_id"],
            timeout=120
        )
        
        self.register_action(
            name="disable_user",
            description="Disable user account",
            priority=ResponsePriority.HIGH,
            handler=self._disable_user,
            required_params=["user_id"],
            timeout=30
        )
        
        self.register_action(
            name="update_firewall_rules",
            description="Update firewall rules",
            priority=ResponsePriority.MEDIUM,
            handler=self._update_firewall_rules,
            required_params=["rules"],
            timeout=180
        )
        
        self.register_action(
            name="scan_asset",
            description="Initiate security scan",
            priority=ResponsePriority.MEDIUM,
            handler=self._scan_asset,
            required_params=["asset_id", "scan_type"],
            timeout=600
        )

    def register_action(self,
                       name: str,
                       description: str,
                       priority: ResponsePriority,
                       handler: Callable,
                       required_params: List[str],
                       timeout: int = 300) -> bool:
        """
        Register a new response action
        
        Args:
            name: Action name
            description: Action description
            priority: Action priority
            handler: Action handler function
            required_params: Required parameters
            timeout: Action timeout in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if name in self.actions:
                logger.warning(f"Action {name} already registered")
                return False
                
            self.actions[name] = ResponseAction(
                name=name,
                description=description,
                priority=priority,
                handler=handler,
                required_params=required_params,
                timeout=timeout
            )
            logger.info(f"Registered action {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering action {name}: {str(e)}")
            return False

    def execute_response(self,
                        action_name: str,
                        params: Dict[str, Any],
                        context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a response action
        
        Args:
            action_name: Name of action to execute
            params: Action parameters
            context: Additional context information
            
        Returns:
            Dictionary containing response status and details
        """
        try:
            if action_name not in self.actions:
                raise ValueError(f"Unknown action: {action_name}")
                
            action = self.actions[action_name]
            
            # Validate required parameters
            missing_params = [
                param for param in action.required_params
                if param not in params
            ]
            if missing_params:
                raise ValueError(f"Missing required parameters: {missing_params}")
                
            # Create response record
            response_id = f"{action_name}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            response = {
                "id": response_id,
                "action": action_name,
                "params": params,
                "context": context or {},
                "status": ResponseStatus.PENDING.value,
                "priority": action.priority.value,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Add to queue
            self.response_queue.put((
                -self._get_priority_value(action.priority),
                response
            ))
            
            return response
            
        except Exception as e:
            logger.error(f"Error executing response {action_name}: {str(e)}")
            return {
                "error": str(e),
                "status": ResponseStatus.FAILED.value
            }

    def _process_responses(self):
        """Process response queue"""
        while True:
            try:
                # Get next response from queue
                _, response = self.response_queue.get()
                
                # Skip if already active
                if response["id"] in self.active_responses:
                    continue
                    
                # Mark as active
                with self.lock:
                    self.active_responses[response["id"]] = response
                
                # Execute action
                action = self.actions[response["action"]]
                response["status"] = ResponseStatus.IN_PROGRESS.value
                response["updated_at"] = datetime.utcnow().isoformat()
                
                try:
                    # Execute handler
                    result = action.handler(**response["params"])
                    
                    # Update response
                    response["status"] = ResponseStatus.COMPLETED.value
                    response["result"] = result
                    
                except Exception as e:
                    logger.error(f"Error executing action {response['action']}: {str(e)}")
                    response["status"] = ResponseStatus.FAILED.value
                    response["error"] = str(e)
                    
                finally:
                    # Update history
                    with self.lock:
                        self.response_history.append(response)
                        del self.active_responses[response["id"]]
                        
            except Exception as e:
                logger.error(f"Error processing response queue: {str(e)}")
                time.sleep(1)

    def _get_priority_value(self, priority: ResponsePriority) -> int:
        """Get numeric value for priority"""
        return {
            ResponsePriority.LOW: 1,
            ResponsePriority.MEDIUM: 2,
            ResponsePriority.HIGH: 3,
            ResponsePriority.CRITICAL: 4
        }[priority]

    def get_response_status(self, response_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a response"""
        # Check active responses
        if response_id in self.active_responses:
            return self.active_responses[response_id]
            
        # Check history
        for response in self.response_history:
            if response["id"] == response_id:
                return response
                
        return None

    def get_active_responses(self) -> List[Dict[str, Any]]:
        """Get list of active responses"""
        return list(self.active_responses.values())

    def get_response_history(self,
                           limit: int = 100,
                           action: Optional[str] = None,
                           status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get response history
        
        Args:
            limit: Maximum number of responses to return
            action: Filter by action name
            status: Filter by status
            
        Returns:
            List of response records
        """
        filtered = self.response_history
        
        if action:
            filtered = [r for r in filtered if r["action"] == action]
            
        if status:
            filtered = [r for r in filtered if r["status"] == status]
            
        return sorted(
            filtered,
            key=lambda x: x["created_at"],
            reverse=True
        )[:limit]

    def cancel_response(self, response_id: str) -> bool:
        """
        Cancel a pending response
        
        Args:
            response_id: ID of response to cancel
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if response_id in self.active_responses:
                response = self.active_responses[response_id]
                if response["status"] == ResponseStatus.PENDING.value:
                    response["status"] = ResponseStatus.CANCELLED.value
                    response["updated_at"] = datetime.utcnow().isoformat()
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling response {response_id}: {str(e)}")
            return False

    # Default action handlers
    def _block_ip(self, ip_address: str, duration: int) -> Dict[str, Any]:
        """Block IP address in firewall"""
        # Implementation would interact with firewall
        return {
            "status": "success",
            "message": f"Blocked IP {ip_address} for {duration} seconds"
        }

    def _isolate_asset(self, asset_id: str) -> Dict[str, Any]:
        """Isolate asset from network"""
        # Implementation would interact with network controls
        return {
            "status": "success",
            "message": f"Isolated asset {asset_id}"
        }

    def _disable_user(self, user_id: str) -> Dict[str, Any]:
        """Disable user account"""
        # Implementation would interact with user management system
        return {
            "status": "success",
            "message": f"Disabled user {user_id}"
        }

    def _update_firewall_rules(self, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update firewall rules"""
        # Implementation would interact with firewall
        return {
            "status": "success",
            "message": f"Updated {len(rules)} firewall rules"
        }

    def _scan_asset(self, asset_id: str, scan_type: str) -> Dict[str, Any]:
        """Initiate security scan"""
        # Implementation would interact with scanning system
        return {
            "status": "success",
            "message": f"Initiated {scan_type} scan on asset {asset_id}"
        } 