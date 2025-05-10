"""
Risk assessment service for evaluating security events and calculating risk scores
"""
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class RiskFactor:
    name: str
    weight: float
    description: str
    threshold: float

class RiskAssessment:
    def __init__(self):
        """Initialize risk assessment service"""
        self.risk_factors = {
            "anomaly_score": RiskFactor(
                name="Anomaly Score",
                weight=0.3,
                description="Score from anomaly detection model",
                threshold=0.7
            ),
            "event_frequency": RiskFactor(
                name="Event Frequency",
                weight=0.2,
                description="Number of events in time window",
                threshold=10
            ),
            "severity": RiskFactor(
                name="Event Severity",
                weight=0.25,
                description="Severity level of events",
                threshold=0.8
            ),
            "asset_criticality": RiskFactor(
                name="Asset Criticality",
                weight=0.15,
                description="Criticality of affected assets",
                threshold=0.7
            ),
            "user_risk": RiskFactor(
                name="User Risk",
                weight=0.1,
                description="Risk level of involved users",
                threshold=0.6
            )
        }
        
        # Initialize risk thresholds
        self.risk_thresholds = {
            RiskLevel.LOW: 0.3,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.7,
            RiskLevel.CRITICAL: 0.9
        }

    def calculate_risk_score(self, 
                           events: List[Dict[str, Any]],
                           asset_info: Optional[Dict[str, Any]] = None,
                           user_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculate risk score based on events and context
        
        Args:
            events: List of security events
            asset_info: Information about affected assets
            user_info: Information about involved users
            
        Returns:
            Dictionary containing risk score and factors
        """
        try:
            # Calculate individual factor scores
            factor_scores = {}
            
            # Anomaly score
            anomaly_scores = [e.get('anomaly_score', 0) for e in events]
            factor_scores['anomaly_score'] = np.mean(anomaly_scores) if anomaly_scores else 0
            
            # Event frequency
            time_window = timedelta(hours=24)
            recent_events = [
                e for e in events 
                if datetime.fromisoformat(e['timestamp']) > datetime.utcnow() - time_window
            ]
            factor_scores['event_frequency'] = min(len(recent_events) / self.risk_factors['event_frequency'].threshold, 1.0)
            
            # Event severity
            severity_map = {'low': 0.3, 'medium': 0.6, 'high': 0.8, 'critical': 1.0}
            severity_scores = [severity_map.get(e.get('severity', 'low'), 0.3) for e in events]
            factor_scores['severity'] = np.mean(severity_scores) if severity_scores else 0
            
            # Asset criticality
            if asset_info:
                factor_scores['asset_criticality'] = asset_info.get('criticality_score', 0)
            else:
                factor_scores['asset_criticality'] = 0.5  # Default medium criticality
                
            # User risk
            if user_info:
                factor_scores['user_risk'] = user_info.get('risk_score', 0)
            else:
                factor_scores['user_risk'] = 0.3  # Default low risk
                
            # Calculate weighted risk score
            risk_score = sum(
                factor_scores[factor] * self.risk_factors[factor].weight
                for factor in self.risk_factors
            )
            
            # Determine risk level
            risk_level = self._get_risk_level(risk_score)
            
            return {
                "risk_score": float(risk_score),
                "risk_level": risk_level.value,
                "factors": {
                    factor: {
                        "score": float(factor_scores[factor]),
                        "weight": self.risk_factors[factor].weight,
                        "description": self.risk_factors[factor].description
                    }
                    for factor in self.risk_factors
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {str(e)}")
            return {
                "risk_score": 0.0,
                "risk_level": RiskLevel.LOW.value,
                "error": str(e)
            }

    def _get_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level based on score"""
        if risk_score >= self.risk_thresholds[RiskLevel.CRITICAL]:
            return RiskLevel.CRITICAL
        elif risk_score >= self.risk_thresholds[RiskLevel.HIGH]:
            return RiskLevel.HIGH
        elif risk_score >= self.risk_thresholds[RiskLevel.MEDIUM]:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def update_risk_factors(self, 
                          factor_updates: Dict[str, Dict[str, Any]]) -> bool:
        """
        Update risk factor weights and thresholds
        
        Args:
            factor_updates: Dictionary of factor updates
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            for factor, updates in factor_updates.items():
                if factor in self.risk_factors:
                    if 'weight' in updates:
                        self.risk_factors[factor].weight = float(updates['weight'])
                    if 'threshold' in updates:
                        self.risk_factors[factor].threshold = float(updates['threshold'])
                    if 'description' in updates:
                        self.risk_factors[factor].description = updates['description']
            return True
        except Exception as e:
            logger.error(f"Error updating risk factors: {str(e)}")
            return False

    def update_risk_thresholds(self, 
                             threshold_updates: Dict[str, float]) -> bool:
        """
        Update risk level thresholds
        
        Args:
            threshold_updates: Dictionary of threshold updates
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            for level, threshold in threshold_updates.items():
                if level in self.risk_thresholds:
                    self.risk_thresholds[level] = float(threshold)
            return True
        except Exception as e:
            logger.error(f"Error updating risk thresholds: {str(e)}")
            return False

    def get_risk_factors(self) -> Dict[str, Dict[str, Any]]:
        """Get current risk factors configuration"""
        return {
            factor: {
                "weight": self.risk_factors[factor].weight,
                "threshold": self.risk_factors[factor].threshold,
                "description": self.risk_factors[factor].description
            }
            for factor in self.risk_factors
        }

    def get_risk_thresholds(self) -> Dict[str, float]:
        """Get current risk level thresholds"""
        return {
            level.value: threshold
            for level, threshold in self.risk_thresholds.items()
        }

    def analyze_trends(self, 
                      risk_scores: List[Dict[str, Any]],
                      window: int = 24) -> Dict[str, Any]:
        """
        Analyze risk score trends
        
        Args:
            risk_scores: List of historical risk scores
            window: Time window in hours
            
        Returns:
            Dictionary containing trend analysis
        """
        try:
            # Convert timestamps to datetime objects
            scores_with_time = [
                (datetime.fromisoformat(score['timestamp']), score['risk_score'])
                for score in risk_scores
            ]
            
            # Sort by timestamp
            scores_with_time.sort(key=lambda x: x[0])
            
            # Get scores within window
            cutoff_time = datetime.utcnow() - timedelta(hours=window)
            recent_scores = [score for time, score in scores_with_time if time > cutoff_time]
            
            if not recent_scores:
                return {
                    "trend": "stable",
                    "change": 0.0,
                    "volatility": 0.0,
                    "max_score": 0.0,
                    "min_score": 0.0,
                    "avg_score": 0.0
                }
            
            # Calculate trend metrics
            change = recent_scores[-1] - recent_scores[0]
            volatility = np.std(recent_scores)
            max_score = max(recent_scores)
            min_score = min(recent_scores)
            avg_score = np.mean(recent_scores)
            
            # Determine trend
            if abs(change) < 0.1:
                trend = "stable"
            elif change > 0:
                trend = "increasing"
            else:
                trend = "decreasing"
            
            return {
                "trend": trend,
                "change": float(change),
                "volatility": float(volatility),
                "max_score": float(max_score),
                "min_score": float(min_score),
                "avg_score": float(avg_score)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {str(e)}")
            return {
                "trend": "unknown",
                "error": str(e)
            } 