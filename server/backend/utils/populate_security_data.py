from datetime import datetime, timedelta
from backend.models.security_event import SecurityEvent, BlockedIP, LockedAccount
from backend.models.alert import Alert
from backend.db import db
import random

def populate_sample_data():
    """Populate database with sample security data from 12-05-2025"""
    
    # Base date: 12-05-2025
    base_date = datetime(2025, 5, 12)
    
    # Sample IPs and usernames
    malicious_ips = ['192.168.1.100', '10.0.0.50', '172.16.0.25', '203.0.113.45']
    usernames = ['admin', 'user1', 'test', 'administrator', 'root']
    phishing_urls = [
        'http://phishing-bank.com/login',
        'https://fake-paypal.net/verify',
        'http://suspicious-amazon.org/account',
        'https://malicious-microsoft.co/signin'
    ]
    
    # Clear existing data
    SecurityEvent.query.delete()
    BlockedIP.query.delete()
    LockedAccount.query.delete()
    
    # Generate security events
    events = []
    
    # DoS Attacks
    for i in range(15):
        event = SecurityEvent(
            event_type='dos_attack',
            source_ip=random.choice(malicious_ips),
            target_ip='192.168.1.1',
            severity=random.choice(['high', 'critical']),
            status='blocked',
            attempts=random.randint(100, 1000),
            description=f'DoS attack detected - {random.randint(100, 1000)} requests/sec',
            timestamp=base_date + timedelta(hours=random.randint(0, 72))
        )
        events.append(event)
    
    # Brute Force Attacks
    for i in range(25):
        ip = random.choice(malicious_ips)
        user = random.choice(usernames)
        attempts = random.randint(3, 50)
        
        event = SecurityEvent(
            event_type='brute_force',
            source_ip=ip,
            username=user,
            severity='high' if attempts > 10 else 'medium',
            status='blocked' if attempts > 5 else 'active',
            attempts=attempts,
            description=f'Brute force login attempts for user {user}',
            timestamp=base_date + timedelta(hours=random.randint(0, 72))
        )
        events.append(event)
    
    # Phishing Attempts
    for i in range(12):
        event = SecurityEvent(
            event_type='phishing',
            source_ip=random.choice(malicious_ips),
            url=random.choice(phishing_urls),
            severity=random.choice(['medium', 'high']),
            status='detected',
            description='Phishing URL detected and blocked',
            timestamp=base_date + timedelta(hours=random.randint(0, 72))
        )
        events.append(event)
    
    # Malware Detection
    for i in range(8):
        event = SecurityEvent(
            event_type='malware',
            source_ip=random.choice(malicious_ips),
            severity='critical',
            status='quarantined',
            description=f'Malware detected: Trojan.{random.choice(["Win32", "Generic", "Backdoor"])}',
            timestamp=base_date + timedelta(hours=random.randint(0, 72))
        )
        events.append(event)
    
    # Add all events
    for event in events:
        db.session.add(event)
    
    # Add blocked IPs
    blocked_ips = [
        BlockedIP(address='192.168.1.100', reason='Brute force attack', attempts=25),
        BlockedIP(address='10.0.0.50', reason='DoS attack', attempts=500),
        BlockedIP(address='203.0.113.45', reason='Malware distribution', attempts=12)
    ]
    
    for ip in blocked_ips:
        db.session.add(ip)
    
    # Add locked accounts
    locked_accounts = [
        LockedAccount(username='admin', reason='Multiple failed login attempts'),
        LockedAccount(username='test', reason='Suspicious activity detected')
    ]
    
    for account in locked_accounts:
        db.session.add(account)
    
    # Create corresponding alerts
    alerts = [
        Alert(
            type='brute_force_detected',
            severity='high',
            description='Multiple brute force attempts detected',
            status='new',
            source='security_monitor',
            risk_score=85,
            threat_level='high',
            techniques='["T1110"]'
        ),
        Alert(
            type='dos_attack',
            severity='critical', 
            description='DoS attack in progress',
            status='active',
            source='network_monitor',
            risk_score=95,
            threat_level='critical',
            techniques='["T1499"]'
        ),
        Alert(
            type='phishing_detected',
            severity='medium',
            description='Phishing URL blocked',
            status='resolved',
            source='url_scanner',
            risk_score=65,
            threat_level='medium',
            techniques='["T1566"]'
        )
    ]
    
    for alert in alerts:
        db.session.add(alert)
    
    try:
        db.session.commit()
        print(f"✅ Sample security data populated successfully!")
        print(f"   - {len(events)} security events")
        print(f"   - {len(blocked_ips)} blocked IPs") 
        print(f"   - {len(locked_accounts)} locked accounts")
        print(f"   - {len(alerts)} alerts")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error populating data: {e}")

if __name__ == '__main__':
    populate_sample_data()