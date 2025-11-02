import platform
import subprocess
import asyncio
from typing import List

class IPBlocker:
    def __init__(self):
        self.os_type = platform.system()
        self.blocked_ips = set()
        
    async def block_ip(self, ip_address: str, permanent: bool = False) -> bool:
        """Block IP address using firewall"""
        try:
            if self.os_type == "Windows":
                success = await self._block_ip_windows(ip_address)
            elif self.os_type == "Linux":
                success = await self._block_ip_linux(ip_address)
            else:
                print(f"⚠️ OS {self.os_type} not supported for IP blocking")
                return False
            
            if success:
                self.blocked_ips.add(ip_address)
                print(f"✅ IP {ip_address} blocked successfully")
            
            return success
            
        except Exception as e:
            print(f"❌ Failed to block IP {ip_address}: {e}")
            return False
    
    async def _block_ip_windows(self, ip_address: str) -> bool:
        """Block IP on Windows using netsh"""
        try:
            # Create inbound rule
            command = [
                'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                f'name=WARN_Block_{ip_address}',
                'dir=in',
                'action=block',
                f'remoteip={ip_address}',
                'enable=yes'
            ]
            
            result = await asyncio.to_thread(
                subprocess.run,
                command,
                capture_output=True,
                text=True,
                shell=True
            )
            
            if result.returncode == 0:
                print(f"🔥 Windows Firewall: Blocked incoming from {ip_address}")
            
            # Create outbound rule
            command_out = [
                'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                f'name=WARN_Block_Out_{ip_address}',
                'dir=out',
                'action=block',
                f'remoteip={ip_address}',
                'enable=yes'
            ]
            
            result_out = await asyncio.to_thread(
                subprocess.run,
                command_out,
                capture_output=True,
                text=True,
                shell=True
            )
            
            return result.returncode == 0 and result_out.returncode == 0
            
        except Exception as e:
            print(f"Windows firewall error: {e}")
            return False
    
    async def _block_ip_linux(self, ip_address: str) -> bool:
        """Block IP on Linux using iptables"""
        try:
            # Block incoming traffic
            command_in = ['sudo', 'iptables', '-A', 'INPUT', '-s', ip_address, '-j', 'DROP']
            
            result_in = await asyncio.to_thread(
                subprocess.run,
                command_in,
                capture_output=True,
                text=True
            )
            
            # Block outgoing traffic
            command_out = ['sudo', 'iptables', '-A', 'OUTPUT', '-d', ip_address, '-j', 'DROP']
            
            result_out = await asyncio.to_thread(
                subprocess.run,
                command_out,
                capture_output=True,
                text=True
            )
            
            if result_in.returncode == 0:
                print(f"🔥 iptables: Blocked {ip_address}")
            
            return result_in.returncode == 0 and result_out.returncode == 0
            
        except Exception as e:
            print(f"Linux iptables error: {e}")
            return False
    
    async def unblock_ip(self, ip_address: str) -> bool:
        """Unblock IP address"""
        try:
            if self.os_type == "Windows":
                subprocess.run([
                    'netsh', 'advfirewall', 'firewall', 'delete', 'rule',
                    f'name=WARN_Block_{ip_address}'
                ], shell=True)
                subprocess.run([
                    'netsh', 'advfirewall', 'firewall', 'delete', 'rule',
                    f'name=WARN_Block_Out_{ip_address}'
                ], shell=True)
                
            elif self.os_type == "Linux":
                subprocess.run(['sudo', 'iptables', '-D', 'INPUT', '-s', ip_address, '-j', 'DROP'])
                subprocess.run(['sudo', 'iptables', '-D', 'OUTPUT', '-d', ip_address, '-j', 'DROP'])
            
            self.blocked_ips.discard(ip_address)
            print(f"✅ IP {ip_address} unblocked")
            return True
            
        except Exception as e:
            print(f"❌ Failed to unblock IP {ip_address}: {e}")
            return False
    
    def list_blocked_ips(self) -> List[str]:
        """Get list of all blocked IPs"""
        return list(self.blocked_ips)