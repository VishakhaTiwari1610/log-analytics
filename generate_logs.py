import requests
import time
import random
import json

BASE_URL = "http://localhost:8000/api/v1"
session = requests.Session()
token = None

def login_correct():
    global token
    try:
        response = session.post(f"{BASE_URL}/user/login", json={
            "email": "anisha123@gmail.com",
            "password": "anisha123",
            "role": "recruiter"  # ADD THIS - must match the account's role
        })
        if response.status_code == 200:
            # Manually set the cookie from response headers
            set_cookie = response.headers.get("Set-Cookie", "")
            if "token=" in set_cookie:
                token_value = set_cookie.split("token=")[1].split(";")[0]
                session.cookies.set("token", token_value, domain="localhost")
                print(f"Correct login: 200, token stored")
            else:
                print("Login 200 but no token in response")
        else:
            print(f"Correct login failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Login failed: {e}")

def login_wrong():
    try:
        response = session.post(f"{BASE_URL}/user/login", json={
            "email": "anisha123@gmail.com",
            "password": "wrongpassword123",
            "role":"recruiter"
        })
        print(f"Login attempt: {response.status_code}")
    except Exception as e:
        print(f"Login failed: {e}")

def get_jobs():
    try:
        cookies = {"token": token} if token else {}
        response = session.get(f"{BASE_URL}/jobs/get", cookies=cookies)
        print(f"Get jobs: {response.status_code}")
    except Exception as e:
        print(f"Get jobs failed: {e}")

def get_job_by_invalid_id():
    try:
        cookies = {"token": token} if token else {}
        response = session.get(
            f"{BASE_URL}/jobs/get/invalidid123",
            cookies=cookies
        )
        print(f"Invalid job ID: {response.status_code}")
    except Exception as e:
        print(f"Request failed: {e}")

def simulate_normal_traffic():
    print("\n--- Simulating normal traffic ---")
    for i in range(20):
        get_jobs()
        time.sleep(0.5)

def simulate_error_spike():
    print("\n--- Simulating error spike ---")
    for i in range(15):
        login_wrong()
        time.sleep(0.2)

def simulate_mixed_traffic():
    print("\n--- Simulating mixed traffic ---")
    actions = [get_jobs, login_wrong, get_job_by_invalid_id]
    for i in range(30):
        action = random.choice(actions)
        action()
        time.sleep(random.uniform(0.3, 0.8))

if __name__ == "__main__":
    print("Starting data generation...")
    
    login_correct()
    time.sleep(1)
    
    simulate_normal_traffic()
    time.sleep(2)
    
    simulate_error_spike()
    time.sleep(2)
    
    simulate_mixed_traffic()
    
    print("\nData generation complete.")