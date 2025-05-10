import requests
import json
from datetime import datetime

BASE_URL = 'http://localhost:5000/api'

def test_auth():
    # Login
    login_data = {
        'username': 'test_user',
        'password': 'test123'
    }
    response = requests.post(f'{BASE_URL}/auth/login', json=login_data)
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    return headers

def test_alerts(headers):
    # Get all alerts
    response = requests.get(f'{BASE_URL}/alerts', headers=headers)
    print("\nAlerts:")
    print(json.dumps(response.json(), indent=2))
    
    # Create new alert
    new_alert = {
        'type': 'Test Alert',
        'severity': 'high',
        'description': 'Test alert from script',
        'timestamp': datetime.utcnow().isoformat()
    }
    response = requests.post(f'{BASE_URL}/alerts', json=new_alert, headers=headers)
    print("\nCreated Alert:")
    print(json.dumps(response.json(), indent=2))

def test_assets(headers):
    # Get all assets
    response = requests.get(f'{BASE_URL}/assets', headers=headers)
    print("\nAssets:")
    print(json.dumps(response.json(), indent=2))
    
    # Create new asset
    new_asset = {
        'name': 'Test Server',
        'type': 'server',
        'status': 'active'
    }
    response = requests.post(f'{BASE_URL}/assets', json=new_asset, headers=headers)
    print("\nCreated Asset:")
    print(json.dumps(response.json(), indent=2))

def test_events(headers):
    # Get recent events
    response = requests.get(f'{BASE_URL}/events', headers=headers)
    print("\nEvents:")
    print(json.dumps(response.json(), indent=2))
    
    # Create new event
    new_event = {
        'type': 'test_event',
        'source_ip': '192.168.1.100',
        'details': 'Test event from script'
    }
    response = requests.post(f'{BASE_URL}/events', json=new_event, headers=headers)
    print("\nCreated Event:")
    print(json.dumps(response.json(), indent=2))

if __name__ == '__main__':
    try:
        print("Testing API endpoints...")
        headers = test_auth()
        test_alerts(headers)
        test_assets(headers)
        test_events(headers)
        print("\nAll tests completed successfully!")
    except Exception as e:
        print(f"Error during testing: {str(e)}") 