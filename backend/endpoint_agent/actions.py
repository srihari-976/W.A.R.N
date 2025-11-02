# actions.py - Endpoint agent action handlers

import os
import subprocess
import psutil
from backend.utils.logging import get_logger

logger = get_logger(__name__)

def execute_command(command):
    """Execute a system command"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode
        }
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def kill_process(pid):
    """Kill a process by PID"""
    try:
        process = psutil.Process(pid)
        process.terminate()
        return {
            'success': True,
            'message': f"Process {pid} terminated"
        }
    except psutil.NoSuchProcess:
        return {
            'success': False,
            'error': f"Process {pid} not found"
        }
    except Exception as e:
        logger.error(f"Error killing process {pid}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def block_ip(ip_address):
    """Block an IP address using firewall rules"""
    try:
        # This is a placeholder - implement actual firewall rules
        logger.info(f"Blocking IP address: {ip_address}")
        return {
            'success': True,
            'message': f"IP address {ip_address} blocked"
        }
    except Exception as e:
        logger.error(f"Error blocking IP {ip_address}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def scan_file(file_path):
    """Scan a file for malware"""
    try:
        # This is a placeholder - implement actual file scanning
        logger.info(f"Scanning file: {file_path}")
        return {
            'success': True,
            'message': f"File {file_path} scanned",
            'result': 'clean'  # or 'infected'
        }
    except Exception as e:
        logger.error(f"Error scanning file {file_path}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def collect_system_info():
    """Collect system information"""
    try:
        info = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'network_connections': len(psutil.net_connections()),
            'process_count': len(psutil.pids())
        }
        return {
            'success': True,
            'data': info
        }
    except Exception as e:
        logger.error(f"Error collecting system info: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
