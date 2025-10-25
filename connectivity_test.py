#!/usr/bin/env python3
"""
W.A.R.N Frontend-Backend Connectivity Test
Tests all API endpoints that the frontend uses
"""

import requests
import json
from datetime import datetime

API_BASE = "http://localhost:5000"

def test_endpoint(endpoint, method="GET", data=None):
    """Test a single API endpoint"""
    url = f"{API_BASE}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        
        return {
            'endpoint': endpoint,
            'status': response.status_code,
            'success': response.status_code < 400,
            'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            'error': None
        }
    except requests.exceptions.ConnectionError:
        return {
            'endpoint': endpoint,
            'status': None,
            'success': False,
            'data': None,
            'error': 'Connection refused - Backend not running'
        }
    except Exception as e:
        return {
            'endpoint': endpoint,
            'status': None,
            'success': False,
            'data': None,
            'error': str(e)
        }

def main():
    print("W.A.R.N Frontend-Backend Connectivity Test")
    print("=" * 50)
    
    # Test endpoints that frontend uses
    endpoints = [
        "/",                    # Root endpoint
        "/health",              # Health check
        "/api/alerts/",         # Alerts (main dashboard data)
        "/api/risk/scores",     # Risk scores (main dashboard data)
        "/api/risk/factors",    # Risk factors
        "/api/events/",         # Events (requires auth)
    ]
    
    results = []
    
    for endpoint in endpoints:
        print(f"Testing {endpoint}...")
        result = test_endpoint(endpoint)
        results.append(result)
        
        if result['success']:
            print(f"  SUCCESS ({result['status']})")
            if endpoint in ["/api/alerts/", "/api/risk/scores"]:
                # Check data structure for critical endpoints
                data = result['data']
                if endpoint == "/api/alerts/" and 'alerts' in data:
                    print(f"    Found {len(data['alerts'])} alerts")
                elif endpoint == "/api/risk/scores" and 'risk_scores' in data:
                    print(f"    Found {len(data['risk_scores'])} risk scores")
                    print(f"    Average score: {data.get('average_score', 0):.1f}%")
        else:
            print(f"  FAILED: {result['error'] or ('HTTP ' + str(result['status']))}")
    
    print("\n" + "=" * 50)
    print("CONNECTIVITY SUMMARY")
    print("=" * 50)
    
    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    
    print(f"Successful endpoints: {success_count}/{total_count}")
    
    # Critical endpoints for dashboard
    critical_endpoints = ["/api/alerts/", "/api/risk/scores", "/health"]
    critical_results = [r for r in results if r['endpoint'] in critical_endpoints]
    critical_success = sum(1 for r in critical_results if r['success'])
    
    print(f"Critical dashboard endpoints: {critical_success}/{len(critical_results)}")
    
    if critical_success == len(critical_results):
        print("DASHBOARD CONNECTIVITY: FULLY OPERATIONAL")
    else:
        print("DASHBOARD CONNECTIVITY: ISSUES DETECTED")
        print("\nFailed critical endpoints:")
        for r in critical_results:
            if not r['success']:
                print(f"  - {r['endpoint']}: {r['error']}")
    
    # Check for missing data issues
    print("\nDATA AVAILABILITY CHECK")
    alerts_result = next((r for r in results if r['endpoint'] == '/api/alerts/'), None)
    risk_result = next((r for r in results if r['endpoint'] == '/api/risk/scores'), None)
    
    if alerts_result and alerts_result['success']:
        alerts_data = alerts_result['data'].get('alerts', [])
        if len(alerts_data) == 0:
            print("WARNING: No alerts found - Dashboard will show 'No alerts - System secure'")
        else:
            print(f"{len(alerts_data)} alerts available for dashboard")
    
    if risk_result and risk_result['success']:
        risk_data = risk_result['data'].get('risk_scores', [])
        if len(risk_data) == 0:
            print("WARNING: No risk scores found - Charts will be empty")
        else:
            print(f"{len(risk_data)} risk scores available for charts")
    
    print(f"\nTest completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()