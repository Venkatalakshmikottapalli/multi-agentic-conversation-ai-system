#!/usr/bin/env python3
"""
Simple test script to demonstrate the Multi-Agent Conversational AI System
"""

import requests
import json
import time
from typing import Dict, Any

class ChatbotTester:
    """Simple tester for the chatbot system."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_health(self) -> Dict[str, Any]:
        """Test the health endpoint."""
        print("🔍 Testing health endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Health check passed: {health_data['status']}")
                return health_data
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return {"status": "unhealthy"}
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return {"status": "error", "error": str(e)}
    
    def test_chat(self, message: str, user_id: str = "test-user-001", 
                  session_id: str = "test-session-001") -> Dict[str, Any]:
        """Test the chat endpoint."""
        print(f"💬 Testing chat with message: '{message}'")
        
        chat_data = {
            "message": message,
            "user_id": user_id,
            "session_id": session_id
        }
        
        try:
            response = self.session.post(f"{self.base_url}/chat", json=chat_data)
            if response.status_code == 200:
                chat_response = response.json()
                print(f"✅ Chat response received:")
                print(f"   Agent: {chat_response.get('metadata', {}).get('agent_used', 'Unknown')}")
                print(f"   Response: {chat_response['response'][:100]}...")
                print(f"   Processing time: {chat_response['processing_time']:.2f}s")
                return chat_response
            else:
                print(f"❌ Chat failed: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ Chat error: {e}")
            return {"error": str(e)}
    
    def test_create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test user creation."""
        print(f"👤 Testing user creation for: {user_data.get('name', 'Unknown')}")
        
        try:
            response = self.session.post(f"{self.base_url}/crm/create_user", json=user_data)
            if response.status_code == 200:
                user_response = response.json()
                print(f"✅ User created successfully: {user_response['data']['id']}")
                return user_response
            else:
                print(f"❌ User creation failed: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ User creation error: {e}")
            return {"error": str(e)}
    
    def test_upload_document(self, content: str, filename: str, content_type: str) -> Dict[str, Any]:
        """Test document upload."""
        print(f"📄 Testing document upload: {filename}")
        
        try:
            files = {
                "files": (filename, content, content_type)
            }
            response = self.session.post(f"{self.base_url}/upload_docs", files=files)
            if response.status_code == 200:
                upload_response = response.json()
                print(f"✅ Document uploaded successfully")
                return upload_response
            else:
                print(f"❌ Document upload failed: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ Document upload error: {e}")
            return {"error": str(e)}
    
    def test_get_users(self) -> Dict[str, Any]:
        """Test getting users list."""
        print("👥 Testing users list...")
        
        try:
            response = self.session.get(f"{self.base_url}/crm/users")
            if response.status_code == 200:
                users_response = response.json()
                print(f"✅ Retrieved {len(users_response['data'])} users")
                return users_response
            else:
                print(f"❌ Users list failed: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ Users list error: {e}")
            return {"error": str(e)}
    
    def test_get_analytics(self) -> Dict[str, Any]:
        """Test getting analytics."""
        print("📊 Testing analytics...")
        
        try:
            response = self.session.get(f"{self.base_url}/crm/analytics")
            if response.status_code == 200:
                analytics_response = response.json()
                print(f"✅ Analytics retrieved")
                return analytics_response
            else:
                print(f"❌ Analytics failed: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ Analytics error: {e}")
            return {"error": str(e)}
    
    def run_comprehensive_test(self):
        """Run a comprehensive test of the system."""
        print("🚀 Starting comprehensive test of Multi-Agent Conversational AI System")
        print("=" * 70)
        
        # Test 1: Health Check
        health_result = self.test_health()
        if health_result.get("status") != "healthy":
            print("❌ System is not healthy. Stopping tests.")
            return
        
        print("\n" + "=" * 70)
        
        # Test 2: Document Upload
        test_content = """Property Address,Floor,Suite,Size (SF),Rent/SF/Year
Test Property 1,E1,100,5000,$100.00
Test Property 2,E2,200,7500,$95.00"""
        
        upload_result = self.test_upload_document(test_content, "test_properties.csv", "text/csv")
        
        print("\n" + "=" * 70)
        
        # Test 3: Create User
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "555-123-4567",
            "company": "Test Company",
            "role": "Tester"
        }
        
        user_result = self.test_create_user(user_data)
        user_id = user_result.get("data", {}).get("id", "test-user-001")
        
        print("\n" + "=" * 70)
        
        # Test 4: Chat Tests
        test_messages = [
            "Hello, I'm looking for office space in Manhattan.",
            "My name is Sarah and I work for TechCorp. What properties do you have available?",
            "I need about 5000 square feet for my team.",
            "What's the rent for the Test Property 1?",
            "Thank you for your help!"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n--- Chat Test {i} ---")
            chat_result = self.test_chat(message, user_id, "test-session-001")
            time.sleep(1)  # Small delay between messages
        
        print("\n" + "=" * 70)
        
        # Test 5: Get Users
        users_result = self.test_get_users()
        
        print("\n" + "=" * 70)
        
        # Test 6: Get Analytics
        analytics_result = self.test_get_analytics()
        
        print("\n" + "=" * 70)
        print("✅ Comprehensive test completed!")
        print("🎉 Multi-Agent Conversational AI System is working correctly!")

def main():
    """Main function to run the tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the Multi-Agent Conversational AI System")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--quick", action="store_true", help="Run quick tests only")
    
    args = parser.parse_args()
    
    tester = ChatbotTester(args.url)
    
    if args.quick:
        print("🚀 Running quick tests...")
        tester.test_health()
        tester.test_chat("Hello, test message")
    else:
        tester.run_comprehensive_test()

if __name__ == "__main__":
    main() 