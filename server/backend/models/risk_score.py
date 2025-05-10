from datetime import datetime
from backend.db import db

class RiskScore(db.Model):
    """RiskScore model for risk assessments"""
    __tablename__ = 'risk_scores'
    
    id = db.Column(db.String(36), primary_key=True)
    score = db.Column(db.Float, nullable=False)  # 0-100 scale
    category = db.Column(db.String(20), nullable=False)  # low, medium, high
    factors = db.Column(db.JSON, nullable=True)  # Factors contributing to score
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships - can be associated with an asset, event, or both
    asset_id = db.Column(db.String(36), db.ForeignKey('assets.id'), nullable=True)
    event_id = db.Column(db.String(36), db.ForeignKey('security_events.id'), nullable=True)
    
    def __init__(self, score, category, factors=None, asset_id=None, event_id=None, timestamp=None):
        import uuid
        self.id = str(uuid.uuid4())
        self.score = score
        self.category = category
        self.factors = factors or {}
        self.asset_id = asset_id
        self.event_id = event_id
        self.timestamp = timestamp or datetime.utcnow()
    
    def to_dict(self):
        """Convert risk score to dictionary"""
        return {
            'id': self.id,
            'score': self.score,
            'category': self.category,
            'factors': self.factors,
            'timestamp': self.timestamp.isoformat(),
            'created_at': self.created_at.isoformat(),
            'asset_id': self.asset_id,
            'event_id': self.event_id
        }
    
    def save(self):
        """Save risk score to database"""
        db.session.add(self)
        db.session.commit()
        return self
    
    def update(self, **kwargs):
        """Update risk score attributes"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()
        return self
    
    def delete(self):
        """Delete risk score from database"""
        db.session.delete(self)
        db.session.commit()