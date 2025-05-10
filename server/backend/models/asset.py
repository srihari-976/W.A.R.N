# models/asset.py - Asset model
from datetime import datetime
from backend.db import db, Column, Integer, String, DateTime, Float, JSON, relationship, ForeignKey
import json

class Asset(db.Model):
    """Asset model for security assets"""
    __tablename__ = 'assets'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    ip_address = Column(String(50))
    status = Column(String(20), nullable=False, default='active')
    criticality = Column(String(20), nullable=False, default='medium')
    description = Column(String(200))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    owner_id = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    owner = relationship('User', backref='assets')
    events = relationship('SecurityEvent', back_populates='asset', lazy=True)
    
    def __repr__(self):
        return f'<Asset {self.id}: {self.name}>'
        
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'ip_address': self.ip_address,
            'status': self.status,
            'criticality': self.criticality,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __init__(self, name, type, ip_address=None, status=None, criticality=None, description=None):
        self.name = name
        self.type = type
        self.ip_address = ip_address
        self.status = status
        self.criticality = criticality
        self.description = description