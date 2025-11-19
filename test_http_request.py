"""Test script to send HTTP request to ShotGrid MCP server with custom headers."""

import json
import requests

# Server URL
SERVER_URL = "http://localhost:8088/mcp"

# Custom headers with ShotGrid credentials
headers = {
    "Content-Type": "application/json",
    "X-ShotGrid-URL": "https://test.shotgunstudio.com",
    "X-ShotGrid-Script-Name": "test_script",
    "X-ShotGrid-Script-Key": "test_api_key_12345",
    "User-Agent": "TestClient/1.0",
}

# MCP request to list tools
request_data = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
}

print(f"Sending request to {SERVER_URL}")
print(f"Headers: {json.dumps({k: v if k != 'X-ShotGrid-Script-Key' else '***' for k, v in headers.items()}, indent=2)}")
print(f"Request: {json.dumps(request_data, indent=2)}")
print()

try:
    response = requests.post(SERVER_URL, json=request_data, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

