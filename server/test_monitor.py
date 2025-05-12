import requests
import time
import json

# Configuration
BASE_URL = 'http://localhost:5001'  # Updated port

def test_login_attempt(username, success=False):
    url = f'{BASE_URL}/api/security/log-attempt'
    data = {
        'username': username,
        'success': success
    }
    try:
        print(f"Sending request to {url}")
        print(f"Data: {json.dumps(data, indent=2)}")
        response = requests.post(url, json=data)
        print(f"Status code: {response.status_code}")
        try:
            print(f"Response: {response.json()}")
        except:
            print(f"Raw response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

def simulate_brute_force():
    print("\n=== Simulating brute force attack ===")
    for i in range(6):  # 6 attempts to trigger alert (threshold is 5)
        print(f"\nAttempt {i+1}/6:")
        test_login_attempt("admin")
        time.sleep(1)  # Wait 1 second between attempts

def test_service():
    print("\n=== Testing monitoring service ===")
    try:
        url = f'{BASE_URL}/api/security/test'
        print(f"Sending GET request to {url}")
        response = requests.get(url)
        print(f"Status code: {response.status_code}")
        try:
            print(f"Response: {response.json()}")
            return True
        except:
            print(f"Raw response: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("Connection error: Make sure the monitoring service is running")
        return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False

def check_status():
    print("\n=== Checking monitor status ===")
    try:
        url = f'{BASE_URL}/api/security/status'
        print(f"Sending GET request to {url}")
        response = requests.get(url)
        print(f"Status code: {response.status_code}")
        try:
            status = response.json()
            print("Current status:")
            print(json.dumps(status, indent=2))
            return True
        except:
            print(f"Raw response: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("Connection error: Make sure the monitoring service is running")
        return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting brute force simulation test...")
    print(f"Make sure agent_bruteforce_monitor.py is running on port 5001!")
    
    # Test the service first
    if not test_service():
        print("\nFailed to connect to monitoring service!")
        print("Please ensure agent_bruteforce_monitor.py is running")
        exit(1)

    # Initial status check
    check_status()
    
    # Run the simulation
    simulate_brute_force()
    
    # Final status check
    print("\n=== Final Status ===")
    check_status() 