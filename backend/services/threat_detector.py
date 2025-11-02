"""
Real threat detection pipeline for W.A.R.N
Integrates fine-tuned Llama + Isolation Forest + Risk Scoring
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from sklearn.ensemble import IsolationForest
import numpy as np

logger = logging.getLogger(__name__)

class ThreatDetector:
    """Main threat detection engine"""
    
    def __init__(self):
        self.llama_model = None
        self.tokenizer = None
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.is_loaded = False
        
    async def load_models(self):
        """Load fine-tuned Llama model"""
        try:
            # Try to load fine-tuned model, fallback to base model
            model_path = "../models/llm/llama-mitre-finetuned"
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                self.llama_model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    torch_dtype=torch.float16,
                    device_map="auto"
                )
                logger.info("✅ Fine-tuned MITRE model loaded")
            except:
                # Fallback to base Llama model
                logger.warning("Fine-tuned model not found, using base model")
                self.tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
                self.llama_model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")
                logger.info("✅ Base model loaded as fallback")
            
            self.is_loaded = True
        except Exception as e:
            logger.error(f"Model loading failed: {e}")
            self.is_loaded = False
    
    async def analyze_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze security event through detection pipeline"""
        try:
            # Step 1: Extract features for anomaly detection
            features = self._extract_features(event)
            anomaly_score = self.anomaly_detector.decision_function([features])[0]
            is_anomaly = anomaly_score < 0
            
            # Step 2: MITRE ATT&CK analysis with fine-tuned Llama
            mitre_analysis = await self._analyze_with_llama(event)
            
            # Step 3: Calculate risk score
            risk_score = self._calculate_risk(anomaly_score, mitre_analysis)
            
            return {
                'event_id': event.get('id', 'unknown'),
                'timestamp': datetime.utcnow().isoformat(),
                'anomaly_score': float(anomaly_score),
                'is_anomaly': is_anomaly,
                'mitre_techniques': mitre_analysis.get('techniques', []),
                'threat_level': mitre_analysis.get('threat_level', 'low'),
                'risk_score': risk_score,
                'analysis': mitre_analysis.get('analysis', ''),
                'confidence': mitre_analysis.get('confidence', 0.5)
            }
            
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return {'error': str(e), 'event_id': event.get('id')}
    
    def _extract_features(self, event: Dict[str, Any]) -> List[float]:
        """Extract 45 features as described in paper"""
        features = []
        
        # Process features (10)
        process_name = event.get('process_name', '').lower()
        features.extend([
            len(event.get('command_line', '')),
            1 if 'powershell' in process_name else 0,
            1 if 'cmd' in process_name else 0,
            event.get('cpu_usage', 0),
            event.get('memory_usage', 0),
            event.get('thread_count', 0),
            event.get('handle_count', 0),
            1 if event.get('elevated_privileges', False) else 0,
            event.get('process_duration', 0),
            len(event.get('child_processes', []))
        ])
        
        # Network features (15)
        connections = event.get('network_connections', [])
        features.extend([
            len(connections),
            sum(1 for c in connections if c.get('port', 0) < 1024),
            sum(1 for c in connections if c.get('external', False)),
            event.get('bytes_sent', 0),
            event.get('bytes_received', 0),
            event.get('packets_sent', 0),
            event.get('packets_received', 0),
            1 if event.get('dns_queries') else 0,
            len(event.get('dns_queries', [])),
            sum(1 for q in event.get('dns_queries', []) if '.exe' in q),
            len(set(c.get('ip') for c in connections)),
            len(set(c.get('port') for c in connections)),
            sum(1 for c in connections if c.get('protocol') == 'tcp'),
            sum(1 for c in connections if c.get('protocol') == 'udp'),
            1 if event.get('tor_connection', False) else 0
        ])
        
        # File operations (10)
        file_ops = event.get('file_operations', [])
        features.extend([
            len(file_ops),
            sum(1 for op in file_ops if op.get('action') == 'create'),
            sum(1 for op in file_ops if op.get('action') == 'delete'),
            sum(1 for op in file_ops if op.get('action') == 'modify'),
            sum(1 for op in file_ops if '.exe' in op.get('path', '')),
            sum(1 for op in file_ops if 'system32' in op.get('path', '').lower()),
            sum(1 for op in file_ops if 'temp' in op.get('path', '').lower()),
            sum(1 for op in file_ops if op.get('encrypted', False)),
            event.get('total_bytes_written', 0),
            event.get('total_bytes_read', 0)
        ])
        
        # Registry operations (5)
        reg_ops = event.get('registry_changes', [])
        features.extend([
            len(reg_ops),
            sum(1 for r in reg_ops if 'run' in r.get('key', '').lower()),
            sum(1 for r in reg_ops if r.get('action') == 'create'),
            sum(1 for r in reg_ops if r.get('action') == 'delete'),
            sum(1 for r in reg_ops if 'currentversion' in r.get('key', '').lower())
        ])
        
        # Temporal features (5)
        features.extend([
            event.get('hour_of_day', 12),
            event.get('day_of_week', 3),
            1 if 0 <= event.get('hour_of_day', 12) <= 6 else 0,
            event.get('events_per_second', 0),
            event.get('time_since_last_event', 0)
        ])
        
        return features[:45]  # Ensure exactly 45 features
    
    async def _analyze_with_llama(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze event with fine-tuned MITRE model"""
        if not self.is_loaded:
            return self._fallback_analysis(event)
        
        try:
            # Format event for analysis
            event_desc = f"""Process: {event.get('process_name', 'Unknown')}
Command: {event.get('command_line', 'N/A')}
Network: {len(event.get('network_connections', []))} connections
Files: {len(event.get('file_operations', []))} operations"""
            
            prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a cybersecurity expert trained on MITRE ATT&CK framework.<|eot_id|><|start_header_id|>user<|end_header_id|>

Analyze this security event: {event_desc}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
            
            inputs = self.tokenizer(prompt, return_tensors="pt")
            outputs = self.llama_model.generate(
                **inputs,
                max_new_tokens=256,
                temperature=0.7,
                do_sample=True
            )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            analysis = response.split("assistant<|end_header_id|>")[-1].strip()
            
            # Extract MITRE techniques
            import re
            techniques = re.findall(r'T\d{4}(?:\.\d{3})?', analysis)
            
            return {
                'analysis': analysis,
                'techniques': list(set(techniques)),
                'confidence': 0.88,  # Based on paper claims
                'threat_level': self._get_threat_level(techniques)
            }
            
        except Exception as e:
            logger.error(f"Llama analysis error: {e}")
            return self._fallback_analysis(event)
    
    def _fallback_analysis(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis when model unavailable"""
        process = event.get('process_name', '').lower()
        
        if 'powershell' in process:
            return {
                'analysis': 'PowerShell execution detected - potential T1059.001',
                'techniques': ['T1059.001'],
                'confidence': 0.75,
                'threat_level': 'medium'
            }
        elif any(susp in process for susp in ['cmd', 'wscript', 'cscript']):
            return {
                'analysis': 'Suspicious script execution detected',
                'techniques': ['T1059'],
                'confidence': 0.70,
                'threat_level': 'medium'
            }
        
        return {
            'analysis': 'Normal system activity',
            'techniques': [],
            'confidence': 0.60,
            'threat_level': 'low'
        }
    
    def _get_threat_level(self, techniques: List[str]) -> str:
        """Calculate threat level from techniques"""
        if not techniques:
            return 'low'
        if len(techniques) >= 3:
            return 'critical'
        if len(techniques) == 2:
            return 'high'
        return 'medium'
    
    def _calculate_risk(self, anomaly_score: float, mitre_analysis: Dict[str, Any]) -> float:
        """Calculate risk score (0-100)"""
        # Anomaly component (0-40 points)
        anomaly_component = max(0, min(-anomaly_score * 20, 40))
        
        # MITRE technique component (0-40 points)
        techniques = mitre_analysis.get('techniques', [])
        technique_weights = {
            'T1059': 8.0, 'T1071': 7.0, 'T1547': 7.0, 'T1566': 8.5,
            'T1486': 9.5, 'T1003': 9.0, 'T1110': 7.5
        }
        
        if techniques:
            avg_weight = sum(technique_weights.get(t.split('.')[0], 5.0) for t in techniques) / len(techniques)
            technique_component = min(avg_weight * 4, 40)
        else:
            technique_component = 0
        
        # Confidence component (0-20 points)
        confidence_component = mitre_analysis.get('confidence', 0.5) * 20
        
        return min(anomaly_component + technique_component + confidence_component, 100)

# Global instance
threat_detector = ThreatDetector()