import urllib.request
import json
import uuid

base_url = "http://127.0.0.1:8000/api/v1/auth"
email = f"student_new_{uuid.uuid4().hex[:6]}@example.com"
password = "StudentPassword123!"
full_name = "New Student User"

print(f"1. Testing HTTP Signup for {email}...")
signup_data = json.dumps({
    "email": email,
    "password": password,
    "full_name": full_name
}).encode('utf-8')

req = urllib.request.Request(
    f"{base_url}/signup",
    data=signup_data,
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
        print(f"Signup Response Status: {resp.status}")
        print(f"Success: {res.get('success')}, User ID: {res.get('data', {}).get('user', {}).get('id')}")
except Exception as e:
    print(f"Signup HTTP Error: {e}")

print(f"2. Testing HTTP Login for {email}...")
login_data = json.dumps({
    "email": email,
    "password": password
}).encode('utf-8')

req_login = urllib.request.Request(
    f"{base_url}/login",
    data=login_data,
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req_login) as resp:
        res = json.loads(resp.read().decode())
        print(f"Login Response Status: {resp.status}")
        print(f"Success: {res.get('success')}, Token: {res.get('data', {}).get('access_token')[:20]}...")
except Exception as e:
    print(f"Login HTTP Error: {e}")
