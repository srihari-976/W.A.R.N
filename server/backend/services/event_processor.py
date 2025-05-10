from flask_socketio import emit
from backend.models.event import SecurityEvent
from backend.models.alert import Alert
from backend.models.asset import Asset
from backend.services.risk.scoring import calculate_risk_score
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class EventProcessor:
    def __init__(self, socketio):
        self.socketio = socketio
        self.risk_thresholds = {
            'low': 30,
            'medium': 70,
            'high': 90
        }
    
    def process_event(self, event_data):
        """Process a new security event"""
        try:
            # Validate required fields
            if not event_data.get('type') or not event_data.get('source_ip') or not event_data.get('details'):
                logger.error("Missing required fields in event data")
                return None, {'score': 0.0, 'factors': {}, 'category': 'unknown', 'timestamp': datetime.utcnow().isoformat()}
            
            # Create event
            event = SecurityEvent(
                type=event_data['type'],
                source_ip=event_data['source_ip'],
                details=event_data['details'],
                severity=event_data.get('severity', 'medium'),
                status='new'
            )
            event.save()
            
            # Calculate risk score
            risk_score = calculate_risk_score(event)
            
            # Check if alert should be generated
            if risk_score['score'] >= self.risk_thresholds['medium']:
                self._create_alert(event, risk_score)
            
            # Emit real-time updates
            self._emit_updates(event, risk_score)
            
            return event, risk_score
            
        except Exception as e:
            logger.error(f"Error processing event: {str(e)}")
            raise
    
    def _create_alert(self, event, risk_score):
        """Create an alert based on event and risk score"""
        try:
            alert = Alert(
                event_id=event.id,
                severity=event.severity,
                message=f"High risk event detected: {event.type}",
                status='new',
                risk_score=risk_score['score']
            )
            alert.save()
            
            # Emit alert notification
            self.socketio.emit('new_alert', alert.to_dict())
            
            return alert
            
        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}")
            raise
    
    def _emit_updates(self, event, risk_score):
        """Emit real-time updates to connected clients"""
        try:
            # Emit event update
            self.socketio.emit('new_event', {
                'event': event.to_dict(),
                'risk_score': risk_score
            })
            
            # Emit risk score update
            self.socketio.emit('risk_update', {
                'event_id': event.id,
                'score': risk_score['score'],
                'factors': risk_score['factors']
            })
            
        except Exception as e:
            logger.error(f"Error emitting updates: {str(e)}")
            raise
    
    def monitor_asset(self, asset_id):
        """Monitor an asset for security events"""
        try:
            asset = Asset.get_by_id(asset_id)
            if not asset:
                raise ValueError(f"Asset not found: {asset_id}")
            
            # Get recent events for asset
            events = SecurityEvent.get_by_asset(asset_id)
            
            # Calculate overall risk
            risk_score = calculate_risk_score(asset=asset, events=events)
            
            # Emit asset status update
            self.socketio.emit('asset_status', {
                'asset_id': asset_id,
                'status': asset.status,
                'risk_score': risk_score
            })
            
            return risk_score
            
        except Exception as e:
            logger.error(f"Error monitoring asset: {str(e)}")
            raise 