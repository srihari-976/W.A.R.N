from datetime import datetime
from backend.db import db, Column, Integer, String, DateTime, Text, ForeignKey, relationship
import json

class Response(db.Model):
    """Response model for alert responses"""
    __tablename__ = 'responses'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    action = Column(String(100), nullable=False)
    description = Column(Text)
    status = Column(String(20), nullable=False, default='pending')
    parameters = Column(db.JSON)
    result = Column(db.JSON)
    error = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    alert_id = Column(Integer, ForeignKey('alerts.id'))
    created_by_id = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    created_by = relationship('User', backref='responses')
    
    def __init__(self, action, description, alert_id, created_by_id, parameters=None):
        self.action = action
        self.description = description
        self.alert_id = alert_id
        self.created_by_id = created_by_id
        self.parameters = parameters or {}
        self.status = 'pending'
        self.result = None
        self.error = None
        
    def to_dict(self):
        """Convert response to dictionary"""
        return {
            'id': self.id,
            'action': self.action,
            'status': self.status,
            'parameters': self.parameters,
            'result': self.result,
            'error': self.error,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'alert_id': self.alert_id,
            'created_by_id': self.created_by_id
        }
        
    def save(self):
        """Save response to database"""
        db.session.add(self)
        db.session.commit()
        
    def update(self, **kwargs):
        """Update response attributes"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        db.session.commit()
        
    def delete(self):
        """Delete response from database"""
        db.session.delete(self)
        db.session.commit()
        
    @staticmethod
    def get_by_id(response_id):
        """Get response by ID"""
        return Response.query.get(response_id)
        
    @staticmethod
    def get_all(filters=None, page=1, per_page=20):
        """
        Get all responses with optional filtering
        
        Args:
            filters (dict): Dictionary of filters
            page (int): Page number
            per_page (int): Items per page
            
        Returns:
            tuple: (responses, total)
        """
        query = Response.query
        
        if filters:
            if 'action' in filters:
                query = query.filter_by(action=filters['action'])
            if 'status' in filters:
                query = query.filter_by(status=filters['status'])
            if 'alert_id' in filters:
                query = query.filter_by(alert_id=filters['alert_id'])
            if 'created_by_id' in filters:
                query = query.filter_by(created_by_id=filters['created_by_id'])
            if 'start_date' in filters:
                query = query.filter(Response.created_at >= filters['start_date'])
            if 'end_date' in filters:
                query = query.filter(Response.created_at <= filters['end_date'])
                
        total = query.count()
        responses = query.order_by(Response.created_at.desc()).paginate(page=page, per_page=per_page)
        
        return responses.items, total