import pytest
from app import create_app, db
from models.user import User
from models.alert import Alert
from models.asset import Asset
from models.event import SecurityEvent

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(client):
    # Create test user
    user = User(username='test_user', email='test@example.com', role='admin')
    user.set_password('test123')
    db.session.add(user)
    db.session.commit()
    
    # Login to get token
    response = client.post('/api/auth/login', json={
        'username': 'test_user',
        'password': 'test123'
    })
    token = response.json['access_token']
    return {'Authorization': f'Bearer {token}'}

def test_login(client):
    # Create test user
    user = User(username='test_user', email='test@example.com', role='admin')
    user.set_password('test123')
    db.session.add(user)
    db.session.commit()
    
    # Test login
    response = client.post('/api/auth/login', json={
        'username': 'test_user',
        'password': 'test123'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json

def test_get_alerts(client, auth_headers):
    # Create test alert
    alert = Alert(
        type='Test Alert',
        severity='high',
        description='Test alert description'
    )
    db.session.add(alert)
    db.session.commit()
    
    # Test getting alerts
    response = client.get('/api/alerts', headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['type'] == 'Test Alert'

def test_get_assets(client, auth_headers):
    # Create test asset
    asset = Asset(
        name='Test Server',
        type='server',
        status='active'
    )
    db.session.add(asset)
    db.session.commit()
    
    # Test getting assets
    response = client.get('/api/assets', headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['name'] == 'Test Server'

def test_get_events(client, auth_headers):
    # Create test event
    event = SecurityEvent(
        type='test_event',
        source_ip='192.168.1.1',
        details='Test event details'
    )
    db.session.add(event)
    db.session.commit()
    
    # Test getting events
    response = client.get('/api/events', headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['type'] == 'test_event' 