import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import hashlib
import re
from sklearn.feature_extraction.text import TfidfVectorizer
import logging

logger = logging.getLogger(__name__)

class FeatureExtractor:
    """Extract features from security events for anomaly detection"""
    
    def __init__(self):
        self.tfidf = TfidfVectorizer(max_features=100)
        self.categorical_columns = [
            'event_type',
            'source_ip',
            'destination_ip',
            'protocol',
            'severity'
        ]
        self.numerical_columns = [
            'timestamp',
            'duration',
            'bytes_sent',
            'bytes_received',
            'packet_count'
        ]
    
    def _extract_temporal_features(self, timestamp: Union[str, datetime]) -> Dict[str, float]:
        """Extract temporal features from timestamp"""
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        return {
            'hour': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'day_of_month': timestamp.day,
            'month': timestamp.month,
            'is_weekend': 1.0 if timestamp.weekday() >= 5 else 0.0
        }
    
    def _extract_ip_features(self, ip: str) -> Dict[str, float]:
        """Extract features from IP address"""
        if not ip or ip == 'unknown':
            return {
                'is_private': 0.0,
                'is_loopback': 0.0,
                'ip_numeric': 0.0
            }
        
        # Check if private IP
        is_private = 1.0 if (
            ip.startswith('10.') or
            ip.startswith('172.16.') or
            ip.startswith('192.168.')
        ) else 0.0
        
        # Check if loopback
        is_loopback = 1.0 if ip == '127.0.0.1' else 0.0
        
        # Convert IP to numeric
        try:
            ip_numeric = sum(int(x) * (256 ** (3-i)) for i, x in enumerate(ip.split('.')))
        except:
            ip_numeric = 0.0
        
        return {
            'is_private': is_private,
            'is_loopback': is_loopback,
            'ip_numeric': ip_numeric
        }
    
    def _extract_text_features(self, text: str) -> Dict[str, float]:
        """Extract features from text fields"""
        if not text:
            return {
                'text_length': 0.0,
                'word_count': 0.0,
                'special_char_ratio': 0.0
            }
        
        # Basic text statistics
        text_length = len(text)
        word_count = len(text.split())
        
        # Special character ratio
        special_chars = len(re.findall(r'[^a-zA-Z0-9\s]', text))
        special_char_ratio = special_chars / text_length if text_length > 0 else 0.0
        
        return {
            'text_length': float(text_length),
            'word_count': float(word_count),
            'special_char_ratio': special_char_ratio
        }
    
    def _normalize_categorical(self, value: str) -> float:
        """Convert categorical values to numerical using hashing"""
        if not value:
            return 0.0
        return float(int(hashlib.md5(str(value).encode()).hexdigest(), 16) % 1000) / 1000.0
    
    def extract_features(self, events_data: List[Dict[str, Any]]) -> np.ndarray:
        """Extract features from a list of security events"""
        try:
            features = []
            
            for event in events_data:
                event_features = []
                
                # Extract temporal features
                if 'timestamp' in event:
                    temporal_features = self._extract_temporal_features(event['timestamp'])
                    event_features.extend(temporal_features.values())
                
                # Extract IP features
                for ip_field in ['source_ip', 'destination_ip']:
                    if ip_field in event:
                        ip_features = self._extract_ip_features(event[ip_field])
                        event_features.extend(ip_features.values())
                
                # Extract text features from relevant fields
                for text_field in ['message', 'description']:
                    if text_field in event:
                        text_features = self._extract_text_features(event[text_field])
                        event_features.extend(text_features.values())
                
                # Handle categorical features
                for cat_field in self.categorical_columns:
                    if cat_field in event:
                        event_features.append(self._normalize_categorical(event[cat_field]))
                
                # Handle numerical features
                for num_field in self.numerical_columns:
                    if num_field in event:
                        try:
                            value = float(event[num_field])
                        except (ValueError, TypeError):
                            value = 0.0
                        event_features.append(value)
                
                features.append(event_features)
            
            # Convert to numpy array
            features_array = np.array(features)
            
            # Handle missing values
            features_array = np.nan_to_num(features_array, nan=0.0)
            
            return features_array
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            raise
