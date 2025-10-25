import time
from collections import defaultdict
from typing import Dict

class BruteForceDetector:
    def __init__(self):
        self.failed_attempts_ip = defaultdict(list)
        self.failed_attempts_username = defaultdict(list)
        self.blocked_ips = {}
        self.locked_accounts = {}
        
        # Instagram-style thresholds
        self.MAX_ATTEMPTS = 3
        self.BLOCK_DURATION = 3600  # 1 hour
        self.ATTEMPT_WINDOW = 300   # 5 minutes
        
    async def record_failed_login(self, username: str, ip_address: str, password_attempt: str) -> Dict:
        """Record failed login and determine risk level"""
        timestamp = time.time()
        
        # Clean old attempts
        self._clean_old_attempts(timestamp)
        
        # Record attempt
        self.failed_attempts_ip[ip_address].append({
            'timestamp': timestamp,
            'username': username,
            'password': password_attempt
        })
        
        self.failed_attempts_username[username].append({
            'timestamp': timestamp,
            'ip': ip_address
        })
        
        # Count recent attempts
        ip_attempts = self._count_recent_attempts(self.failed_attempts_ip[ip_address], timestamp)
        user_attempts = self._count_recent_attempts(self.failed_attempts_username[username], timestamp)
        
        # Determine risk level and action
        risk_analysis = {
            'ip': ip_address,
            'username': username,
            'ip_attempts': ip_attempts,
            'user_attempts': user_attempts,
            'risk_level': 'low',
            'action': 'monitor',
            'is_blocked': False,
            'message': ''
        }
        
        # Risk level calculation
        if ip_attempts >= self.MAX_ATTEMPTS or user_attempts >= self.MAX_ATTEMPTS:
            # CRITICAL: Block and isolate
            risk_analysis['risk_level'] = 'critical'
            risk_analysis['action'] = 'block_and_isolate'
            risk_analysis['is_blocked'] = True
            
            # Block IP
            self.blocked_ips[ip_address] = {
                'blocked_at': timestamp,
                'reason': 'Brute force attempt detected',
                'attempts': ip_attempts
            }
            
            # Lock account
            self.locked_accounts[username] = {
                'locked_at': timestamp,
                'reason': 'Multiple failed login attempts',
                'unlock_required': True
            }
            
            risk_analysis['message'] = f'Account locked after {user_attempts} failed attempts. Browser will be terminated.'
            
        elif ip_attempts >= 2 or user_attempts >= 2:
            # MEDIUM: Require password change
            risk_analysis['risk_level'] = 'medium'
            risk_analysis['action'] = 'require_password_change'
            risk_analysis['message'] = 'Suspicious activity detected. Please change your password.'
            
        else:
            # LOW: Monitor and isolate
            risk_analysis['risk_level'] = 'low'
            risk_analysis['action'] = 'isolate_system'
            risk_analysis['message'] = 'Failed login attempt recorded. System isolated for monitoring.'
        
        return risk_analysis
    
    def _count_recent_attempts(self, attempts: list, current_time: float) -> int:
        """Count attempts within the time window"""
        return len([a for a in attempts if current_time - a['timestamp'] <= self.ATTEMPT_WINDOW])
    
    def _clean_old_attempts(self, current_time: float):
        """Remove attempts older than window"""
        cutoff_time = current_time - self.ATTEMPT_WINDOW
        
        for ip in list(self.failed_attempts_ip.keys()):
            self.failed_attempts_ip[ip] = [
                a for a in self.failed_attempts_ip[ip] 
                if a['timestamp'] > cutoff_time
            ]
            if not self.failed_attempts_ip[ip]:
                del self.failed_attempts_ip[ip]
        
        for username in list(self.failed_attempts_username.keys()):
            self.failed_attempts_username[username] = [
                a for a in self.failed_attempts_username[username]
                if a['timestamp'] > cutoff_time
            ]
            if not self.failed_attempts_username[username]:
                del self.failed_attempts_username[username]
    
    def is_ip_blocked(self, ip_address: str) -> Dict:
        """Check if IP is currently blocked"""
        if ip_address in self.blocked_ips:
            block_info = self.blocked_ips[ip_address]
            elapsed = time.time() - block_info['blocked_at']
            
            if elapsed < self.BLOCK_DURATION:
                return {
                    'is_blocked': True,
                    'reason': block_info['reason'],
                    'time_remaining': self.BLOCK_DURATION - elapsed,
                    'attempts': block_info['attempts']
                }
            else:
                del self.blocked_ips[ip_address]
        
        return {'is_blocked': False}
    
    def is_account_locked(self, username: str) -> Dict:
        """Check if account is locked"""
        if username in self.locked_accounts:
            lock_info = self.locked_accounts[username]
            return {
                'is_locked': True,
                'reason': lock_info['reason'],
                'unlock_required': lock_info['unlock_required']
            }
        
        return {'is_locked': False}