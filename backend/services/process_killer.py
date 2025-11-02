import psutil
import time
from typing import List, Dict

class ProcessKiller:
    def __init__(self):
        self.killed_processes = []
        
    async def terminate_process(self, process_identifier: str) -> bool:
        """Terminate process by name or PID"""
        try:
            target_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if (process_identifier.lower() in proc.info['name'].lower() or
                        str(proc.info['pid']) == process_identifier):
                        target_processes.append(proc)
                except:
                    continue
            
            # Kill processes
            for proc in target_processes:
                try:
                    proc.terminate()
                    proc.wait(timeout=3)
                    
                    self.killed_processes.append({
                        'pid': proc.pid,
                        'name': proc.name(),
                        'timestamp': time.time()
                    })
                    
                    print(f"💀 Terminated process: {proc.name()} (PID: {proc.pid})")
                except:
                    proc.kill()
            
            return len(target_processes) > 0
            
        except Exception as e:
            print(f"❌ Failed to kill process {process_identifier}: {e}")
            return False
    
    async def kill_browser_processes(self) -> Dict:
        """Kill all browser processes (Instagram-style cutoff)"""
        browsers = ['chrome', 'firefox', 'edge', 'safari', 'opera', 'brave']
        killed = []
        
        for browser in browsers:
            success = await self.terminate_process(browser)
            if success:
                killed.append(browser)
        
        return {
            'killed_browsers': killed,
            'count': len(killed)
        }