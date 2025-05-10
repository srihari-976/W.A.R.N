import os
import logging
from typing import Dict, List, Any, Optional, Union
import json
from datetime import datetime
import asyncio
import aiohttp
import paramiko
import boto3
from botocore.exceptions import ClientError
import yaml
import jinja2
import schedule
import time
from threading import Thread

logger = logging.getLogger(__name__)

class AutomationEngine:
    """Engine for automating security response actions"""
    
    def __init__(self, config_path: str = "config/automation.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.templates = self._load_templates()
        self.running = False
        self.scheduler_thread = None
        
        # Initialize clients
        self.ssh_client = None
        self.aws_client = None
        self.http_session = None
    
    def _load_config(self) -> Dict[str, Any]:
        """Load automation configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded automation config from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading automation config: {e}")
            return {}
    
    def _load_templates(self) -> Dict[str, jinja2.Template]:
        """Load automation templates"""
        try:
            templates = {}
            template_dir = self.config.get('template_dir', 'templates/automation')
            
            for filename in os.listdir(template_dir):
                if filename.endswith('.j2'):
                    with open(os.path.join(template_dir, filename), 'r') as f:
                        template_content = f.read()
                        template_name = filename[:-3]  # Remove .j2 extension
                        templates[template_name] = jinja2.Template(template_content)
            
            logger.info(f"Loaded {len(templates)} automation templates")
            return templates
        except Exception as e:
            logger.error(f"Error loading automation templates: {e}")
            return {}
    
    async def _initialize_clients(self):
        """Initialize automation clients"""
        try:
            # Initialize SSH client
            if 'ssh' in self.config:
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh_client.connect(
                    hostname=self.config['ssh']['host'],
                    username=self.config['ssh']['username'],
                    key_filename=self.config['ssh'].get('key_file')
                )
            
            # Initialize AWS client
            if 'aws' in self.config:
                self.aws_client = boto3.client(
                    'ec2',
                    aws_access_key_id=self.config['aws']['access_key'],
                    aws_secret_access_key=self.config['aws']['secret_key'],
                    region_name=self.config['aws']['region']
                )
            
            # Initialize HTTP session
            self.http_session = aiohttp.ClientSession()
            
            logger.info("Initialized automation clients")
        except Exception as e:
            logger.error(f"Error initializing automation clients: {e}")
            raise
    
    async def _close_clients(self):
        """Close automation clients"""
        try:
            if self.ssh_client:
                self.ssh_client.close()
            
            if self.http_session:
                await self.http_session.close()
            
            logger.info("Closed automation clients")
        except Exception as e:
            logger.error(f"Error closing automation clients: {e}")
    
    async def execute_ssh_command(self, command: str) -> Dict[str, Any]:
        """Execute SSH command"""
        try:
            if not self.ssh_client:
                raise ValueError("SSH client not initialized")
            
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()
            
            return {
                'success': exit_code == 0,
                'stdout': stdout.read().decode(),
                'stderr': stderr.read().decode(),
                'exit_code': exit_code
            }
        except Exception as e:
            logger.error(f"Error executing SSH command: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def execute_aws_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute AWS action"""
        try:
            if not self.aws_client:
                raise ValueError("AWS client not initialized")
            
            # Get the appropriate AWS client method
            method = getattr(self.aws_client, action)
            if not method:
                raise ValueError(f"Unknown AWS action: {action}")
            
            # Execute the action
            response = method(**params)
            
            return {
                'success': True,
                'response': response
            }
        except Exception as e:
            logger.error(f"Error executing AWS action: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def execute_http_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Execute HTTP request"""
        try:
            if not self.http_session:
                raise ValueError("HTTP session not initialized")
            
            async with self.http_session.request(method, url, **kwargs) as response:
                return {
                    'success': response.status < 400,
                    'status': response.status,
                    'headers': dict(response.headers),
                    'body': await response.text()
                }
        except Exception as e:
            logger.error(f"Error executing HTTP request: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render automation template"""
        try:
            if template_name not in self.templates:
                raise ValueError(f"Template not found: {template_name}")
            
            return self.templates[template_name].render(**context)
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            raise
    
    async def execute_automation(self, automation_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute automation workflow"""
        try:
            if automation_name not in self.config['workflows']:
                raise ValueError(f"Automation workflow not found: {automation_name}")
            
            workflow = self.config['workflows'][automation_name]
            results = []
            
            for step in workflow['steps']:
                step_type = step['type']
                step_config = step['config']
                
                # Render template if present
                if 'template' in step_config:
                    rendered_config = self._render_template(
                        step_config['template'],
                        context
                    )
                    step_config = json.loads(rendered_config)
                
                # Execute step based on type
                if step_type == 'ssh':
                    result = await self.execute_ssh_command(step_config['command'])
                elif step_type == 'aws':
                    result = await self.execute_aws_action(
                        step_config['action'],
                        step_config['params']
                    )
                elif step_type == 'http':
                    result = await self.execute_http_request(
                        step_config['method'],
                        step_config['url'],
                        **step_config.get('options', {})
                    )
                else:
                    raise ValueError(f"Unknown step type: {step_type}")
                
                results.append({
                    'step': step['name'],
                    'result': result
                })
                
                # Check if we should continue based on result
                if not result['success'] and step.get('fail_fast', True):
                    break
            
            return {
                'success': all(r['result']['success'] for r in results),
                'steps': results
            }
            
        except Exception as e:
            logger.error(f"Error executing automation: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _scheduler_loop(self):
        """Scheduler loop for periodic automations"""
        while self.running:
            schedule.run_pending()
            time.sleep(1)
    
    def start_scheduler(self):
        """Start automation scheduler"""
        try:
            if self.running:
                return
            
            self.running = True
            self.scheduler_thread = Thread(target=self._scheduler_loop)
            self.scheduler_thread.start()
            
            # Schedule periodic automations
            for automation in self.config.get('periodic', []):
                schedule.every(automation['interval']).minutes.do(
                    lambda: asyncio.run(self.execute_automation(
                        automation['name'],
                        automation.get('context', {})
                    ))
                )
            
            logger.info("Started automation scheduler")
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            raise
    
    def stop_scheduler(self):
        """Stop automation scheduler"""
        try:
            if not self.running:
                return
            
            self.running = False
            if self.scheduler_thread:
                self.scheduler_thread.join()
            
            logger.info("Stopped automation scheduler")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
            raise
    
    async def start(self):
        """Start automation engine"""
        try:
            await self._initialize_clients()
            self.start_scheduler()
            logger.info("Started automation engine")
        except Exception as e:
            logger.error(f"Error starting automation engine: {e}")
            raise
    
    async def stop(self):
        """Stop automation engine"""
        try:
            self.stop_scheduler()
            await self._close_clients()
            logger.info("Stopped automation engine")
        except Exception as e:
            logger.error(f"Error stopping automation engine: {e}")
            raise
