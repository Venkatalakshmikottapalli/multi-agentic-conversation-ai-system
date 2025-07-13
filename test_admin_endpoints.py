#!/usr/bin/env python3
"""
Test script for admin endpoints
"""

import requests
import json
from datetime import datetime

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint, method="GET", data=None):
    """Test a single endpoint and return the response."""
    url = f"{BASE_URL}{endpoint}"
    
    print(f"\n{'='*60}")
    print(f"Testing {method} {endpoint}")
    print(f"{'='*60}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        else:
            print(f"Unsupported method: {method}")
            return
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success', False)}")
            print(f"Message: {result.get('message', 'No message')}")
            
            # Print data in a readable format
            if 'data' in result and result['data']:
                print("Data:")
                print(json.dumps(result['data'], indent=2, default=str))
            
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to the server. Make sure the server is running.")
    except Exception as e:
        print(f"ERROR: {e}")

def main():
    """Test all admin endpoints."""
    print("Testing Admin Endpoints")
    print("Make sure the server is running on http://localhost:8000")
    
    # Test system analytics
    test_endpoint("/admin/analytics/system")
    
    # Test analytics overview
    test_endpoint("/admin/analytics/overview")
    
    # Test system settings
    test_endpoint("/admin/settings")
    
    # Test system overview
    test_endpoint("/admin/overview")
    
    # Test detailed health
    test_endpoint("/admin/health/detailed")
    
    # Test settings update
    settings_update = {
        "category": "ai",
        "settings": {
            "temperature": 0.8,
            "max_tokens": 1200
        }
    }
    test_endpoint("/admin/settings", method="PUT", data=settings_update)
    
    # Test settings again to see if update worked
    test_endpoint("/admin/settings")
    
    # Test basic health endpoint for comparison
    test_endpoint("/health")
    
    # Test root endpoint to see new admin endpoints listed
    test_endpoint("/")
    
    print(f"\n{'='*60}")
    print("Testing completed!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main() 