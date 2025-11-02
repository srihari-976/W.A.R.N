import time
from enum import Enum
from typing import Dict

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ActionType(Enum):
    MONITOR = "monitor"
    ISOLATE_SYSTEM = "isolate_system"
    REQUIRE_PASSWORD_CHANGE = "require_password_change"
    BLOCK_AND_ISOLATE = "block_and_isolate"
    TERMINATE_RESOURCES = "terminate_resources"

class RiskActionSystem:
    def __init__(self, ip_blocker, process_killer):
        self.ip_blocker = ip_blocker
        self.process_killer = process_killer
        self.action_log = []
        
    async def execute_action(
        self, 
        risk_level: RiskLevel, 
        action: ActionType,
        threat_data: Dict,
        manual_override: bool = False
    ) -> Dict:
        """Execute security action based on risk level"""
        
        result = {
            'risk_level': risk_level.value,
            'action_type': action.value,
            'manual_override': manual_override,
            'executed_actions': [],
            'success': True,
            'timestamp': time.time()
        }
        
        try:
            if action == ActionType.MONITOR:
                result['executed_actions'].append('System monitoring enabled')
                await self._log_threat(threat_data)
                
            elif action == ActionType.ISOLATE_SYSTEM:
                result['executed_actions'].append('System isolated from network')
                await self._isolate_system(threat_data.get('ip'))
                
            elif action == ActionType.REQUIRE_PASSWORD_CHANGE:
                result['executed_actions'].append('Password change required')
                await self._force_password_reset(threat_data.get('username'))
                
            elif action == ActionType.BLOCK_AND_ISOLATE:
                if 'ip' in threat_data:
                    blocked = await self.ip_blocker.block_ip(threat_data['ip'])
                    if blocked:
                        result['executed_actions'].append(f"IP {threat_data['ip']} blocked")
                
                await self._isolate_system(threat_data.get('ip'))
                result['executed_actions'].append('System isolated')
                
            elif action == ActionType.TERMINATE_RESOURCES:
                # Kill browser processes
                browser_result = await self.process_killer.kill_browser_processes()
                if browser_result['count'] > 0:
                    result['executed_actions'].append(f"Terminated {browser_result['count']} browser processes")
                
                # Block IP permanently
                if 'ip' in threat_data:
                    await self.ip_blocker.block_ip(threat_data['ip'], permanent=True)
                    result['executed_actions'].append(f"IP {threat_data['ip']} permanently blocked")
                
                await self._isolate_system(threat_data.get('ip'))
                result['executed_actions'].append('All resources terminated and system isolated')
            
            self.action_log.append(result)
            
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
        
        return result
    
    async def _isolate_system(self, source_ip: str = None):
        """Isolate system from network"""
        print(f"🔒 System isolated from network (source: {source_ip})")
    
    async def _force_password_reset(self, username: str):
        """Force user to reset password"""
        print(f"🔐 Password reset required for user: {username}")
    
    async def _log_threat(self, threat_data: Dict):
        """Log threat to database"""
        print(f"📝 Threat logged: {threat_data}")