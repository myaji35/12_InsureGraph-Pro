#!/usr/bin/env python3
"""
Test query-simple endpoint with authentication
"""
import requests
import json

# Step 1: Login
print("🔐 Logging in...")
login_response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={
        "email": "admin@insuregraph.com",
        "password": "Admin123!"
    }
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.text}")
    exit(1)

token = login_response.json()["access_token"]
print(f"✅ Login successful, token: {token[:20]}...")

# Step 2: Test query endpoint
print("\n🔍 Testing query endpoint...")
query_response = requests.post(
    "http://localhost:8000/api/v1/query-simple/execute",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    },
    json={
        "query": "삼성화재 자동차보험 보장 내용은?",
        "limit": 10,
        "use_traversal": True,
        "llm_provider": "anthropic"
    }
)

print(f"\n📊 Response Status: {query_response.status_code}")
print(f"📄 Response Body:")
print(json.dumps(query_response.json(), indent=2, ensure_ascii=False))
