from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.models.alert import Alert
from backend.models.incident import Incident
from backend.models.rule import Rule
from backend.models.asset import Asset
from backend.models.user import User
from backend.schemas.alert import AlertCreate, AlertUpdate, AlertResponse
from backend.core.config import settings
from backend.utils.notification import send_notification
from backend.utils.logging import get_logger

logger = get_logger(__name__)

class AlertService:
    def __init__(self, db: Session):
        self.db = db

    def create_alert(self, alert_data: AlertCreate) -> Alert:
        """Create a new alert"""
        try:
            alert = Alert(
                title=alert_data.title,
                description=alert_data.description,
                severity=alert_data.severity,
                status=alert_data.status,
                source=alert_data.source,
                rule_id=alert_data.rule_id,
                asset_id=alert_data.asset_id,
                incident_id=alert_data.incident_id,
                created_at=datetime.utcnow()
            )
            self.db.add(alert)
            self.db.commit()
            self.db.refresh(alert)
            
            # Send notification for high severity alerts
            if alert.severity in ['high', 'critical']:
                send_notification(
                    title=f"High Severity Alert: {alert.title}",
                    message=alert.description,
                    severity=alert.severity
                )
            
            return alert
        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}")
            self.db.rollback()
            raise

    def get_alert(self, alert_id: int) -> Optional[Alert]:
        """Get alert by ID"""
        return self.db.query(Alert).filter(Alert.id == alert_id).first()

    def get_alerts(
        self,
        skip: int = 0,
        limit: int = 100,
        severity: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Alert]:
        """Get all alerts with optional filtering"""
        query = self.db.query(Alert)
        
        if severity:
            query = query.filter(Alert.severity == severity)
        if status:
            query = query.filter(Alert.status == status)
            
        return query.offset(skip).limit(limit).all()

    def update_alert(self, alert_id: int, alert_data: AlertUpdate) -> Optional[Alert]:
        """Update alert"""
        try:
            alert = self.get_alert(alert_id)
            if not alert:
                return None
                
            for field, value in alert_data.dict(exclude_unset=True).items():
                setattr(alert, field, value)
                
            alert.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(alert)
            return alert
        except Exception as e:
            logger.error(f"Error updating alert: {str(e)}")
            self.db.rollback()
            raise

    def delete_alert(self, alert_id: int) -> bool:
        """Delete alert"""
        try:
            alert = self.get_alert(alert_id)
            if not alert:
                return False
                
            self.db.delete(alert)
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting alert: {str(e)}")
            self.db.rollback()
            raise

    def get_alerts_by_asset(self, asset_id: int) -> List[Alert]:
        """Get all alerts for a specific asset"""
        return self.db.query(Alert).filter(Alert.asset_id == asset_id).all()

    def get_alerts_by_incident(self, incident_id: int) -> List[Alert]:
        """Get all alerts associated with an incident"""
        return self.db.query(Alert).filter(Alert.incident_id == incident_id).all()

    def get_alerts_by_rule(self, rule_id: int) -> List[Alert]:
        """Get all alerts triggered by a specific rule"""
        return self.db.query(Alert).filter(Alert.rule_id == rule_id).all()

    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts"""
        return self.db.query(Alert).filter(Alert.status != 'resolved').all()

    def get_high_severity_alerts(self) -> List[Alert]:
        """Get all high and critical severity alerts"""
        return self.db.query(Alert).filter(
            Alert.severity.in_(['high', 'critical'])
        ).all()

    def resolve_alert(self, alert_id: int, resolution_notes: str) -> Optional[Alert]:
        """Resolve an alert with resolution notes"""
        try:
            alert = self.get_alert(alert_id)
            if not alert:
                return None
                
            alert.status = 'resolved'
            alert.resolution_notes = resolution_notes
            alert.resolved_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(alert)
            return alert
        except Exception as e:
            logger.error(f"Error resolving alert: {str(e)}")
            self.db.rollback()
            raise

    def get_alert_statistics(self) -> dict:
        """Get alert statistics"""
        total_alerts = self.db.query(Alert).count()
        active_alerts = self.db.query(Alert).filter(Alert.status != 'resolved').count()
        high_severity = self.db.query(Alert).filter(Alert.severity.in_(['high', 'critical'])).count()
        
        return {
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'high_severity_alerts': high_severity,
            'resolved_alerts': total_alerts - active_alerts
        } 