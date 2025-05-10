from datetime import datetime
from backend.db import db, Column, Integer, String, DateTime, JSON, ForeignKey, relationship
import json

class SecurityEvent(db.Model):
    """Security event model"""
    __tablename__ = 'security_events'
    
    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)
    source_ip = Column(String(50), nullable=False)
    details = Column(db.Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    severity = Column(String(20), nullable=False, default='medium')
    status = Column(String(20), nullable=False, default='new')
    
    # Foreign keys
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=True)
    
    # Relationships
    asset = relationship('Asset', back_populates='events')
    
    def __repr__(self):
        return f'<SecurityEvent {self.id}: {self.type}>'
        
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'source_ip': self.source_ip,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'severity': self.severity,
            'status': self.status
        }
        
    def save(self):
        """Save event to database"""
        db.session.add(self)
        db.session.commit()
        
    def update(self, **kwargs):
        """Update event attributes"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()
        
    def delete(self):
        """Delete event from database"""
        db.session.delete(self)
        db.session.commit()
        
    @staticmethod
    def get_by_id(event_id):
        """Get event by ID"""
        return SecurityEvent.query.get(event_id)
        
    @staticmethod
    def get_all(filters=None, page=1, per_page=20):
        """
        Get all events with optional filtering
        
        Args:
            filters (dict): Dictionary of filters
            page (int): Page number
            per_page (int): Items per page
            
        Returns:
            tuple: (events, total)
        """
        query = SecurityEvent.query
        
        if filters:
            if 'type' in filters:
                query = query.filter_by(type=filters['type'])
            if 'source_ip' in filters:
                query = query.filter_by(source_ip=filters['source_ip'])
            if 'asset_id' in filters:
                query = query.filter_by(asset_id=filters['asset_id'])
            if 'start_date' in filters:
                query = query.filter(SecurityEvent.timestamp >= filters['start_date'])
            if 'end_date' in filters:
                query = query.filter(SecurityEvent.timestamp <= filters['end_date'])
                
        total = query.count()
        events = query.order_by(SecurityEvent.timestamp.desc()).paginate(page=page, per_page=per_page)
        
        return events.items, total
        
    @staticmethod
    def get_anomalies(filters=None, page=1, per_page=20):
        """
        Get all anomalous events with optional filtering
        
        Args:
            filters (dict): Dictionary of filters
            page (int): Page number
            per_page (int): Items per page
            
        Returns:
            tuple: (events, total)
        """
        query = SecurityEvent.query.filter_by(is_anomaly=True)
        
        if filters:
            if 'type' in filters:
                query = query.filter_by(type=filters['type'])
            if 'source_ip' in filters:
                query = query.filter_by(source_ip=filters['source_ip'])
            if 'asset_id' in filters:
                query = query.filter_by(asset_id=filters['asset_id'])
            if 'start_date' in filters:
                query = query.filter(SecurityEvent.timestamp >= filters['start_date'])
            if 'end_date' in filters:
                query = query.filter(SecurityEvent.timestamp <= filters['end_date'])
                
        total = query.count()
        events = query.order_by(SecurityEvent.anomaly_score.desc()).paginate(page=page, per_page=per_page)
        
        return events.items, total

# Alias SecurityEvent as Event for backward compatibility
Event = SecurityEvent