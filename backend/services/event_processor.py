"""
Real-time security event processor for W.A.R.N
Integrates ML inference, anomaly detection, and risk scoring
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor

from backend.services.threat_detector import threat_detector
from backend.models.alert import Alert
from backend.db import db

logger = logging.getLogger(__name__)

class EventProcessor:
    def __init__(self):
        self.is_running = False
        
    async def start(self):
        """Start the event processing pipeline"""
        self.is_running = True
        logger.info("🚀 Event processor started")
        
        # In production, this would read from a message queue
        # For demo, we'll simulate events
        while self.is_running:
            await asyncio.sleep(1)
            # Process any queued events here
    
    async def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process security event through real threat detection pipeline"""
        try:
            result = await threat_detector.analyze_event(event)
            
            if result.get('risk_score', 0) >= 70:
                await self._create_alert(result)
                
                if result.get('risk_score', 0) >= 90:
                    await self._execute_response(result, event)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            return {'error': str(e), 'event_id': event.get('id', 'unknown')}
    
    async def _create_alert(self, alert_data: Dict[str, Any]):
        """Create and save security alert"""
        try:
            alert = Alert(
                event_id=alert_data['event_id'],
                risk_score=alert_data['risk_score'],
                threat_level=alert_data['threat_level'],
                techniques=json.dumps(alert_data['techniques']),
                analysis=alert_data['analysis'],
                is_anomaly=alert_data['is_anomaly'],
                timestamp=alert_data['timestamp'],
                status=alert_data['status']
            )
            
            db.session.add(alert)
            db.session.commit()
            
            # Emit WebSocket event for real-time updates
            from backend.app import socketio
            socketio.emit('new_alert', {
                'id': alert.id,
                'risk_score': alert.risk_score,
                'threat_level': alert.threat_level,
                'techniques': alert_data['techniques'],
                'timestamp': alert.timestamp.isoformat()
            })
            
            logger.info(f"Alert created: {alert.id} (Risk: {alert.risk_score})")
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
    
    async def _execute_response(self, alert: Dict[str, Any], event: Dict[str, Any]):
        """Execute automated response for critical threats"""
        actions = []
        
        # Block suspicious IP addresses
        if event.get('network_connections'):
            for conn in event['network_connections']:
                if conn.get('external'):
                    # Simulate firewall rule
                    actions.append(f"Blocked IP: {conn.get('ip')}")
        
        # Quarantine suspicious processes
        if 'T1059' in alert.get('techniques', []):  # Command execution
            actions.append(f"Terminated process: {event.get('process_name')}")
        
        logger.info(f"Automated response executed: {actions}")
        return actions
    
    def stop(self):
        """Stop the event processor"""
        self.is_running = False
        logger.info("Event processor stopped")

# Global instance
event_processor = EventProcessor()