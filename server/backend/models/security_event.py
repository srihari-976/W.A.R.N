from datetime import datetime
from backend.db import db

class SecurityEvent(db.Model):
    __tablename__ = 'security_events'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), nullable=False)  # dos, brute_force, phishing, malware
    source_ip = db.Column(db.String(45), nullable=False)
    target_ip = db.Column(db.String(45), nullable=True)
    username = db.Column(db.String(100), nullable=True)
    url = db.Column(db.Text, nullable=True)
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    status = db.Column(db.String(20), default='active')  # active, blocked, resolved
    attempts = db.Column(db.Integer, default=1)
    description = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type,
            'source_ip': self.source_ip,
            'target_ip': self.target_ip,
            'username': self.username,
            'url': self.url,
            'severity': self.severity,
            'status': self.status,
            'attempts': self.attempts,
            'description': self.description,
            'timestamp': self.timestamp.isoformat()
        }

    # Persistence helpers to align with API usage
    def save(self):
        db.session.add(self)
        db.session.commit()

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def get_by_id(event_id):
        return SecurityEvent.query.get(event_id)

    @staticmethod
    def get_all(filters=None, page=1, per_page=20):
        query = SecurityEvent.query
        if filters:
            if 'event_type' in filters:
                query = query.filter_by(event_type=filters['event_type'])
            if 'severity' in filters:
                query = query.filter_by(severity=filters['severity'])
            if 'status' in filters:
                query = query.filter_by(status=filters['status'])
        total = query.count()
        items = query.order_by(SecurityEvent.timestamp.desc()).paginate(page=page, per_page=per_page)
        return items.items, total

class BlockedIP(db.Model):
    __tablename__ = 'blocked_ips'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(45), unique=True, nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    attempts = db.Column(db.Integer, default=0)
    blocked_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'address': self.address,
            'reason': self.reason,
            'attempts': self.attempts,
            'blocked_at': self.blocked_at.isoformat()
        }

class LockedAccount(db.Model):
    __tablename__ = 'locked_accounts'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    locked_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'username': self.username,
            'reason': self.reason,
            'locked_at': self.locked_at.isoformat()
        }