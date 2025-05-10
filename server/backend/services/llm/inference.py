import os
import logging
import json
import time
from typing import Dict, List, Any, Optional, Union
from concurrent.futures import ThreadPoolExecutor
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

def analyze_event_context(event_text: str, model_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze the context of a security event using LLM.
    
    Args:
        event_text: Text description of the event
        model_id: Optional ID of the specific model to use
        
    Returns:
        Dictionary containing analysis results
    """
    # For now, return a simulated response
    return {
        "threat_level": "medium",
        "confidence": 0.85,
        "analysis": "Potential unauthorized access attempt detected",
        "recommendations": [
            "Monitor for additional suspicious activity",
            "Review access logs",
            "Update access controls"
        ]
    }

class LLaMAInferenceEngine:
    """Inference engine for LLaMA model security analysis"""
    
    def __init__(
        self,
        model_path: str,
        max_length: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        num_return_sequences: int = 1
    ):
        self.model_path = model_path
        self.max_length = max_length
        self.temperature = temperature
        self.top_p = top_p
        self.num_return_sequences = num_return_sequences
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = None
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the LLaMA model and tokenizer"""
        try:
            logger.info(f"Loading LLaMA model from {self.model_path}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto"
            )
            logger.info("LLaMA model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading LLaMA model: {e}")
            raise
    
    def _prepare_prompt(self, security_event: Dict[str, Any]) -> str:
        """Prepare prompt for security event analysis"""
        prompt = f"""Analyze the following security event and provide insights:

Event Details:
- Timestamp: {security_event.get('timestamp', 'unknown')}
- Source IP: {security_event.get('source_ip', 'unknown')}
- Destination IP: {security_event.get('destination_ip', 'unknown')}
- Protocol: {security_event.get('protocol', 'unknown')}
- Event Type: {security_event.get('event_type', 'unknown')}
- Severity: {security_event.get('severity', 'unknown')}
- Description: {security_event.get('description', 'unknown')}

Please analyze this event and provide:
1. Potential threat assessment
2. Recommended actions
3. Similar known attack patterns
4. Risk level assessment

Analysis:"""
        return prompt
    
    def _parse_analysis(self, response: str) -> Dict[str, Any]:
        """Parse model response into structured format"""
        try:
            # Split response into sections
            sections = response.split("\n\n")
            
            # Extract sections
            threat_assessment = sections[0] if len(sections) > 0 else ""
            recommended_actions = sections[1] if len(sections) > 1 else ""
            known_patterns = sections[2] if len(sections) > 2 else ""
            risk_level = sections[3] if len(sections) > 3 else ""
            
            # Extract confidence scores
            confidence_scores = {}
            for section in sections:
                if "confidence:" in section.lower():
                    try:
                        score = float(section.split("confidence:")[-1].strip())
                        confidence_scores[section.split(":")[0].strip()] = score
                    except:
                        pass
            
            return {
                "threat_assessment": threat_assessment,
                "recommended_actions": recommended_actions,
                "known_patterns": known_patterns,
                "risk_level": risk_level,
                "confidence_scores": confidence_scores,
                "raw_analysis": response
            }
        except Exception as e:
            logger.error(f"Error parsing analysis: {e}")
            return {
                "error": str(e),
                "threat_assessment": "Error in analysis",
                "recommended_actions": "Unable to generate recommendations",
                "known_patterns": "Unable to identify patterns",
                "risk_level": "Unknown",
                "confidence_scores": {},
                "raw_analysis": response
            }
    
    def analyze_event(self, security_event: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single security event"""
        try:
            # Prepare prompt
            prompt = self._prepare_prompt(security_event)
            
            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=self.max_length,
                    num_return_sequences=self.num_return_sequences,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    do_sample=True
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract analysis from response
            analysis = response.split("Analysis:")[-1].strip()
            
            # Parse analysis
            structured_analysis = self._parse_analysis(analysis)
            
            return structured_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing security event: {e}")
            return {
                "error": str(e),
                "threat_assessment": "Error in analysis",
                "recommended_actions": "Unable to generate recommendations",
                "known_patterns": "Unable to identify patterns",
                "risk_level": "Unknown",
                "confidence_scores": {},
                "raw_analysis": ""
            }
    
    def batch_analyze_events(self, security_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze multiple security events in batch"""
        try:
            results = []
            for event in security_events:
                analysis = self.analyze_event(event)
                results.append({
                    "event": event,
                    "analysis": analysis
                })
            return results
        except Exception as e:
            logger.error(f"Error in batch analysis: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "model_path": self.model_path,
            "device": self.device,
            "model_parameters": sum(p.numel() for p in self.model.parameters()),
            "model_layers": len(self.model.model.layers),
            "vocab_size": self.tokenizer.vocab_size,
            "max_length": self.max_length,
            "temperature": self.temperature,
            "top_p": self.top_p
        }

class InferenceEngine:
    """Engine for running inference with fine-tuned LLaMA models."""
    
    def __init__(self, model_path: str, max_concurrent_requests: int = 10,
                max_tokens: int = 1024, temperature: float = 0.2):
        """
        Initialize the inference engine.
        
        Args:
            model_path: Path to the fine-tuned LLaMA model
            max_concurrent_requests: Maximum number of concurrent inference requests
            max_tokens: Maximum number of tokens in model responses
            temperature: Temperature parameter for response generation
        """
        self.model_path = model_path
        self.max_concurrent_requests = max_concurrent_requests
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # In a real implementation, this would load the model
        # For this example, we'll simulate model loading
        logger.info(f"Loading LLaMA model from {model_path}")
        self._load_model()
        
        # Initialize thread pool for concurrent inference
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_requests)
        
        logger.info(f"Inference engine initialized with model: {model_path}")
    
    def _load_model(self):
        """Load the LLaMA model (simulated in this implementation)."""
        # In a real implementation, this would use libraries like transformers
        # to load the actual model. This is a simplified version.
        
        # Check if model configuration exists
        config_path = os.path.join(self.model_path, "fine_tuning_config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = json.load(f)
                logger.info(f"Loaded model configuration: {self.config}")
        else:
            logger.warning(f"No model configuration found at {config_path}")
            self.config = {}
    
    def analyze_security_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a security log entry using the LLaMA model.
        
        Args:
            log_data: Dictionary containing the security log entry
            
        Returns:
            Dictionary with analysis results
        """
        # Format the prompt for log analysis
        prompt = self._format_log_analysis_prompt(log_data)
        
        # Run inference
        response = self._run_inference(prompt)
        
        # Parse the response
        result = self._parse_log_analysis_response(response)
        
        return result
    
    def detect_attack_pattern(self, event_sequence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect attack patterns in a sequence of security events.
        
        Args:
            event_sequence: List of security events in chronological order
            
        Returns:
            Dictionary with attack pattern detection results
        """
        # Format the prompt for attack pattern detection
        prompt = self._format_attack_pattern_prompt(event_sequence)
        
        # Run inference
        response = self._run_inference(prompt)
        
        # Parse the response
        result = self._parse_attack_pattern_response(response)
        
        return result
    
    def generate_incident_report(self, incident_data: Dict[str, Any]) -> str:
        """
        Generate an incident report from security incident data.
        
        Args:
            incident_data: Dictionary containing incident information
            
        Returns:
            Generated incident report as a string
        """
        # Format the prompt for incident report generation
        prompt = self._format_incident_report_prompt(incident_data)
        
        # Run inference with higher max tokens for report generation
        response = self._run_inference(prompt, max_tokens=2048)
        
        # Return the generated report
        return response.strip()
    
    def _format_log_analysis_prompt(self, log_data: Dict[str, Any]) -> str:
        """
        Format a security log analysis prompt.
        
        Args:
            log_data: Dictionary containing the security log entry
            
        Returns:
            Formatted prompt string
        """
        # Convert log data to a string representation
        log_str = json.dumps(log_data, indent=2)
        
        prompt = f"""
        You are a cybersecurity expert analyzing security logs.
        
        Analyze the following security log entry and provide:
        1. A determination if this log entry indicates a security threat (benign, suspicious, or malicious)
        2. The specific indicators of compromise (IoCs) present, if any
        3. The potential MITRE ATT&CK techniques that might be involved
        4. Recommended next steps for investigation or response
        
        Security Log Entry:
        {log_str}
        
        Your Analysis:
        """
        
        return prompt
    
    def _format_attack_pattern_prompt(self, event_sequence: List[Dict[str, Any]]) -> str:
        """
        Format an attack pattern detection prompt.
        
        Args:
            event_sequence: List of security events
            
        Returns:
            Formatted prompt string
        """
        # Convert events to a string representation
        events_str = json.dumps(event_sequence, indent=2)
        
        prompt = f"""
        You are a cybersecurity expert analyzing sequences of security events.
        
        Analyze the following sequence of security events and determine:
        1. If they represent a coordinated attack
        2. The attack technique or pattern that might be occurring
        3. The attack phase (reconnaissance, initial access, execution, persistence, etc.)
        4. Recommended defensive actions
        
        Security Event Sequence:
        {events_str}
        
        Your Analysis:
        """
        
        return prompt
    
    def _format_incident_report_prompt(self, incident_data: Dict[str, Any]) -> str:
        """
        Format an incident report generation prompt.
        
        Args:
            incident_data: Dictionary containing incident information
            
        Returns:
            Formatted prompt string
        """
        # Extract key incident information
        incident_type = incident_data.get("type", "Unknown")
        timestamp = incident_data.get("timestamp", "Unknown")
        affected_systems = ", ".join(incident_data.get("affected_systems", ["Unknown"]))
        summary = incident_data.get("summary", "Unknown incident")
        events = json.dumps(incident_data.get("events", []), indent=2)
        
        prompt = f"""
        You are a cybersecurity expert creating an incident report.
        
        Generate a professional security incident report based on the following information:
        
        Incident Type: {incident_type}
        Timestamp: {timestamp}
        Affected Systems: {affected_systems}
        Summary: {summary}
        
        Related Events:
        {events}
        
        Create a comprehensive security incident report with the following sections:
        1. Executive Summary
        2. Incident Timeline
        3. Technical Analysis
        4. Impact Assessment
        5. Recommendations
        
        Security Incident Report:
        """
        
        return prompt
    
    def _run_inference(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """
        Run inference with the LLaMA model.
        
        Args:
            prompt: The prompt to send to the model
            max_tokens: Optional override for max tokens
            
        Returns:
            Model response as a string
        """
        # In a real implementation, this would run actual inference
        # For this example, we'll simulate model inference
        
        # Use provided max_tokens or fall back to instance default
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        logger.debug(f"Running inference with prompt length {len(prompt)}")
        
        # Simulate inference time based on prompt length and max tokens
        inference_time = (len(prompt) / 1000) + (tokens / 500)
        time.sleep(min(inference_time, 0.5))  # Simulate inference time, capped at 0.5s
        
        # Generate a simulated response based on the prompt
        if "incident report" in prompt.lower():
            return self._simulate_incident_report(prompt)
        elif "attack pattern" in prompt.lower():
            return self._simulate_attack_pattern_analysis(prompt)
        else:
            return self._simulate_log_analysis(prompt)
    
    def _parse_log_analysis_response(self, response: str) -> Dict[str, Any]:
        """
        Parse log analysis response into a structured format.
        
        Args:
            response: Raw response from the model
            
        Returns:
            Structured analysis result
        """
        # Basic parsing of response content
        result = {
            "threat_level": "unknown",
            "indicators": [],
            "mitre_techniques": [],
            "recommendations": [],
            "raw_response": response
        }
        
        # Extract threat level
        if "BENIGN" in response.upper():
            result["threat_level"] = "benign"
        elif "SUSPICIOUS" in response.upper():
            result["threat_level"] = "suspicious"
        elif "MALICIOUS" in response.upper():
            result["threat_level"] = "malicious"
        
        # Extract IoCs, MITRE techniques, and recommendations
        # This is a simplified parser - production version would be more robust
        sections = response.split("\n\n")
        for section in sections:
            if "Indicators of Compromise" in section:
                lines = section.split("\n")[1:]  # Skip the header
                for line in lines:
                    if line.strip() and line.strip().startswith("-"):
                        result["indicators"].append(line.strip()[2:])
            
            elif "MITRE ATT&CK Techniques" in section:
                lines = section.split("\n")[1:]  # Skip the header
                for line in lines:
                    if "T" in line and "(" in line:
                        # Extract technique ID (e.g., T1110)
                        tid = line.split("(")[0].strip()
                        if tid.startswith("-"):
                            tid = tid[2:]
                        result["mitre_techniques"].append(tid.strip())
            
            elif "Recommended Next Steps" in section or "Recommended" in section:
                lines = section.split("\n")[1:]  # Skip the header
                for line in lines:
                    if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith("-")):
                        # Clean up the recommendation text
                        if line.strip()[0].isdigit():
                            # Remove the numbering
                            text = line.strip()[2:].strip()
                        else:
                            # Remove the bullet point
                            text = line.strip()[1:].strip()
                        result["recommendations"].append(text)
        
        return result
    
    def _parse_attack_pattern_response(self, response: str) -> Dict[str, Any]:
        """
        Parse attack pattern analysis response into a structured format.
        
        Args:
            response: Raw response from the model
            
        Returns:
            Structured analysis result
        """
        # Initialize result structure
        result = {
            "is_attack": False,
            "attack_pattern": "",
            "attack_phase": "",
            "mitre_techniques": [],
            "recommended_actions": [],
            "raw_response": response
        }
        
        # Determine if it's an attack
        if "DOES represent" in response:
            result["is_attack"] = True
        
        # Extract attack pattern
        if "Attack Technique/Pattern:" in response:
            pattern_section = response.split("Attack Technique/Pattern:")[1].split("\n\n")[0]
            result["attack_pattern"] = pattern_section.strip()
        
        # Extract attack phase
        if "Attack Phase:" in response:
            phase_section = response.split("Attack Phase:")[1].split("\n\n")[0]
            result["attack_phase"] = phase_section.strip()
        
        # Extract MITRE techniques
        if "MITRE ATT&CK Techniques:" in response:
            techniques_section = response.split("MITRE ATT&CK Techniques:")[1].split("\n\n")[0]
            for line in techniques_section.split("\n"):
                if "T" in line and "(" in line and "-" in line:
                    # Extract technique ID (e.g., T1566)
                    tid = line.split("(")[0].strip()
                    if tid.startswith("-"):
                        tid = tid[2:]
                    result["mitre_techniques"].append(tid.strip())
        
        # Extract recommended actions
        if "Recommended Defensive Actions:" in response:
            actions_section = response.split("Recommended Defensive Actions:")[1]
            for line in actions_section.split("\n"):
                if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith("-")):
                    # Clean up the action text
                    if line.strip()[0].isdigit():
                        # Remove the numbering
                        text = line.strip()[2:].strip()
                    else:
                        # Remove the bullet point
                        text = line.strip()[1:].strip()
                    result["recommended_actions"].append(text)
        
        return result
    
    def _simulate_log_analysis(self, prompt: str) -> str:
        """Simulate a log analysis response."""
        # Extract log type from prompt for more realistic simulation
        log_type = "authentication failure"
        threat_level = "suspicious"
        
        if "failed login" in prompt.lower() or "authentication failure" in prompt.lower():
            log_type = "authentication failure"
            threat_level = "suspicious"
        elif "network connection" in prompt.lower():
            log_type = "network connection"
            threat_level = "benign"
        elif "command execution" in prompt.lower() or "powershell" in prompt.lower():
            log_type = "command execution"
            threat_level = "malicious"
        
        # Generate simulated response
        if threat_level == "benign":
            return f"""
            Based on my analysis, this log entry appears to be BENIGN.
            
            Indicators of Compromise (IoCs): None detected
            
            MITRE ATT&CK Techniques: N/A
            
            Recommended Next Steps:
            1. No immediate action required
            2. Consider adding this pattern to your baseline of normal activity
            3. Continue regular monitoring
            """
        elif threat_level == "suspicious":
            return f"""
            Based on my analysis, this log entry appears to be SUSPICIOUS.
            
            Indicators of Compromise (IoCs):
            - Unusual {log_type} pattern
            - Activity outside normal business hours
            - Multiple failed attempts
            
            MITRE ATT&CK Techniques:
            - T1110 (Brute Force) - Potential credential stuffing or password spraying
            
            Recommended Next Steps:
            1. Investigate the source IP address
            2. Check for other failed login attempts from the same source
            3. Consider implementing account lockout policies
            4. Notify the user about suspicious login attempts
            """
        else:  # malicious
            return f"""
            Based on my analysis, this log entry appears to be MALICIOUS.
            
            Indicators of Compromise (IoCs):
            - Known malicious {log_type} pattern
            - Suspicious command arguments
            - Attempt to disable security controls
            
            MITRE ATT&CK Techniques:
            - T1059 (Command and Scripting Interpreter)
            - T1562 (Impair Defenses)
            
            Recommended Next Steps:
            1. Isolate the affected system immediately
            2. Investigate lateral movement attempts
            3. Analyze running processes and persistence mechanisms
            4. Escalate to incident response team
            """
    
    def _simulate_attack_pattern_analysis(self, prompt: str) -> str:
        """Simulate an attack pattern analysis response."""
        return """
        Based on my analysis of the security event sequence, this DOES represent a coordinated attack.
        
        Attack Technique/Pattern:
        This appears to be a multi-stage attack involving initial access via phishing, followed by command execution and lateral movement attempts.
        
        Attack Phase:
        The events indicate the attacker has completed the initial access phase and is currently in the execution and lateral movement phases of the attack lifecycle.
        
        MITRE ATT&CK Techniques:
        - T1566 (Phishing) - Initial access via email attachment
        - T1059.001 (PowerShell) - Execution of malicious commands
        - T1021.001 (Remote Desktop Protocol) - Lateral movement attempts
        
        Recommended Defensive Actions:
        1. Isolate the initially compromised host (192.168.1.45) immediately
        2. Block outbound connections to the C2 server (203.0.113.100)
        3. Disable the compromised user account and force password resets
        4. Scan the environment for the observed indicators of compromise
        5. Review RDP and PowerShell logging across the environment
        """
    
    def _simulate_incident_report(self, prompt: str) -> str:
        """Simulate an incident report response."""
        return """
        # Security Incident Report
        
        ## 1. Executive Summary
        
        On 2023-04-15 at 02:34 UTC, a security incident was detected involving unauthorized access to the HR database server. The attack originated from a compromised user account and resulted in the exfiltration of approximately 2.3GB of data. The incident has been contained, and all affected systems have been secured. No evidence of persistent access was found.
        
        ## 2. Incident Timeline
        
        - 2023-04-15 02:34 UTC: Initial suspicious login detected from an unusual location
        - 2023-04-15 02:37 UTC: Privilege escalation attempt observed
        - 2023-04-15 02:42 UTC: Database query with excessive data retrieval executed
        - 2023-04-15 02:47 UTC: Large outbound data transfer detected
        - 2023-04-15 03:15 UTC: Security team alerted and response initiated
        - 2023-04-15 03:28 UTC: Affected account isolated and access revoked
        - 2023-04-15 04:12 UTC: Systems secured and evidence collection completed
        
        ## 3. Technical Analysis
        
        The attack utilized a compromised user account with valid credentials, suggesting either a successful phishing attack or password reuse. Once access was gained, the attacker used known privilege escalation techniques to obtain increased database permissions. The attack methodology aligns with the MITRE ATT&CK techniques T1078 (Valid Accounts), T1078.002 (Domain Accounts), and T1114 (Email Collection).
        
        Analysis of the database logs shows a series of queries designed to extract employee personal information, including names, addresses, and financial details. The data exfiltration occurred via encrypted HTTPS connections to a previously unseen external IP address.
        
        ## 4. Impact Assessment
        
        The incident impacted the following assets:
        - HR database server (DB-HR-01)
        - User account (jsmith@example.com)
        
        The following data was potentially exposed:
        - Employee personal information (approximately 850 records)
        - Salary and banking information (approximately 750 records)
        
        Business impact:
        - Potential regulatory notification requirements under GDPR
        - Possible financial impact for credit monitoring services
        - Temporary disruption to HR systems during investigation (4 hours)
        
        ## 5. Recommendations
        
        Immediate actions:
        1. Force password resets for all administrative accounts
        2. Implement multi-factor authentication for database access
        3. Review and restrict database query size limits
        
        Short-term improvements:
        1. Enhance monitoring for large data transfers and unusual database queries
        2. Conduct phishing awareness training for all employees
        3. Implement data loss prevention (DLP) solutions for sensitive databases
        4. Review and update database access controls and permissions
        
        Long-term strategy:
        1. Implement a comprehensive Identity and Access Management (IAM) solution
        2. Consider data encryption for sensitive employee information
        3. Develop and regularly test an incident response playbook for data breaches
        4. Conduct regular security assessments of critical infrastructure
        """
    
    def run_batch_analysis(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Run batch analysis on multiple security log entries concurrently.
        
        Args:
            log_entries: List of security log entries to analyze
            
        Returns:
            List of analysis results for each log entry
        """
        # Submit each log entry for analysis in parallel
        futures = []
        for log_entry in log_entries:
            future = self.executor.submit(self.analyze_security_log, log_entry)
            futures.append(future)
        
        # Collect results as they complete
        results = []
        for future in futures:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Error in batch analysis: {e}")
                results.append({"error": str(e), "threat_level": "unknown"})
        
        return results
    
    def generate_threat_intelligence(self, data_sources: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate threat intelligence from multiple data sources.
        
        Args:
            data_sources: Dictionary of data sources (logs, events, etc.)
            
        Returns:
            Threat intelligence report
        """
        # Format the prompt for threat intelligence generation
        prompt = self._format_threat_intelligence_prompt(data_sources)
        
        # Run inference with higher max tokens
        response = self._run_inference(prompt, max_tokens=2048)
        
        # Parse the response
        result = self._parse_threat_intelligence_response(response)
        
        return result
    
    def _format_threat_intelligence_prompt(self, data_sources: Dict[str, Any]) -> str:
        """
        Format a threat intelligence generation prompt.
        
        Args:
            data_sources: Dictionary of data sources
            
        Returns:
            Formatted prompt string
        """
        # Format each data source as a string
        formatted_sources = []
        for source_name, source_data in data_sources.items():
            formatted_sources.append(f"### {source_name}\n{json.dumps(source_data, indent=2)}")
        
        # Join all formatted sources
        all_sources = "\n\n".join(formatted_sources)
        
        prompt = f"""
        You are a cybersecurity threat intelligence analyst.
        
        Generate a comprehensive threat intelligence report based on the following data sources:
        
        {all_sources}
        
        Your report should include:
        1. Threat actor profile and attribution (if possible)
        2. Tactics, techniques, and procedures (TTPs) observed
        3. Indicators of compromise (IoCs)
        4. Recommended detection and mitigation strategies
        
        Threat Intelligence Report:
        """
        
        return prompt
    
    def _parse_threat_intelligence_response(self, response: str) -> Dict[str, Any]:
        """
        Parse threat intelligence response into a structured format.
        
        Args:
            response: Raw response from the model
            
        Returns:
            Structured threat intelligence report
        """
        # Initialize result structure
        result = {
            "threat_actor": "",
            "ttps": [],
            "iocs": [],
            "mitre_techniques": [],
            "recommendations": [],
            "raw_report": response
        }
        
        # Extract threat actor information
        if "Threat Actor:" in response or "Threat Actor Profile:" in response:
            actor_section = ""
            if "Threat Actor:" in response:
                actor_section = response.split("Threat Actor:")[1].split("\n\n")[0]
            else:
                actor_section = response.split("Threat Actor Profile:")[1].split("\n\n")[0]
            result["threat_actor"] = actor_section.strip()
        
        # Extract TTPs
        if "Tactics, Techniques, and Procedures (TTPs):" in response:
            ttps_section = response.split("Tactics, Techniques, and Procedures (TTPs):")[1].split("\n\n")[0]
            for line in ttps_section.split("\n"):
                if line.strip() and line.strip().startswith("-"):
                    result["ttps"].append(line.strip()[2:])
        
        # Extract IoCs
        if "Indicators of Compromise (IoCs):" in response:
            iocs_section = response.split("Indicators of Compromise (IoCs):")[1].split("\n\n")[0]
            for line in iocs_section.split("\n"):
                if line.strip() and line.strip().startswith("-"):
                    result["iocs"].append(line.strip()[2:])
        
        # Extract MITRE techniques
        if "MITRE ATT&CK Techniques:" in response:
            techniques_section = response.split("MITRE ATT&CK Techniques:")[1].split("\n\n")[0]
            for line in techniques_section.split("\n"):
                if "T" in line and "-" in line:
                    # Extract technique ID (e.g., T1566)
                    tid = line.strip()
                    if tid.startswith("-"):
                        tid = tid[2:]
                    if "(" in tid:
                        tid = tid.split("(")[0].strip()
                    result["mitre_techniques"].append(tid)
        
        # Extract recommendations
        if "Recommended " in response:
            for section_name in ["Recommended Detection and Mitigation Strategies:", 
                                "Recommended Mitigations:", 
                                "Recommendations:"]:
                if section_name in response:
                    rec_section = response.split(section_name)[1].split("\n\n")[0]
                    for line in rec_section.split("\n"):
                        if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith("-")):
                            # Clean up the recommendation text
                            if line.strip()[0].isdigit():
                                # Remove the numbering
                                text = line.strip()[2:].strip()
                            else:
                                # Remove the bullet point
                                text = line.strip()[1:].strip()
                            result["recommendations"].append(text)
        
        return result
    
    def close(self):
        """Clean up resources used by the inference engine."""
        logger.info("Shutting down inference engine")
        self.executor.shutdown()
        logger.info("Inference engine resources released")


def create_inference_engine(model_path: str, **kwargs) -> InferenceEngine:
    """
    Factory function to create an instance of InferenceEngine.
    
    Args:
        model_path: Path to the fine-tuned LLaMA model
        **kwargs: Additional arguments to pass to InferenceEngine constructor
        
    Returns:
        Initialized InferenceEngine instance
    """
    logger.info(f"Creating inference engine with model at {model_path}")
    return InferenceEngine(model_path, **kwargs)