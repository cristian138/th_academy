#!/usr/bin/env python3
"""
Extended SportsAdmin Backend API Testing Suite
Tests specific endpoints mentioned in the review request
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class ExtendedSportsAdminAPITester:
    def __init__(self, base_url="https://sport-staff-portal.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tokens = {}
        self.tests_run = 0
        self.tests_passed = 0
        self.current_user = None
        
        # Test credentials
        self.test_users = {
            "admin": {"email": "admin@sportsadmin.com", "password": "admin123"},
            "legal": {"email": "legal@sportsadmin.com", "password": "legal123"},
            "collaborator": {"email": "carlos.rodriguez@coach.com", "password": "carlos123"}
        }

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    params: Dict = None, use_token: bool = True) -> tuple[bool, Dict, int]:
        """Make HTTP request to API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'}
        
        if use_token and self.current_user and self.current_user in self.tokens:
            headers['Authorization'] = f'Bearer {self.tokens[self.current_user]}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            else:
                return False, {}, 0
            
            try:
                response_data = response.json()
            except:
                response_data = {"message": response.text}
            
            return response.status_code < 400, response_data, response.status_code
            
        except Exception as e:
            return False, {"error": str(e)}, 0

    def test_login(self, user_type: str) -> bool:
        """Test login for specific user type"""
        if user_type not in self.test_users:
            self.log_test(f"Login {user_type}", False, "Invalid user type")
            return False
        
        credentials = self.test_users[user_type]
        success, data, status = self.make_request('POST', '/auth/login', credentials, use_token=False)
        
        if success and 'access_token' in data:
            self.tokens[user_type] = data['access_token']
            self.current_user = user_type
            user_info = data.get('user', {})
            self.log_test(f"Login {user_type}", True, f"Role: {user_info.get('role', 'N/A')}")
            return True
        else:
            self.log_test(f"Login {user_type}", False, f"Status: {status}, Response: {data}")
            return False

    def test_users_with_role_filter(self):
        """Test GET /api/users with role filter"""
        print("\n🔍 Testing Users API with Role Filters...")
        
        # Test filtering by different roles
        roles_to_test = ["admin", "legal_rep", "collaborator", "accountant"]
        
        for role in roles_to_test:
            success, data, status = self.make_request('GET', '/users', params={'role': role})
            if success and isinstance(data, list):
                filtered_users = [u for u in data if u.get('role') == role]
                all_correct_role = len(filtered_users) == len(data)
                self.log_test(f"Users Filter by {role}", all_correct_role, 
                            f"Found {len(data)} users, all with correct role: {all_correct_role}")
            else:
                self.log_test(f"Users Filter by {role}", False, f"Status: {status}")

    def test_reports_endpoints(self):
        """Test all report endpoints"""
        print("\n📊 Testing Reports Endpoints...")
        
        # Test contracts pending report
        success, data, status = self.make_request('GET', '/reports/contracts-pending')
        if success and 'contracts' in data:
            contracts = data['contracts']
            self.log_test("Reports - Contracts Pending", True, f"Found {len(contracts)} pending contracts")
        else:
            self.log_test("Reports - Contracts Pending", False, f"Status: {status}")
        
        # Test active contracts report
        success, data, status = self.make_request('GET', '/reports/contracts-active')
        if success and 'contracts' in data:
            contracts = data['contracts']
            self.log_test("Reports - Contracts Active", True, f"Found {len(contracts)} active contracts")
        else:
            self.log_test("Reports - Contracts Active", False, f"Status: {status}")
        
        # Test pending payments report (need accountant role)
        success, data, status = self.make_request('GET', '/reports/payments-pending')
        if success and 'payments' in data:
            payments = data['payments']
            self.log_test("Reports - Payments Pending", True, f"Found {len(payments)} pending payments")
        else:
            # This might fail due to role restrictions, which is expected
            self.log_test("Reports - Payments Pending", status == 403, f"Status: {status} (Expected 403 for non-accountant)")

    def test_documents_endpoint(self):
        """Test documents endpoint"""
        print("\n📄 Testing Documents Endpoint...")
        
        success, data, status = self.make_request('GET', '/documents')
        if success and isinstance(data, list):
            self.log_test("Documents List", True, f"Found {len(data)} documents")
            
            # Check document structure
            if len(data) > 0:
                doc = data[0]
                required_fields = ['id', 'document_type', 'status', 'user_id']
                has_required = all(field in doc for field in required_fields)
                self.log_test("Document Structure", has_required, f"Has required fields: {has_required}")
        else:
            self.log_test("Documents List", False, f"Status: {status}")

    def test_payments_endpoint(self):
        """Test payments endpoint"""
        print("\n💰 Testing Payments Endpoint...")
        
        success, data, status = self.make_request('GET', '/payments')
        if success and isinstance(data, list):
            self.log_test("Payments List", True, f"Found {len(data)} payments")
            
            # Check payment structure
            if len(data) > 0:
                payment = data[0]
                required_fields = ['id', 'contract_id', 'amount', 'status']
                has_required = all(field in payment for field in required_fields)
                self.log_test("Payment Structure", has_required, f"Has required fields: {has_required}")
        else:
            self.log_test("Payments List", False, f"Status: {status}")

    def test_contract_creation_flow(self):
        """Test contract creation (legal rep only)"""
        print("\n📝 Testing Contract Creation Flow...")
        
        # First get list of collaborators to use in contract creation
        success, users_data, status = self.make_request('GET', '/users', params={'role': 'collaborator'})
        
        if success and len(users_data) > 0:
            collaborator_id = users_data[0]['id']
            
            # Test contract creation
            contract_data = {
                "collaborator_id": collaborator_id,
                "contract_type": "full_time",
                "title": "Test Contract - API Testing",
                "description": "Contract created during API testing",
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-12-31T23:59:59Z",
                "monthly_payment": 5000000
            }
            
            success, data, status = self.make_request('POST', '/contracts', contract_data)
            if success and 'id' in data:
                contract_id = data['id']
                self.log_test("Contract Creation", True, f"Created contract ID: {contract_id}")
                
                # Test getting the created contract
                success, contract_detail, status = self.make_request('GET', f'/contracts/{contract_id}')
                if success:
                    self.log_test("Contract Retrieval", True, f"Status: {contract_detail.get('status')}")
                else:
                    self.log_test("Contract Retrieval", False, f"Status: {status}")
                    
                return contract_id
            else:
                self.log_test("Contract Creation", False, f"Status: {status}, Response: {data}")
        else:
            self.log_test("Contract Creation", False, "No collaborators found for testing")
        
        return None

    def run_extended_tests(self):
        """Run all extended tests"""
        print("🚀 Starting Extended SportsAdmin API Tests")
        print("=" * 60)
        
        # Login as admin first
        if not self.test_login("admin"):
            print("❌ Admin login failed - cannot continue testing")
            return False
        
        # Test users endpoint with role filtering
        self.test_users_with_role_filter()
        
        # Test reports endpoints
        self.test_reports_endpoints()
        
        # Test documents endpoint
        self.test_documents_endpoint()
        
        # Test payments endpoint  
        self.test_payments_endpoint()
        
        # Login as legal rep for contract creation
        if self.test_login("legal"):
            self.test_contract_creation_flow()
        
        # Login as collaborator to test their view
        if self.test_login("collaborator"):
            print(f"\n👨‍💼 Testing Collaborator-specific endpoints...")
            self.test_documents_endpoint()
            self.test_payments_endpoint()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Extended Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All extended tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    """Main test runner"""
    tester = ExtendedSportsAdminAPITester()
    success = tester.run_extended_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())