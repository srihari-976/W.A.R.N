#!/usr/bin/env python3
"""
Test W.A.R.N Frontend-Backend Connectivity
Tests all API endpoints and data flow
"""
import requests
import json
import time

API_BASE = "http://localhost:5000"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"✅ Health: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health failed: {e}")
        return False

def test_alerts():
    """Test alerts endpoint"""
    try:
        response = requests.get(f"{API_BASE}/api/alerts/")
        print(f"✅ Alerts: {response.status_code}")
        data = response.json()
        print(f"   Found {len(data.get('alerts', []))} alerts")
        return True
    except Exception as e:
        print(f"❌ Alerts failed: {e}")
        return False

def test_risk_scores():
    """Test risk scores endpoint"""
    try:
        response = requests.get(f"{API_BASE}/api/risk/scores")
        print(f"✅ Risk Scores: {response.status_code}")
        data = response.json()
        print(f"   Average risk: {data.get('average_score', 0):.1f}%")
        return True
    except Exception as e:
        print(f"❌ Risk Scores failed: {e}")
        return False

def test_event_creation():
    """Test creating a security event"""
    try:
        event_data = {
            "event_type": "process_creation",
            "source": "test_agent",
            "severity": "high",
            "description": "Test PowerShell execution",
            "process_name": "powershell.exe",
            "command_line": "powershell -EncodedCommand <test>",
            "network_connections": [{"ip": "192.168.1.100", "port": 443, "external": True}]
        }
        
        response = requests.post(f"{API_BASE}/api/events/", json=event_data)
        print(f"✅ Event Creation: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            detection = data.get('detection_result', {})
            print(f"   Risk Score: {detection.get('risk_score', 0)}%")
            print(f"   Techniques: {detection.get('mitre_techniques', [])}")
            print(f"   Threat Level: {detection.get('threat_level', 'unknown')}")
        
        return True
    except Exception as e:
        print(f"❌ Event Creation failed: {e}")
        return False

def main():
    """Run all connectivity tests"""
    print("🔍 Testing W.A.R.N Frontend-Backend Connectivity\n")
    
    tests = [
        ("Backend Health", test_health),
        ("Alerts API", test_alerts),
        ("Risk Scores API", test_risk_scores),
        ("Event Processing", test_event_creation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}:")
        if test_func():
            passed += 1
        time.sleep(1)
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All systems operational - Frontend can connect to backend!")
        print("\n🚀 Start frontend with: cd frontend && npm start")
    else:
        print("❌ Some tests failed - check backend is running")
        print("\n🔧 Start backend with: cd server && python app.py")

if __name__ == "__main__":
    main()