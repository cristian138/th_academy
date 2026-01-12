#!/usr/bin/env python3
"""
SportsAdmin Backend API Testing Suite
Tests all major API endpoints and workflows
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class SportsAdminAPITester:
    def __init__(self, base_url="https://coach-contracts.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tokens = {}  # Store tokens for different users
        self.tests_run = 0
        self.tests_passed = 0
        self.current_user = None
        
        # Test credentials
        self.test_users = {
            "admin": {"email": "admin@sportsadmin.com", "password": "admin123"},
            "legal": {"email": "legal@sportsadmin.com", "password": "legal123"},
            "contador": {"email": "contador@sportsadmin.com", "password": "contador123"},
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
                    files: Dict = None, use_token: bool = True) -> tuple[bool, Dict, int]:
        """Make HTTP request to API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'}
        
        if use_token and self.current_user and self.current_user in self.tokens:
            headers['Authorization'] = f'Bearer {self.tokens[self.current_user]}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    # Remove Content-Type for file uploads
                    headers.pop('Content-Type', None)
                    response = requests.post(url, files=files, headers=headers)
                else:
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

    def test_health_check(self):
        """Test health check endpoint"""
        success, data, status = self.make_request('GET', '/health', use_token=False)
        expected = success and status == 200 and data.get('status') == 'healthy'
        self.log_test("Health Check", expected, f"Status: {status}")
        return expected

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

    def test_get_me(self):
        """Test get current user info"""
        success, data, status = self.make_request('GET', '/auth/me')
        expected = success and 'email' in data
        self.log_test("Get Current User", expected, f"Email: {data.get('email', 'N/A')}")
        return expected

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        success, data, status = self.make_request('GET', '/dashboard/stats')
        expected = success and 'total_contracts' in data
        details = f"Contracts: {data.get('total_contracts', 0)}, Active: {data.get('active_contracts', 0)}"
        self.log_test("Dashboard Stats", expected, details)
        return expected, data

    def test_list_contracts(self):
        """Test list contracts"""
        success, data, status = self.make_request('GET', '/contracts')
        expected = success and isinstance(data, list)
        self.log_test("List Contracts", expected, f"Found {len(data) if isinstance(data, list) else 0} contracts")
        return expected, data

    def test_contract_detail(self, contract_id: str):
        """Test get contract detail"""
        success, data, status = self.make_request('GET', f'/contracts/{contract_id}')
        expected = success and 'id' in data
        self.log_test("Contract Detail", expected, f"Status: {data.get('status', 'N/A')}")
        return expected, data

    def test_list_users(self):
        """Test list users (admin only)"""
        success, data, status = self.make_request('GET', '/users')
        expected = success and isinstance(data, list)
        self.log_test("List Users", expected, f"Found {len(data) if isinstance(data, list) else 0} users")
        return expected, data

    def test_notifications(self):
        """Test get notifications"""
        success, data, status = self.make_request('GET', '/notifications')
        expected = success and isinstance(data, list)
        self.log_test("Get Notifications", expected, f"Found {len(data) if isinstance(data, list) else 0} notifications")
        return expected, data

    def test_list_payments(self):
        """Test list payments"""
        success, data, status = self.make_request('GET', '/payments')
        expected = success and isinstance(data, list)
        self.log_test("List Payments", expected, f"Found {len(data) if isinstance(data, list) else 0} payments")
        return expected, data

    def test_create_payment(self, contract_id: str):
        """Test create payment (accountant only)"""
        payment_data = {
            "contract_id": contract_id,
            "amount": 3500000,
            "payment_date": datetime.now().strftime("%Y-%m-%d"),
            "description": "Pago de prueba E2E"
        }
        
        success, data, status = self.make_request('POST', '/payments', payment_data)
        expected = success and 'id' in data and data.get('status') == 'pending_bill'
        details = f"Status: {status}, Payment ID: {data.get('id', 'N/A')}"
        self.log_test("Create Payment", expected, details)
        return expected, data

    def test_payment_workflow(self):
        """Test payment creation workflow"""
        print("\n💰 Testing Payment Workflow...")
        
        # First login as contador (accountant)
        if not self.test_login("contador"):
            print("❌ Cannot login as contador - skipping payment tests")
            return False
        
        # Get active contracts
        success, contracts = self.test_list_contracts()
        if not success:
            print("❌ Cannot get contracts - skipping payment tests")
            return False
        
        # Find an active contract
        active_contract = None
        for contract in contracts:
            if contract.get('status') == 'active':
                active_contract = contract
                break
        
        if not active_contract:
            print("⚠️  No active contracts found - cannot test payment creation")
            return True  # Not a failure, just no data to test with
        
        print(f"📋 Using active contract: {active_contract.get('title', 'N/A')}")
        
        # Test create payment
        payment_success, payment_data = self.test_create_payment(active_contract['id'])
        
        if payment_success:
            # Test list payments to verify it appears
            list_success, payments = self.test_list_payments()
            if list_success:
                # Check if our payment is in the list
                created_payment = None
                for payment in payments:
                    if payment.get('id') == payment_data.get('id'):
                        created_payment = payment
                        break
                
                if created_payment:
                    self.log_test("Payment in List", True, f"Amount: ${created_payment.get('amount', 0)}")
                else:
                    self.log_test("Payment in List", False, "Created payment not found in list")
        
        # Test as collaborator - should NOT be able to create payments
        if self.test_login("collaborator"):
            print("\n👨‍💼 Testing Payment Access as Collaborator...")
            
            # Try to create payment (should fail)
            payment_data = {
                "contract_id": active_contract['id'],
                "amount": 1000000,
                "payment_date": datetime.now().strftime("%Y-%m-%d"),
                "description": "Should fail"
            }
            
            success, data, status = self.make_request('POST', '/payments', payment_data)
            # Should fail with 403 Forbidden
            expected_fail = not success and status == 403
            self.log_test("Collaborator Create Payment (Should Fail)", expected_fail, f"Status: {status}")
            
            # But should be able to list payments
            list_success, payments = self.test_list_payments()
            self.log_test("Collaborator List Payments", list_success, f"Found {len(payments) if isinstance(payments, list) else 0} payments")
        
        return payment_success

    def test_contract_workflow(self):
        """Test contract approval workflow"""
        print("\n🔄 Testing Contract Workflow...")
        
        # First login as admin to find contracts under review
        if not self.test_login("admin"):
            return False
        
        success, contracts = self.test_list_contracts()
        if not success:
            return False
        
        # Find a contract under review
        under_review_contract = None
        for contract in contracts:
            if contract.get('status') == 'under_review':
                under_review_contract = contract
                break
        
        if under_review_contract:
            print(f"📋 Found contract under review: {under_review_contract.get('title', 'N/A')}")
            
            # Test review contract (admin sends for approval)
            success, data, status = self.make_request('POST', f"/contracts/{under_review_contract['id']}/review")
            self.log_test("Review Contract (Admin)", success, f"Status: {status}")
            
            if success:
                # Now login as legal rep and approve
                if self.test_login("legal"):
                    success, data, status = self.make_request('POST', f"/contracts/{under_review_contract['id']}/approve")
                    self.log_test("Approve Contract (Legal)", success, f"Status: {status}")
                    return success
        else:
            print("⚠️  No contracts under review found for workflow testing")
            return True  # Not a failure, just no data to test with

    def run_comprehensive_test(self):
        """Run all tests"""
        print("🚀 Starting SportsAdmin API Tests")
        print("=" * 50)
        
        # Basic connectivity
        if not self.test_health_check():
            print("❌ Health check failed - API may be down")
            return False
        
        print("\n🔐 Testing Authentication...")
        
        # Test login for all user types
        login_results = {}
        for user_type in self.test_users.keys():
            login_results[user_type] = self.test_login(user_type)
        
        if not any(login_results.values()):
            print("❌ All logins failed - cannot continue testing")
            return False
        
        # Test with admin user
        if login_results.get("admin"):
            self.current_user = "admin"
            print(f"\n👤 Testing as Admin User...")
            
            self.test_get_me()
            stats_success, stats_data = self.test_dashboard_stats()
            contracts_success, contracts_data = self.test_list_contracts()
            self.test_list_users()
            self.test_notifications()
            
            # Test contract details if we have contracts
            if contracts_success and contracts_data:
                if len(contracts_data) > 0:
                    first_contract = contracts_data[0]
                    self.test_contract_detail(first_contract['id'])
        
        # Test with legal rep
        if login_results.get("legal"):
            self.current_user = "legal"
            print(f"\n⚖️  Testing as Legal Representative...")
            
            self.test_get_me()
            self.test_dashboard_stats()
            self.test_list_contracts()
            self.test_notifications()
        
        # Test with contador (accountant)
        if login_results.get("contador"):
            self.current_user = "contador"
            print(f"\n💰 Testing as Accountant (Contador)...")
            
            self.test_get_me()
            self.test_dashboard_stats()
            self.test_list_contracts()
            self.test_list_payments()
            self.test_notifications()
        
        # Test payment workflow if contador login worked
        if login_results.get("contador"):
            self.current_user = "contador"
            self.test_payment_workflow()
        
        # Test with collaborator
        if login_results.get("collaborator"):
            self.current_user = "collaborator"
            print(f"\n👨‍💼 Testing as Collaborator...")
            
            self.test_get_me()
            self.test_dashboard_stats()
            self.test_list_contracts()
            self.test_notifications()
        
        # Test workflow if admin login worked
        if login_results.get("admin"):
            self.current_user = "admin"
            self.test_contract_workflow()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    """Main test runner"""
    tester = SportsAdminAPITester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())