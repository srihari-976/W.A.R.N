import threading
import time
import random
from datetime import datetime, timedelta
from backend.models.security_event import SecurityEvent, BlockedIP, LockedAccount
from backend.models.alert import Alert
from backend.db import db
import logging

logger = logging.getLogger(__name__)

class SecurityMonitor:
    def __init__(self):
        self.running = False
        self.thread = None
        self.app = None
        
    def start_monitoring(self, app=None):
        """Start real-time security monitoring"""
        if app:
            self.app = app
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()
            logger.info("Security monitoring started")
    
    def stop_monitoring(self):
        """Stop security monitoring"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Security monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                if self.app:
                    with self.app.app_context():
                        # Simulate random security events
                        if random.random() < 0.3:  # 30% chance every 10 seconds
                            self._generate_random_event()
                        
                        # Check for brute force patterns
                        self._check_brute_force_patterns()
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in security monitoring: {e}")
                time.sleep(5)
    
    def _generate_random_event(self):
        """Generate random security event"""
        try:
            event_types = ['brute_force', 'dos_attack', 'phishing', 'malware']
            ips = ['192.168.1.101', '10.0.0.51', '172.16.0.26', '203.0.113.46']
            
            event_type = random.choice(event_types)
            source_ip = random.choice(ips)
            
            if event_type == 'brute_force':
                event = SecurityEvent(
                    event_type='brute_force',
                    source_ip=source_ip,
                    username=random.choice(['admin', 'user', 'test']),
                    severity='medium',
                    attempts=random.randint(1, 5),
                    description='Real-time brute force attempt detected'
                )
                
                # Auto-block after 3 attempts
                existing_attempts = SecurityEvent.query.filter_by(
                    source_ip=source_ip,
                    event_type='brute_force'
                ).count()
                
                if existing_attempts >= 3:
                    self._block_ip(source_ip, 'Brute force attack', existing_attempts)
                    
            elif event_type == 'dos_attack':
                event = SecurityEvent(
                    event_type='dos_attack',
                    source_ip=source_ip,
                    severity='high',
                    attempts=random.randint(50, 200),
                    description='DoS attack detected in real-time'
                )
                
            else:
                event = SecurityEvent(
                    event_type=event_type,
                    source_ip=source_ip,
                    severity=random.choice(['medium', 'high']),
                    description=f'Real-time {event_type} detected'
                )
            
            db.session.add(event)
            db.session.commit()
            
            logger.info(f"Generated security event: {event_type} from {source_ip}")
            
        except Exception as e:
            logger.error(f"Error generating security event: {e}")
            db.session.rollback()
    
    def _check_brute_force_patterns(self):
        """Check for brute force attack patterns"""
        try:
            # Get recent brute force attempts (last hour)
            recent_time = datetime.utcnow() - timedelta(hours=1)
            
            # Group by IP and count attempts
            from sqlalchemy import func
            ip_attempts = db.session.query(
                SecurityEvent.source_ip,
                func.count(SecurityEvent.id).label('attempt_count')
            ).filter(
                SecurityEvent.event_type == 'brute_force',
                SecurityEvent.timestamp > recent_time
            ).group_by(SecurityEvent.source_ip).all()
            
            for ip, count in ip_attempts:
                if count >= 5:  # Block after 5 attempts in an hour
                    existing_block = BlockedIP.query.filter_by(address=ip).first()
                    if not existing_block:
                        self._block_ip(ip, 'Automated brute force detection', count)
                        
        except Exception as e:
            logger.error(f"Error checking brute force patterns: {e}")
    
    def _block_ip(self, ip_address, reason, attempts):
        """Block an IP address"""
        try:
            blocked_ip = BlockedIP(
                address=ip_address,
                reason=reason,
                attempts=attempts
            )
            db.session.add(blocked_ip)
            
            # Create alert
            alert = Alert(
                alert_type='ip_blocked',
                severity='high',
                status='new',
                source='security_monitor',
                description=f'IP {ip_address} blocked: {reason}',
                risk_score=80,
                threat_level='high'
            )
            db.session.add(alert)
            
            db.session.commit()
            logger.info(f"Blocked IP: {ip_address} - {reason}")
            
        except Exception as e:
            logger.error(f"Error blocking IP {ip_address}: {e}")
            db.session.rollback()

# Global monitor instance
security_monitor = SecurityMonitor()