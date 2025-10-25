#!/usr/bin/env python3
"""
W.A.R.N Security Features Test Script
Tests phishing detection, brute force protection, and IP blocking
"""

import requests
import time
import json

API_BASE = "http://localhost:5000/api"

def test_phishing_detection():
    """Test phishing URL detection"""
    print("🔍 Testing Phishing Detection...")
    
    test_urls = [
        "https://google.com",  # Safe
        "http://phishing-example.com/fake-bank",  # Suspicious
        "https://paypal-security-update.tk/login",  # Phishing indicators
        "http://192.168.1.1/admin"  # IP-based suspicious
    ]
    
    for url in test_urls:
        try:
            response = requests.post(f"{API_BASE}/security/scan-url", 
                                   json={"url": url})
            result = response.json()
            
            print(f"  URL: {url}")
            print(f"  Risk: {result.get('risk_level', 'unknown')}")
            print(f"  Phishing: {result.get('is_phishing', False)}")
            print(f"  Confidence: {result.get('confidence', 0)*100:.1f}%")
            print()
            
        except Exception as e:
            print(f"  Error testing {url}: {e}")

def test_brute_force_protection():
    """Test Instagram-style brute force protection"""
    print("🔒 Testing Brute Force Protection...")
    
    # Simulate 3 failed login attempts
    for attempt in range(1, 4):
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                "username": "test_user",
                "password": f"wrong_password_{attempt}",
                "ip_address": "192.168.1.100"
            })
            
            result = response.json()
            print(f"  Attempt {attempt}:")
            print(f"    Risk Level: {result.get('risk_level', 'unknown')}")
            print(f"    Action: {result.get('action', 'none')}")
            print(f"    Message: {result.get('message', 'No message')}")
            print()
            
            time.sleep(1)  # Brief delay between attempts
            
        except Exception as e:
            print(f"  Error on attempt {attempt}: {e}")

def test_security_status():
    """Check security system status"""
    print("📊 Checking Security Status...")
    
    try:
        # Check blocked IPs
        response = requests.get(f"{API_BASE}/security/blocked-ips")
        blocked_ips = response.json()
        print(f"  Blocked IPs: {blocked_ips.get('count', 0)}")
        
        # Check locked accounts
        response = requests.get(f"{API_BASE}/security/locked-accounts")
        locked_accounts = response.json()
        print(f"  Locked Accounts: {locked_accounts.get('count', 0)}")
        
        # Check brute force status
        response = requests.get(f"{API_BASE}/auth/brute-force-status")
        bf_status = response.json()
        print(f"  Protection Active: {bf_status.get('protection_active', False)}")
        print(f"  Max Attempts: {bf_status.get('max_attempts', 0)}")
        
    except Exception as e:
        print(f"  Error checking status: {e}")

def main():
    print("🛡️ W.A.R.N Security Features Test")
    print("=" * 50)
    
    # Test if backend is running
    try:
        response = requests.get(f"http://localhost:5000/health")
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print("❌ Backend not responding properly")
            return
    except:
        print("❌ Backend not running. Please start with: python server/backend/app.py")
        return
    
    print()
    
    # Run tests
    test_phishing_detection()
    test_brute_force_protection()
    test_security_status()
    
    print("🎯 Test completed! Check the results above.")
    print("💡 Try the Instagram login demo at: http://localhost:3000/instagram_login.html")

if __name__ == "__main__":
    main()