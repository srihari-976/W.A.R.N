from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class BruteForceProtection:
    def __init__(self):
        self.login_attempts = {}  # ip -> list of attempts
        self.user_attempts = {}   # username -> list of attempts
        self.blocked_ips = {}
        self.blocked_users = {}
        self.max_attempts = 3
        self.block_duration = 3600  # 1 hour
    
    def record_failed_login(self, ip, username, app_name):
        """Record a failed login attempt"""
        now = datetime.utcnow()
        
        # Track by IP
        if ip not in self.login_attempts:
            self.login_attempts[ip] = []
        
        # Track by username
        if username not in self.user_attempts:
            self.user_attempts[username] = []
        
        # Clean old attempts (5 minute window)
        self.login_attempts[ip] = [
            attempt for attempt in self.login_attempts[ip]
            if now - attempt['timestamp'] < timedelta(minutes=5)
        ]
        
        self.user_attempts[username] = [
            attempt for attempt in self.user_attempts[username]
            if now - attempt['timestamp'] < timedelta(minutes=5)
        ]
        
        # Add new attempt
        attempt_data = {
            'timestamp': now,
            'username': username,
            'ip': ip,
            'app_name': app_name
        }
        
        self.login_attempts[ip].append(attempt_data)
        self.user_attempts[username].append(attempt_data)
        
        # Check if should block (either IP or username reaches limit)
        ip_attempts = len(self.login_attempts[ip])
        user_attempts = len(self.user_attempts[username])
        
        # Block IP after 3 attempts from any user on that IP
        if ip_attempts >= self.max_attempts:
            self.blocked_ips[ip] = {
                'blocked_at': now,
                'username': username,
                'app_name': app_name,
                'reason': f'IP blocked after {ip_attempts} attempts'
            }
            logger.warning(f"IP {ip} blocked after {ip_attempts} failed attempts")
            return True
            
        # Block specific user after 3 attempts
        if user_attempts >= self.max_attempts:
            self.blocked_users[username] = {
                'blocked_at': now,
                'ip': ip,
                'app_name': app_name,
                'reason': f'User blocked after {user_attempts} attempts'
            }
            logger.warning(f"User {username} blocked after {user_attempts} failed attempts")
            return True
        
        return False
    
    def is_ip_blocked(self, ip):
        """Check if IP is currently blocked"""
        if ip not in self.blocked_ips:
            return False
        
        blocked_at = self.blocked_ips[ip]['blocked_at']
        if datetime.utcnow() - blocked_at > timedelta(seconds=self.block_duration):
            del self.blocked_ips[ip]
            return False
        
        return True
    
    def is_user_blocked(self, username):
        """Check if username is currently blocked"""
        if username not in self.blocked_users:
            return False
        
        blocked_at = self.blocked_users[username]['blocked_at']
        if datetime.utcnow() - blocked_at > timedelta(seconds=self.block_duration):
            del self.blocked_users[username]
            return False
        
        return True
    
    def get_blocked_ips(self):
        """Get all currently blocked IPs"""
        current_blocked = {}
        now = datetime.utcnow()
        
        for ip, info in list(self.blocked_ips.items()):
            blocked_at = info['blocked_at']
            elapsed = now - blocked_at
            
            if elapsed < timedelta(seconds=self.block_duration):
                remaining = self.block_duration - elapsed.total_seconds()
                current_blocked[ip] = {
                    **info,
                    'remaining_seconds': int(remaining)
                }
            else:
                del self.blocked_ips[ip]
        
        return current_blocked

# Global instance
brute_force_protection = BruteForceProtection()