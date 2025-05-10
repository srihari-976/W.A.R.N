from datetime import datetime
from backend.db import db, Column, Integer, String, Float, DateTime, ForeignKey, Text, relationship, backref

class Alert(db.Model):
    """Alert model for security alerts"""
    __tablename__ = 'alerts'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    description = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    status = Column(String(20), nullable=False, default='new')
    risk_score = Column(Float)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    asset_id = Column(Integer, ForeignKey('assets.id'))
    created_by_id = Column(Integer, ForeignKey('users.id'))
    assigned_to_id = Column(Integer, ForeignKey('users.id'))
    event_id = Column(Integer, ForeignKey('security_events.id'))
    
    # Relationships
    asset = relationship('Asset', backref=backref('alerts', lazy=True))
    created_by = relationship('User', foreign_keys=[created_by_id], backref=backref('created_alerts', lazy=True))
    assigned_to = relationship('User', foreign_keys=[assigned_to_id], backref=backref('assigned_alerts', lazy=True))
    event = relationship('SecurityEvent', backref='alerts')
    responses = relationship('Response', backref='alert', lazy=True)
    
    def __init__(self, type, severity, description, asset_id=None, created_by_id=None):
        self.type = type
        self.severity = severity
        self.description = description
        self.asset_id = asset_id
        self.created_by_id = created_by_id
        self.status = 'new'
        self.risk_score = 0.0
        
    def to_dict(self):
        """Convert alert to dictionary"""
        return {
            'id': self.id,
            'type': self.type,
            'severity': self.severity,
            'description': self.description,
            'status': self.status,
            'risk_score': self.risk_score,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'asset_id': self.asset_id,
            'created_by_id': self.created_by_id,
            'assigned_to_id': self.assigned_to_id,
            'event_id': self.event_id,
            'responses': [response.to_dict() for response in self.responses]
        }
        
    def save(self):
        """Save alert to database"""
        db.session.add(self)
        db.session.commit()
        
    def update(self, **kwargs):
        """Update alert attributes"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        db.session.commit()
        
    def delete(self):
        """Delete alert from database"""
        db.session.delete(self)
        db.session.commit()
        
    @staticmethod
    def get_by_id(alert_id):
        """Get alert by ID"""
        return Alert.query.get(alert_id)
        
    @staticmethod
    def get_all(filters=None, page=1, per_page=20):
        """
        Get all alerts with optional filtering
        
        Args:
            filters (dict): Dictionary of filters
            page (int): Page number
            per_page (int): Items per page
            
        Returns:
            tuple: (alerts, total)
        """
        query = Alert.query
        
        if filters:
            if 'type' in filters:
                query = query.filter_by(type=filters['type'])
            if 'severity' in filters:
                query = query.filter_by(severity=filters['severity'])
            if 'status' in filters:
                query = query.filter_by(status=filters['status'])
            if 'asset_id' in filters:
                query = query.filter_by(asset_id=filters['asset_id'])
            if 'created_by_id' in filters:
                query = query.filter_by(created_by_id=filters['created_by_id'])
            if 'assigned_to_id' in filters:
                query = query.filter_by(assigned_to_id=filters['assigned_to_id'])
            if 'start_date' in filters:
                query = query.filter(Alert.created_at >= filters['start_date'])
            if 'end_date' in filters:
                query = query.filter(Alert.created_at <= filters['end_date'])
                
        total = query.count()
        alerts = query.order_by(Alert.created_at.desc()).paginate(page=page, per_page=per_page)
        
        return alerts.items, total
