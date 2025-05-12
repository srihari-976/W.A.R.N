import requests
import time
import json

def simulate_instagram_attack():
    print("Starting Instagram-like brute force simulation...")
    base_url = "http://localhost:5001/api/security/log-attempt"
    username = "instagram_user@example.com"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Simulate 6 failed login attempts
    for attempt in range(1, 7):
        data = {
            "ip": "192.168.1.100",
            "username": username,
            "password": f"wrongpass{attempt}",
            "success": False,
            "source": "instagram_login",
            "details": {
                "browser": "Chrome",
                "platform": "Windows",
                "attempt_number": attempt
            }
        }
        
        print(f"\nAttempt {attempt}/6:")
        print(f"Username: {username}")
        print(f"Password: wrongpass{attempt}")
        
        try:
            response = requests.post(base_url, json=data)
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            # If we get a 403 (Forbidden), it means brute force was detected
            if response.status_code == 403:
                print("\n🚨 Brute force attack detected!")
                print("Check your frontend for the alert!")
            
            # Wait 2 seconds between attempts
            time.sleep(2)
            
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {e}")
            break
    
    # Check final security status
    try:
        status_response = requests.get("http://localhost:5001/api/security/status")
        print("\nFinal Security Status:")
        print(json.dumps(status_response.json(), indent=2))
    except requests.exceptions.RequestException as e:
        print(f"Error checking status: {e}")

if __name__ == "__main__":
    simulate_instagram_attack() 