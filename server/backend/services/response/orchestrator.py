from datetime import datetime
from backend.models.alert import Alert
from backend.models.response import Response
from backend.models.asset import Asset
from backend.utils.logging import get_logger

logger = get_logger(__name__)

class ResponseOrchestrator:
    def __init__(self):
        """Initialize response orchestrator"""
        self.response_rules = {
            'malware': {
                'critical': ['isolate_asset', 'block_source', 'scan_asset'],
                'high': ['block_source', 'scan_asset'],
                'medium': ['scan_asset'],
                'low': ['monitor_asset']
            },
            'phishing': {
                'critical': ['block_source', 'alert_users', 'scan_emails'],
                'high': ['block_source', 'alert_users'],
                'medium': ['alert_users'],
                'low': ['monitor_emails']
            },
            'brute_force': {
                'critical': ['block_source', 'reset_credentials', 'enable_mfa'],
                'high': ['block_source', 'reset_credentials'],
                'medium': ['block_source'],
                'low': ['monitor_attempts']
            },
            'data_exfiltration': {
                'critical': ['isolate_asset', 'block_destination', 'freeze_accounts'],
                'high': ['block_destination', 'freeze_accounts'],
                'medium': ['block_destination'],
                'low': ['monitor_traffic']
            },
            'unauthorized_access': {
                'critical': ['isolate_asset', 'block_source', 'reset_credentials'],
                'high': ['block_source', 'reset_credentials'],
                'medium': ['block_source'],
                'low': ['monitor_access']
            },
            'suspicious_activity': {
                'critical': ['monitor_asset', 'alert_security'],
                'high': ['monitor_asset'],
                'medium': ['monitor_asset'],
                'low': ['log_activity']
            }
        }
        
    def get_responses(self, alert_id):
        """
        Get orchestrated responses for an alert
        
        Args:
            alert_id (int): Alert ID
            
        Returns:
            list: List of Response objects
        """
        try:
            # Get alert
            alert = Alert.query.get(alert_id)
            if not alert:
                return []
                
            # Get asset if available
            asset = None
            if alert.asset_id:
                asset = Asset.query.get(alert.asset_id)
                
            # Get response actions based on threat type and severity
            actions = self._get_response_actions(alert.threat_type, alert.severity)
            
            # Create response objects
            responses = []
            for action in actions:
                response = Response(
                    action=action,
                    description=f"{action} for {alert.threat_type}",
                    alert_id=alert.id,
                    created_by_id=1,  # TODO: Get actual user ID
                    parameters=self._get_action_parameters(action, alert, asset)
                )
                response.save()
                responses.append(response)
                
            return responses
            
        except Exception as e:
            logger.error(f"Error getting responses for alert {alert_id}: {str(e)}")
            return []
            
    def _get_response_actions(self, threat_type, severity):
        """
        Get response actions based on threat type and severity
        
        Args:
            threat_type (str): Type of threat
            severity (str): Severity level
            
        Returns:
            list: List of response actions
        """
        try:
            # Get actions for threat type
            threat_actions = self.response_rules.get(threat_type, {})
            
            # Get actions for severity
            actions = threat_actions.get(severity, [])
            
            # Add common actions
            if severity in ['critical', 'high']:
                actions.append('notify_security')
                
            return actions
            
        except Exception as e:
            logger.error(f"Error getting response actions: {str(e)}")
            return []
            
    def _get_action_parameters(self, action, alert, asset):
        """
        Get parameters for a response action
        
        Args:
            action (str): Response action
            alert (Alert): Alert object
            asset (Asset): Asset object
            
        Returns:
            dict: Action parameters
        """
        try:
            parameters = {
                'alert_id': alert.id,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Add asset parameters if available
            if asset:
                parameters.update({
                    'asset_id': asset.id,
                    'asset_name': asset.name,
                    'asset_type': asset.type,
                    'asset_ip': asset.ip_address
                })
                
            # Add action-specific parameters
            if action == 'isolate_asset':
                parameters.update({
                    'isolation_duration': 3600,  # 1 hour
                    'isolation_reason': f"Alert {alert.id}: {alert.description}"
                })
            elif action == 'block_source':
                parameters.update({
                    'block_duration': 86400,  # 24 hours
                    'block_reason': f"Alert {alert.id}: {alert.description}"
                })
            elif action == 'scan_asset':
                parameters.update({
                    'scan_type': 'full',
                    'scan_depth': 'deep'
                })
            elif action == 'alert_users':
                parameters.update({
                    'alert_priority': 'high',
                    'alert_message': f"Security Alert: {alert.description}"
                })
            elif action == 'reset_credentials':
                parameters.update({
                    'reset_type': 'force',
                    'require_mfa': True
                })
            elif action == 'freeze_accounts':
                parameters.update({
                    'freeze_duration': 3600,  # 1 hour
                    'freeze_reason': f"Alert {alert.id}: {alert.description}"
                })
            elif action == 'notify_security':
                parameters.update({
                    'notification_priority': 'high',
                    'notification_channels': ['email', 'slack']
                })
                
            return parameters
            
        except Exception as e:
            logger.error(f"Error getting action parameters: {str(e)}")
            return {} 