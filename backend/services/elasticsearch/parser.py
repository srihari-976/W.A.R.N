import json
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class LogParser:
    """
    Parser for transforming and normalizing security logs from various sources.
    Handles extraction of relevant fields from different log formats.
    """
    
    @staticmethod
    def parse_syslog(log_line):
        """
        Parse standard syslog format.
        
        Args:
            log_line (str): Raw syslog line
            
        Returns:
            dict: Parsed log entry
        """
        try:
            # Basic syslog pattern: <priority>timestamp hostname process[pid]: message
            pattern = r'<(\d+)>(\w+\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+(\S+)(?:\[(\d+)\])?: (.*)'
            match = re.match(pattern, log_line)
            
            if not match:
                return {"raw": log_line, "parse_error": "No match for syslog pattern"}
                
            priority, timestamp, hostname, program, pid, message = match.groups()
            
            # Convert timestamp to ISO format
            try:
                current_year = datetime.now().year
                parsed_time = datetime.strptime(f"{current_year} {timestamp}", "%Y %b %d %H:%M:%S")
                iso_timestamp = parsed_time.isoformat()
            except ValueError:
                iso_timestamp = timestamp
                
            return {
                "@timestamp": iso_timestamp,
                "host": {"name": hostname},
                "process": {
                    "name": program,
                    "pid": int(pid) if pid else None
                },
                "message": message,
                "syslog": {
                    "priority": int(priority),
                    "facility": int(int(priority) / 8),
                    "severity": int(priority) % 8
                }
            }
        except Exception as e:
            logger.error(f"Error parsing syslog: {str(e)}")
            return {"raw": log_line, "parse_error": str(e)}
            
    @staticmethod
    def parse_windows_event(event_xml):
        """
        Parse Windows Event XML format.
        
        Args:
            event_xml (str): Windows Event XML
            
        Returns:
            dict: Normalized event data
        """
        try:
            # Simple XML parsing - in production would use proper XML parser
            # Extract key elements from Windows Event XML
            event_id_match = re.search(r'<EventID>(\d+)</EventID>', event_xml)
            time_match = re.search(r'<TimeCreated SystemTime="([^"]+)"', event_xml)
            source_match = re.search(r'<Provider Name="([^"]+)"', event_xml)
            computer_match = re.search(r'<Computer>([^<]+)</Computer>', event_xml)
            
            event = {
                "event": {
                    "provider": source_match.group(1) if source_match else None,
                    "code": int(event_id_match.group(1)) if event_id_match else None,
                },
                "@timestamp": time_match.group(1) if time_match else datetime.now().isoformat(),
                "host": {
                    "name": computer_match.group(1) if computer_match else None
                },
                "winlog": {
                    "raw_xml": event_xml
                }
            }
            
            # Extract event data fields
            data_matches = re.findall(r'<Data Name="([^"]+)">([^<]+)</Data>', event_xml)
            if data_matches:
                event["winlog"]["event_data"] = {}
                for name, value in data_matches:
                    event["winlog"]["event_data"][name] = value
                    
            return event
        except Exception as e:
            logger.error(f"Error parsing Windows event: {str(e)}")
            return {"raw": event_xml, "parse_error": str(e)}
            
    @staticmethod
    def parse_json_log(json_str):
        """
        Parse JSON format logs.
        
        Args:
            json_str (str): JSON log string
            
        Returns:
            dict: Parsed log data
        """
        try:
            parsed = json.loads(json_str)
            
            # Ensure timestamp is in standard format
            if "timestamp" in parsed and "@timestamp" not in parsed:
                parsed["@timestamp"] = parsed["timestamp"]
                
            # Add metadata about parser
            parsed["_meta"] = {
                "parser": "json",
                "parsed_at": datetime.now().isoformat()
            }
            
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON log: {str(e)}")
            return {"raw": json_str, "parse_error": str(e)}
            
    @staticmethod
    def detect_log_type(log_line):
        """
        Detect the type of log based on content.
        
        Args:
            log_line (str): Raw log line
            
        Returns:
            str: Detected log type ('syslog', 'windows', 'json', or 'unknown')
        """
        # Check if JSON
        if log_line.strip().startswith('{') and log_line.strip().endswith('}'):
            try:
                json.loads(log_line)
                return 'json'
            except:
                pass
                
        # Check if Windows Event XML
        if '<Event xmlns' in log_line or '<EventID>' in log_line:
            return 'windows'
            
        # Check if standard syslog
        if re.match(r'<\d+>[\w\s:]+\s+\S+\s+\S+(?:\[\d+\])?: ', log_line):
            return 'syslog'
            
        return 'unknown'
        
    def parse_log(self, log_line):
        """
        Parse a log line by detecting its type and routing to appropriate parser.
        
        Args:
            log_line (str): Raw log line
            
        Returns:
            dict: Parsed log entry
        """
        log_type = self.detect_log_type(log_line)
        
        if log_type == 'syslog':
            return self.parse_syslog(log_line)
        elif log_type == 'windows':
            return self.parse_windows_event(log_line)
        elif log_type == 'json':
            return self.parse_json_log(log_line)
        else:
            return {"raw": log_line, "log_type": "unknown"}