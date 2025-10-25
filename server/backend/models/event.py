from datetime import datetime
from backend.db import db

class Event(db.Model):
    __tablename__ = 'events'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), nullable=False)
    source_ip = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    severity = db.Column(db.String(20), default='medium')
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type,
            'source_ip': self.source_ip,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'severity': self.severity
        }