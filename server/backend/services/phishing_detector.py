import re
import requests
import asyncio
from urllib.parse import urlparse
from typing import Dict, List
import tldextract

class PhishingDetector:
    def __init__(self):
        self.safe_browsing_api_key = None  # Set in production
        
    async def scan_url(self, url: str) -> Dict:
        """Comprehensive phishing URL detection"""
        results = {
            'url': url,
            'is_phishing': False,
            'confidence': 0.0,
            'threat_indicators': [],
            'risk_level': 'low'
        }
        
        # Extract URL features
        features = self._extract_url_features(url)
        
        # Heuristic analysis
        heuristic_score = self._heuristic_analysis(url, features)
        results['heuristic_score'] = heuristic_score
        
        if heuristic_score >= 5:
            results['threat_indicators'].append(f'Heuristic score: {heuristic_score}/10')
        
        # Calculate final risk
        total_score = 0
        if heuristic_score >= 5:
            total_score += 3
        
        results['is_phishing'] = total_score >= 3
        results['confidence'] = min(total_score / 10.0, 1.0)
        
        # Risk classification
        if total_score >= 7:
            results['risk_level'] = 'critical'
        elif total_score >= 5:
            results['risk_level'] = 'high'
        elif total_score >= 3:
            results['risk_level'] = 'medium'
        else:
            results['risk_level'] = 'low'
        
        return results
    
    def _extract_url_features(self, url: str) -> Dict:
        """Extract features from URL for analysis"""
        parsed = urlparse(url)
        extracted = tldextract.extract(url)
        
        return {
            'url_length': len(url),
            'domain_length': len(parsed.netloc),
            'dots_count': url.count('.'),
            'hyphens_count': url.count('-'),
            'has_https': 1 if 'https' in url else 0,
            'is_ip': 1 if self._is_ip(parsed.netloc) else 0,
            'suspicious_keywords': 1 if any(x in url.lower() for x in ['login', 'signin', 'verify', 'secure', 'update']) else 0,
            'brand_impersonation': 1 if any(x in url.lower() for x in ['paypal', 'amazon', 'bank', 'microsoft', 'google']) else 0,
            'suspicious_tld': 1 if extracted.suffix in ['tk', 'ml', 'ga', 'cf', 'gq'] else 0,
            'url_shortener': 1 if any(x in url.lower() for x in ['bit.ly', 'tinyurl', 't.co']) else 0
        }
    
    def _is_ip(self, domain: str) -> bool:
        """Check if domain is an IP address"""
        import socket
        try:
            socket.inet_aton(domain)
            return True
        except:
            return False
    
    def _heuristic_analysis(self, url: str, features: Dict) -> int:
        """Rule-based heuristic scoring (0-10)"""
        score = 0
        
        if features['url_length'] > 100:
            score += 1
        if features['is_ip']:
            score += 2
        if features['suspicious_keywords']:
            score += 1
        if not features['has_https'] and 'login' in url.lower():
            score += 2
        if features['brand_impersonation']:
            score += 2
        if features['url_shortener']:
            score += 1
        if features['suspicious_tld']:
            score += 1
        
        return min(score, 10)