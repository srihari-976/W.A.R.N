from backend.models.alert import Alert
from backend.models.event import SecurityEvent
from backend.models.asset import Asset
from backend.models.risk_score import RiskScore
from backend.db import db
from datetime import datetime, timedelta
import logging
import numpy as np
import os
from typing import Dict, List, Any, Optional, Union
import json
from sklearn.preprocessing import MinMaxScaler
import pandas as pd

logger = logging.getLogger(__name__)

# Risk score weights
THREAT_WEIGHTS = {
    'malware': 0.8,
    'phishing': 0.7,
    'brute_force': 0.6,
    'data_exfiltration': 0.9,
    'unauthorized_access': 0.7,
    'suspicious_activity': 0.5
}

SEVERITY_WEIGHTS = {
    'critical': 1.0,
    'high': 0.8,
    'medium': 0.5,
    'low': 0.2
}

class RiskScorer:
    """Risk scoring system for security events"""
    
    def __init__(self):
        self.scaler = MinMaxScaler()
        self.risk_factors = {
            'severity': {
                'critical': 1.0,
                'high': 0.8,
                'medium': 0.5,
                'low': 0.2,
                'info': 0.1
            },
            'confidence': {
                'high': 1.0,
                'medium': 0.6,
                'low': 0.3
            },
            'threat_type': {
                'malware': 1.0,
                'phishing': 0.9,
                'brute_force': 0.8,
                'data_exfiltration': 0.95,
                'unauthorized_access': 0.85,
                'suspicious_activity': 0.7
            }
        }
        
        # Initialize historical risk scores
        self.historical_scores = []
        self.score_thresholds = {
            'critical': 0.8,
            'high': 0.6,
            'medium': 0.4,
            'low': 0.2
        }
    
    def _calculate_base_risk_score(self, event: Dict[str, Any]) -> float:
        """Calculate base risk score from event attributes"""
        try:
            # Get severity score
            severity = event.get('severity', 'low').lower()
            severity_score = self.risk_factors['severity'].get(severity, 0.1)
            
            # Get confidence score
            confidence = event.get('confidence', 'low').lower()
            confidence_score = self.risk_factors['confidence'].get(confidence, 0.3)
            
            # Get threat type score
            threat_type = event.get('threat_type', 'suspicious_activity').lower()
            threat_score = self.risk_factors['threat_type'].get(threat_type, 0.5)
            
            # Calculate base score
            base_score = (severity_score * 0.4 + confidence_score * 0.3 + threat_score * 0.3)
            
            return base_score
            
        except Exception as e:
            logger.error(f"Error calculating base risk score: {e}")
            return 0.0
    
    def _calculate_contextual_factors(self, event: Dict[str, Any]) -> float:
        """Calculate contextual risk factors"""
        try:
            contextual_score = 0.0
            factors = 0
            
            # Check if source IP is internal
            source_ip = event.get('source_ip', '')
            if source_ip and (
                source_ip.startswith('10.') or
                source_ip.startswith('172.16.') or
                source_ip.startswith('192.168.')
            ):
                contextual_score += 0.3
                factors += 1
            
            # Check if destination IP is sensitive
            dest_ip = event.get('destination_ip', '')
            if dest_ip and dest_ip in self._get_sensitive_ips():
                contextual_score += 0.4
                factors += 1
            
            # Check if event occurred during business hours
            timestamp = event.get('timestamp')
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp)
                    if 9 <= timestamp.hour <= 17:
                        contextual_score += 0.2
                        factors += 1
                except:
                    pass
            
            # Check if event involves sensitive data
            if self._contains_sensitive_data(event):
                contextual_score += 0.3
                factors += 1
            
            # Normalize contextual score
            if factors > 0:
                contextual_score /= factors
            
            return contextual_score
            
        except Exception as e:
            logger.error(f"Error calculating contextual factors: {e}")
            return 0.0
    
    def _get_sensitive_ips(self) -> List[str]:
        """Get list of sensitive IP addresses"""
        # This would typically come from a configuration or database
        return [
            '192.168.1.100',  # Database server
            '192.168.1.101',  # Authentication server
            '192.168.1.102'   # File server
        ]
    
    def _contains_sensitive_data(self, event: Dict[str, Any]) -> bool:
        """Check if event involves sensitive data"""
        sensitive_keywords = [
            'password', 'credit card', 'ssn', 'social security',
            'personal information', 'confidential', 'secret'
        ]
        
        # Check description
        description = event.get('description', '').lower()
        if any(keyword in description for keyword in sensitive_keywords):
            return True
        
        # Check additional fields
        for field in ['message', 'details', 'payload']:
            if field in event:
                field_value = str(event[field]).lower()
                if any(keyword in field_value for keyword in sensitive_keywords):
                    return True
        
        return False
    
    def _calculate_temporal_factors(self, event: Dict[str, Any]) -> float:
        """Calculate temporal risk factors"""
        try:
            temporal_score = 0.0
            
            # Get event timestamp
            timestamp = event.get('timestamp')
            if not timestamp:
                return 0.0
            
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            
            # Check if event occurred recently
            now = datetime.now()
            time_diff = (now - timestamp).total_seconds()
            
            # Recent events get higher scores
            if time_diff < 3600:  # Within last hour
                temporal_score = 1.0
            elif time_diff < 86400:  # Within last day
                temporal_score = 0.8
            elif time_diff < 604800:  # Within last week
                temporal_score = 0.6
            else:
                temporal_score = 0.4
            
            return temporal_score
            
        except Exception as e:
            logger.error(f"Error calculating temporal factors: {e}")
            return 0.0
    
    def calculate_risk_score(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive risk score for an event"""
        try:
            # Calculate component scores
            base_score = self._calculate_base_risk_score(event)
            contextual_score = self._calculate_contextual_factors(event)
            temporal_score = self._calculate_temporal_factors(event)
            
            # Calculate final risk score
            risk_score = (
                base_score * 0.5 +
                contextual_score * 0.3 +
                temporal_score * 0.2
            )
            
            # Determine risk level
            risk_level = 'low'
            for level, threshold in sorted(
                self.score_thresholds.items(),
                key=lambda x: x[1],
                reverse=True
            ):
                if risk_score >= threshold:
                    risk_level = level
                    break
            
            # Store historical score
            self.historical_scores.append(risk_score)
            if len(self.historical_scores) > 1000:  # Keep last 1000 scores
                self.historical_scores.pop(0)
            
            # Calculate score statistics
            score_stats = {
                'mean': np.mean(self.historical_scores),
                'std': np.std(self.historical_scores),
                'percentile_90': np.percentile(self.historical_scores, 90)
            }
            
            return {
                'risk_score': float(risk_score),
                'risk_level': risk_level,
                'component_scores': {
                    'base_score': float(base_score),
                    'contextual_score': float(contextual_score),
                    'temporal_score': float(temporal_score)
                },
                'score_statistics': score_stats,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return {
                'error': str(e),
                'risk_score': 0.0,
                'risk_level': 'unknown',
                'component_scores': {
                    'base_score': 0.0,
                    'contextual_score': 0.0,
                    'temporal_score': 0.0
                },
                'score_statistics': {
                    'mean': 0.0,
                    'std': 0.0,
                    'percentile_90': 0.0
                },
                'timestamp': datetime.now().isoformat()
            }
    
    def batch_calculate_risk_scores(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate risk scores for multiple events"""
        try:
            results = []
            for event in events:
                risk_assessment = self.calculate_risk_score(event)
                results.append({
                    'event': event,
                    'risk_assessment': risk_assessment
                })
            return results
        except Exception as e:
            logger.error(f"Error in batch risk calculation: {e}")
            raise
    
    def update_risk_thresholds(self, new_thresholds: Dict[str, float]):
        """Update risk score thresholds"""
        try:
            self.score_thresholds.update(new_thresholds)
            logger.info(f"Updated risk thresholds: {self.score_thresholds}")
        except Exception as e:
            logger.error(f"Error updating risk thresholds: {e}")
            raise
    
    def get_risk_statistics(self) -> Dict[str, Any]:
        """Get statistics about risk scores"""
        try:
            if not self.historical_scores:
                return {
                    'mean': 0.0,
                    'std': 0.0,
                    'min': 0.0,
                    'max': 0.0,
                    'percentiles': {
                        '25': 0.0,
                        '50': 0.0,
                        '75': 0.0,
                        '90': 0.0
                    }
                }
            
            return {
                'mean': float(np.mean(self.historical_scores)),
                'std': float(np.std(self.historical_scores)),
                'min': float(np.min(self.historical_scores)),
                'max': float(np.max(self.historical_scores)),
                'percentiles': {
                    '25': float(np.percentile(self.historical_scores, 25)),
                    '50': float(np.percentile(self.historical_scores, 50)),
                    '75': float(np.percentile(self.historical_scores, 75)),
                    '90': float(np.percentile(self.historical_scores, 90))
                }
            }
        except Exception as e:
            logger.error(f"Error getting risk statistics: {e}")
            return {}

def calculate_risk_score(event_id, asset_id):
    """Calculate risk score for an event on an asset"""
    try:
        # Get event and asset
        event = SecurityEvent.query.get(event_id)
        asset = Asset.query.get(asset_id)
        
        if not event or not asset:
            logger.error(f"Event {event_id} or asset {asset_id} not found")
            return {
                'score': 0.0,
                'factors': {},
                'category': 'unknown',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        # Calculate base score
        base_score = 50  # Default medium risk
        
        # Adjust based on event type
        if event.type in ['malware', 'exploit', 'data_exfiltration']:
            base_score += 30
        elif event.type in ['suspicious_activity', 'unauthorized_access']:
            base_score += 20
            
        # Adjust based on asset criticality
        if asset.criticality == 'high':
            base_score += 20
        elif asset.criticality == 'medium':
            base_score += 10
            
        # Normalize score to 0-100
        risk_score = min(max(base_score, 0), 100)
        
        # Determine risk category
        if risk_score >= 80:
            category = "High"
        elif risk_score >= 50:
            category = "Medium"
        else:
            category = "Low"
            
        # Create risk score record
        risk_score_record = RiskScore(
            event_id=event_id,
            asset_id=asset_id,
            score=risk_score,
            category=category,
            timestamp=datetime.utcnow()
        )
        
        db.session.add(risk_score_record)
        db.session.commit()
        
        return {
            'score': risk_score,
            'factors': {},
            'category': category,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error calculating risk score: {str(e)}")
        return {
            'score': 0.0,
            'factors': {},
            'category': 'unknown',
            'timestamp': datetime.utcnow().isoformat()
        }

def calculate_time_decay(events):
    """
    Calculate time decay factor for events
    
    Args:
        events (list): List of Event objects
        
    Returns:
        float: Time decay factor between 0 and 1
    """
    try:
        if not events:
            return 1.0
            
        # Get most recent event time
        latest_time = max(event.timestamp for event in events)
        
        # Calculate hours since latest event
        hours_ago = (datetime.utcnow() - latest_time).total_seconds() / 3600
        
        # Apply exponential decay
        decay_factor = np.exp(-hours_ago / 24)  # 24-hour half-life
        
        return decay_factor
        
    except Exception as e:
        logger.error(f"Error calculating time decay: {str(e)}")
        return 1.0

def calculate_asset_factor(asset):
    """
    Calculate risk factor based on asset properties
    
    Args:
        asset (Asset): Asset object
        
    Returns:
        float: Asset risk factor between 0.5 and 1.5
    """
    try:
        factor = 1.0
        
        # Adjust based on asset type
        if asset.type == 'server':
            factor *= 1.2
        elif asset.type == 'database':
            factor *= 1.3
        elif asset.type == 'network_device':
            factor *= 1.1
            
        # Adjust based on asset criticality
        if asset.criticality >= 0.8:
            factor *= 1.2
        elif asset.criticality <= 0.3:
            factor *= 0.8
            
        # Ensure factor is within bounds
        factor = min(max(factor, 0.5), 1.5)
        
        return factor
        
    except Exception as e:
        logger.error(f"Error calculating asset factor: {str(e)}")
        return 1.0

def get_risk_level(risk_score):
    """
    Convert risk score to risk level
    
    Args:
        risk_score (float): Risk score between 0 and 1
        
    Returns:
        str: Risk level ('low', 'medium', 'high', 'critical')
    """
    try:
        if risk_score >= 0.8:
            return 'critical'
        elif risk_score >= 0.6:
            return 'high'
        elif risk_score >= 0.3:
            return 'medium'
        else:
            return 'low'
            
    except Exception as e:
        logger.error(f"Error getting risk level: {str(e)}")
        return 'low'

def update_asset_risk(asset_id):
    """
    Update risk score and level for an asset
    
    Args:
        asset_id (int): Asset ID
        
    Returns:
        tuple: (risk_score, risk_level)
    """
    try:
        # Get asset
        asset = Asset.query.get(asset_id)
        if not asset:
            return None, None
            
        # Get recent events for asset
        recent_events = SecurityEvent.query.filter(
            SecurityEvent.asset_id == asset_id,
            SecurityEvent.timestamp >= datetime.utcnow() - timedelta(days=7)
        ).all()
        
        # Calculate risk score
        risk_score = calculate_risk_score(recent_events[0].id, asset_id)
        
        # Get risk level
        risk_level = get_risk_level(risk_score)
        
        # Update asset
        asset.risk_score = risk_score
        asset.risk_level = risk_level
        asset.save()
        
        return risk_score, risk_level
        
    except Exception as e:
        logger.error(f"Error updating asset risk: {str(e)}")
        return None, None

def update_alert_risk(alert_id):
    """
    Update risk score and severity for an alert
    
    Args:
        alert_id (int): Alert ID
        
    Returns:
        tuple: (risk_score, severity)
    """
    try:
        # Get alert
        alert = Alert.query.get(alert_id)
        if not alert:
            return None, None
            
        # Get related events
        events = alert.events
        
        # Get asset if available
        asset = None
        if alert.asset_id:
            asset = Asset.query.get(alert.asset_id)
            
        # Calculate risk score
        risk_score = calculate_risk_score(events[0].id, alert.asset_id)
        
        # Get severity level
        severity = get_risk_level(risk_score)
        
        # Update alert
        alert.risk_score = risk_score
        alert.severity = severity
        alert.save()
        
        return risk_score, severity
        
    except Exception as e:
        logger.error(f"Error updating alert risk: {str(e)}")
        return None, None

def calculate_asset_risk(asset_data):
    """Calculate risk score for an asset based on its attributes"""
    base_score = 0
    
    # Asset type risk
    type_scores = {
        'server': 8,
        'workstation': 5,
        'network_device': 7,
        'iot_device': 6,
        'mobile_device': 4
    }
    base_score += type_scores.get(asset_data.get('type', '').lower(), 3)
    
    # Location risk
    if asset_data.get('location', '').lower() in ['dmz', 'external']:
        base_score += 3
    
    # Normalize score to 0-100 range
    normalized_score = min(100, max(0, base_score * 10))
    
    return normalized_score

def get_risk_factors():
    """Return a dictionary of risk factors and their weights."""
    return {
        'severity': {
            'critical': 1.0,
            'high': 0.8,
            'medium': 0.5,
            'low': 0.2,
            'info': 0.1
        },
        'confidence': {
            'high': 1.0,
            'medium': 0.6,
            'low': 0.3
        },
        'threat_type': {
            'malware': 1.0,
            'phishing': 0.9,
            'brute_force': 0.8,
            'data_exfiltration': 0.95,
            'unauthorized_access': 0.85,
            'suspicious_activity': 0.7
        }
    }
