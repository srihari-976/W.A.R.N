from datetime import datetime
from backend.db import db

class RiskScore(db.Model):
    __tablename__ = 'risk_scores'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=True)
    score = db.Column(db.Float, nullable=False)
    factors = db.Column(db.JSON, nullable=True)
    category = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    asset = db.relationship('Asset', backref='risk_scores')
    event = db.relationship('Event', backref='risk_scores')
    
    def to_dict(self):
        return {
            'id': self.id,
            'asset_id': self.asset_id,
            'event_id': self.event_id,
            'score': self.score,
            'factors': self.factors,
            'category': self.category,
            'timestamp': self.timestamp.isoformat()
        }
    
    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

def calculate_risk_score(asset=None, event=None, threat_info=None, context=None):
    """Calculate risk score based on inputs"""
    base_score = 0.5
    
    if event and hasattr(event, 'severity'):
        severity_map = {'low': 0.2, 'medium': 0.5, 'high': 0.8, 'critical': 1.0}
        base_score = severity_map.get(event.severity, 0.5)
    
    if threat_info:
        base_score += threat_info.get('threat_level', 0) * 0.3
    
    score = min(base_score, 1.0)
    category = 'high' if score >= 0.7 else 'medium' if score >= 0.4 else 'low'
    
    return {
        'score': score,
        'category': category,
        'factors': {'base_score': base_score},
        'timestamp': datetime.utcnow()
    }