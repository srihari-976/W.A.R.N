from app import create_app, db
from models.user import User
from models.alert import Alert
from models.asset import Asset
from models.event import SecurityEvent
from datetime import datetime, timedelta
import random

app = create_app()

def generate_test_data():
    with app.app_context():
        # Create test user
        test_user = User(
            username='test_user',
            email='test@example.com',
            role='admin'
        )
        test_user.set_password('test123')
        db.session.add(test_user)
        
        # Create test assets
        assets = [
            Asset(name='Web Server', type='server', status='active'),
            Asset(name='Database Server', type='server', status='active'),
            Asset(name='Firewall', type='network', status='active')
        ]
        db.session.add_all(assets)
        
        # Create test alerts
        alert_types = ['Intrusion', 'Malware', 'Unauthorized Access']
        severities = ['high', 'medium', 'low']
        
        for i in range(10):
            alert = Alert(
                type=random.choice(alert_types),
                severity=random.choice(severities),
                description=f'Test alert {i+1}',
                timestamp=datetime.utcnow() - timedelta(hours=random.randint(1, 24)),
                status='new'
            )
            db.session.add(alert)
        
        # Create test events
        event_types = ['login', 'file_access', 'network_connection']
        
        for i in range(20):
            event = SecurityEvent(
                type=random.choice(event_types),
                source_ip=f'192.168.1.{random.randint(1, 255)}',
                timestamp=datetime.utcnow() - timedelta(minutes=random.randint(1, 60)),
                details=f'Test event {i+1}'
            )
            db.session.add(event)
        
        db.session.commit()
        print("Test data generated successfully!")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        generate_test_data()
    
    app.run(debug=True, port=5000) 