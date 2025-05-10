import os
import logging
from typing import Dict, List, Any, Optional, Union
import requests
import json
from datetime import datetime
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import numpy as np

logger = logging.getLogger(__name__)

class LLaMAClient:
    """Client for interacting with LLaMA model for security analysis"""
    
    def __init__(self, model_name: str = "meta-llama/Llama-2-7b-chat-hf"):
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = None
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the LLaMA model and tokenizer"""
        try:
            logger.info(f"Initializing LLaMA model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto"
            )
            logger.info("LLaMA model initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing LLaMA model: {e}")
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
    
    def analyze_security_event(self, security_event: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a security event using LLaMA model"""
        try:
            # Prepare prompt
            prompt = self._prepare_prompt(security_event)
            
            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=512,
                    num_return_sequences=1,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract analysis from response
            analysis = response.split("Analysis:")[-1].strip()
            
            # Parse analysis into structured format
            sections = analysis.split("\n\n")
            structured_analysis = {
                "threat_assessment": sections[0] if len(sections) > 0 else "",
                "recommended_actions": sections[1] if len(sections) > 1 else "",
                "known_patterns": sections[2] if len(sections) > 2 else "",
                "risk_level": sections[3] if len(sections) > 3 else "",
                "raw_analysis": analysis
            }
            
            return structured_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing security event: {e}")
            return {
                "error": str(e),
                "threat_assessment": "Error in analysis",
                "recommended_actions": "Unable to generate recommendations",
                "known_patterns": "Unable to identify patterns",
                "risk_level": "Unknown",
                "raw_analysis": ""
            }
    
    def batch_analyze_events(self, security_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze multiple security events in batch"""
        try:
            results = []
            for event in security_events:
                analysis = self.analyze_security_event(event)
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
            "model_name": self.model_name,
            "device": self.device,
            "model_parameters": sum(p.numel() for p in self.model.parameters()),
            "model_layers": len(self.model.model.layers),
            "vocab_size": self.tokenizer.vocab_size
        }