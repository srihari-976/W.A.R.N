"""
Risk scoring service for W.A.R.N
Implements the risk assessment algorithm described in the paper
"""
import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class RiskScorer:
    """Risk scoring engine based on MITRE techniques and anomaly scores"""
    
    def __init__(self):
        # MITRE technique severity weights (based on CVSS-like scoring)
        self.technique_weights = {
            # Initial Access
            'T1566': 8.5,  # Phishing
            'T1190': 9.0,  # Exploit Public-Facing Application
            'T1078': 7.5,  # Valid Accounts
            
            # Execution
            'T1059': 8.0,  # Command and Scripting Interpreter
            'T1059.001': 8.5,  # PowerShell
            'T1059.003': 8.0,  # Windows Command Shell
            
            # Persistence
            'T1547': 7.0,  # Boot or Logon Autostart Execution
            'T1053': 6.5,  # Scheduled Task/Job
            
            # Privilege Escalation
            'T1068': 9.5,  # Exploitation for Privilege Escalation
            'T1055': 8.0,  # Process Injection
            
            # Defense Evasion
            'T1562': 8.5,  # Impair Defenses
            'T1070': 7.0,  # Indicator Removal on Host
            
            # Credential Access
            'T1110': 7.5,  # Brute Force
            'T1003': 9.0,  # OS Credential Dumping
            
            # Discovery
            'T1083': 5.0,  # File and Directory Discovery
            'T1057': 4.5,  # Process Discovery
            
            # Lateral Movement
            'T1021': 8.0,  # Remote Services
            'T1570': 7.5,  # Lateral Tool Transfer
            
            # Collection
            'T1114': 6.0,  # Email Collection
            'T1005': 5.5,  # Data from Local System
            
            # Command and Control
            'T1071': 7.0,  # Application Layer Protocol
            'T1573': 6.5,  # Encrypted Channel
            
            # Exfiltration
            'T1041': 8.5,  # Exfiltration Over C2 Channel
            'T1048': 8.0,  # Exfiltration Over Alternative Protocol
            
            # Impact
            'T1486': 9.5,  # Data Encrypted for Impact (Ransomware)
            'T1490': 9.0,  # Inhibit System Recovery
        }
        
        # Threat level multipliers
        self.threat_multipliers = {
            'low': 1.0,
            'medium': 1.5,
            'high': 2.0,
            'critical': 2.5
        }
    
    def calculate_risk(self, 
                      anomaly_score: float = 0.0,
                      techniques: List[str] = None,
                      threat_level: str = 'low',
                      event_context: Dict[str, Any] = None) -> float:
        """
        Calculate comprehensive risk score (0-100)
        
        Args:
            anomaly_score: Isolation Forest anomaly score
            techniques: List of MITRE ATT&CK technique IDs
            threat_level: Threat level from ML analysis
            event_context: Additional event context
            
        Returns:
            Risk score between 0-100
        """
        try:
            techniques = techniques or []
            event_context = event_context or {}
            
            # Base score from anomaly detection (0-30 points)
            anomaly_component = min(anomaly_score * 30, 30)
            
            # MITRE technique score (0-50 points)
            technique_component = self._calculate_technique_score(techniques)
            
            # Threat level multiplier (0-20 points)
            threat_component = self.threat_multipliers.get(threat_level, 1.0) * 8
            
            # Context-based adjustments (0-10 points)
            context_component = self._calculate_context_score(event_context)
            
            # Calculate final score
            raw_score = (anomaly_component + technique_component + 
                        threat_component + context_component)
            
            # Apply threat level multiplier
            multiplier = self.threat_multipliers.get(threat_level, 1.0)
            final_score = min(raw_score * multiplier, 100)
            
            logger.debug(f"Risk calculation: anomaly={anomaly_component:.1f}, "
                        f"techniques={technique_component:.1f}, "
                        f"threat={threat_component:.1f}, "
                        f"context={context_component:.1f}, "
                        f"final={final_score:.1f}")
            
            return round(final_score, 1)
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 50.0  # Default medium risk
    
    def _calculate_technique_score(self, techniques: List[str]) -> float:
        """Calculate score based on MITRE techniques"""
        if not techniques:
            return 0.0
        
        # Get weights for detected techniques
        technique_scores = []
        for technique in techniques:
            # Handle sub-techniques (e.g., T1059.001)
            base_technique = technique.split('.')[0]
            weight = self.technique_weights.get(technique, 
                    self.technique_weights.get(base_technique, 5.0))
            technique_scores.append(weight)
        
        # Calculate weighted average with diminishing returns
        if len(technique_scores) == 1:
            return min(technique_scores[0] * 5, 50)
        else:
            # Multiple techniques increase severity
            avg_score = sum(technique_scores) / len(technique_scores)
            multiplier = min(1 + (len(technique_scores) - 1) * 0.3, 2.0)
            return min(avg_score * 5 * multiplier, 50)
    
    def _calculate_context_score(self, context: Dict[str, Any]) -> float:
        """Calculate score based on event context"""
        score = 0.0
        
        # Time-based factors
        hour = context.get('hour', 12)
        if 0 <= hour <= 6 or 22 <= hour <= 23:  # Night time
            score += 2.0
        
        # Process-based factors
        process_name = context.get('process_name', '').lower()
        if any(proc in process_name for proc in ['powershell', 'cmd', 'wscript']):
            score += 2.0
        
        # Network-based factors
        external_connections = context.get('external_connections', 0)
        if external_connections > 0:
            score += min(external_connections * 1.5, 3.0)
        
        # File operation factors
        suspicious_files = context.get('suspicious_file_ops', 0)
        if suspicious_files > 0:
            score += min(suspicious_files * 1.0, 2.0)
        
        # User privilege factors
        if context.get('elevated_privileges', False):
            score += 1.0
        
        return min(score, 10.0)
    
    def get_risk_category(self, risk_score: float) -> str:
        """Convert risk score to category"""
        if risk_score >= 90:
            return 'critical'
        elif risk_score >= 70:
            return 'high'
        elif risk_score >= 40:
            return 'medium'
        else:
            return 'low'
    
    def get_recommendations(self, risk_score: float, 
                          techniques: List[str] = None) -> List[str]:
        """Get security recommendations based on risk assessment"""
        techniques = techniques or []
        recommendations = []
        
        if risk_score >= 90:
            recommendations.extend([
                "IMMEDIATE: Isolate affected systems",
                "IMMEDIATE: Block all network traffic from source",
                "Escalate to incident response team",
                "Preserve forensic evidence"
            ])
        elif risk_score >= 70:
            recommendations.extend([
                "Investigate source IP and user account",
                "Monitor for lateral movement",
                "Review recent system changes",
                "Consider temporary access restrictions"
            ])
        elif risk_score >= 40:
            recommendations.extend([
                "Monitor system for additional suspicious activity",
                "Review security logs for patterns",
                "Verify user account legitimacy"
            ])
        else:
            recommendations.append("Continue normal monitoring")
        
        # Technique-specific recommendations
        if 'T1059' in techniques:
            recommendations.append("Review PowerShell execution policies")
        if 'T1071' in techniques:
            recommendations.append("Analyze network traffic patterns")
        if 'T1547' in techniques:
            recommendations.append("Check startup programs and services")
        
        return recommendations
    
    def calculate_trend_score(self, recent_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate risk trend over time"""
        if not recent_events:
            return {'trend': 'stable', 'direction': 0, 'velocity': 0}
        
        # Calculate scores for recent events
        scores = []
        for event in recent_events:
            score = self.calculate_risk(
                anomaly_score=event.get('anomaly_score', 0),
                techniques=event.get('techniques', []),
                threat_level=event.get('threat_level', 'low')
            )
            scores.append(score)
        
        if len(scores) < 2:
            return {'trend': 'stable', 'direction': 0, 'velocity': 0}
        
        # Calculate trend
        recent_avg = sum(scores[-3:]) / min(len(scores), 3)
        older_avg = sum(scores[:-3]) / max(len(scores) - 3, 1) if len(scores) > 3 else recent_avg
        
        direction = recent_avg - older_avg
        velocity = abs(direction) / len(scores)
        
        if direction > 5:
            trend = 'increasing'
        elif direction < -5:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'direction': round(direction, 1),
            'velocity': round(velocity, 1),
            'current_avg': round(recent_avg, 1)
        }