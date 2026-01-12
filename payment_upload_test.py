#!/usr/bin/env python3
"""
SportsAdmin Payment Upload Testing Suite
Tests the complete payment workflow with PDF uploads
"""

import requests
import sys
import json
import os
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional

class PaymentUploadTester:
    def __init__(self, base_url="https://coach-contracts.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tokens = {}
        self.tests_run = 0
        self.tests_passed = 0
        self.current_user = None
        
        # Test credentials
        self.test_users = {
            "collaborator": {"email": "carlos.rodriguez@coach.com", "password": "carlos123"},
            "contador": {"email": "contador@sportsadmin.com", "password": "contador123"}
        }

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

    def create_test_pdf(self, filename: str = "test_bill.pdf") -> str:
        """Create a test PDF file"""
        # Create a simple PDF-like file for testing
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test Payment Bill) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
299
%%EOF"""
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.write(pdf_content)
        temp_file.close()
        
        return temp_file.name

    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    files: Dict = None, use_token: bool = True) -> tuple[bool, Dict, int]:
        """Make HTTP request to API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {}
        
        if use_token and self.current_user and self.current_user in self.tokens:
            headers['Authorization'] = f'Bearer {self.tokens[self.current_user]}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    # Don't set Content-Type for file uploads
                    response = requests.post(url, files=files, headers=headers)
                else:
                    headers['Content-Type'] = 'application/json'
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                headers['Content-Type'] = 'application/json'
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

    def test_create_payment(self, contract_id: str):
        """Test create payment (collaborator creates cuenta de cobro)"""
        payment_data = {
            "contract_id": contract_id,
            "amount": 5000000,
            "payment_date": datetime.now().strftime("%Y-%m-%d"),
            "description": "Pago febrero 2025"
        }
        
        success, data, status = self.make_request('POST', '/payments', payment_data)
        expected = success and 'id' in data and data.get('status') == 'draft'
        details = f"Status: {status}, Payment ID: {data.get('id', 'N/A')}, Payment Status: {data.get('status', 'N/A')}"
        self.log_test("Create Payment (Cuenta de Cobro)", expected, details)
        return expected, data

    def test_upload_bill(self, payment_id: str):
        """Test upload bill PDF"""
        # Create test PDF
        pdf_file_path = self.create_test_pdf("cuenta_cobro.pdf")
        
        try:
            with open(pdf_file_path, 'rb') as f:
                files = {'file': ('cuenta_cobro.pdf', f, 'application/pdf')}
                success, data, status = self.make_request('POST', f'/payments/{payment_id}/upload-bill', files=files)
            
            expected = success and status == 200
            details = f"Status: {status}, Response: {data.get('message', 'N/A')}"
            self.log_test("Upload Bill PDF", expected, details)
            
            return expected, data
            
        finally:
            # Clean up temp file
            if os.path.exists(pdf_file_path):
                os.unlink(pdf_file_path)

    def test_approve_payment(self, payment_id: str):
        """Test approve payment (accountant approves cuenta de cobro)"""
        success, data, status = self.make_request('POST', f'/payments/{payment_id}/approve')
        expected = success and status == 200
        details = f"Status: {status}, Response: {data.get('message', 'N/A')}"
        self.log_test("Approve Payment", expected, details)
        return expected, data

    def test_upload_voucher(self, payment_id: str):
        """Test upload payment voucher (comprobante de pago)"""
        # Create test PDF for voucher
        pdf_file_path = self.create_test_pdf("comprobante_pago.pdf")
        
        try:
            with open(pdf_file_path, 'rb') as f:
                files = {'file': ('comprobante_pago.pdf', f, 'application/pdf')}
                success, data, status = self.make_request('POST', f'/payments/{payment_id}/confirm', files=files)
            
            expected = success and status == 200
            details = f"Status: {status}, Response: {data.get('message', 'N/A')}"
            self.log_test("Upload Voucher PDF", expected, details)
            
            return expected, data
            
        finally:
            # Clean up temp file
            if os.path.exists(pdf_file_path):
                os.unlink(pdf_file_path)

    def test_payment_status(self, payment_id: str, expected_status: str):
        """Test payment status by listing payments and finding the specific one"""
        success, data, status = self.make_request('GET', '/payments')
        
        if success and isinstance(data, list):
            payment = None
            for p in data:
                if p.get('id') == payment_id:
                    payment = p
                    break
            
            if payment:
                actual_status = payment.get('status')
                expected = actual_status == expected_status
                details = f"Expected: {expected_status}, Actual: {actual_status}"
                self.log_test(f"Payment Status Check ({expected_status})", expected, details)
                return expected, payment
            else:
                self.log_test(f"Payment Status Check ({expected_status})", False, "Payment not found")
                return False, None
        else:
            self.log_test(f"Payment Status Check ({expected_status})", False, f"Failed to get payments: {status}")
            return False, None

    def check_storage_directories(self):
        """Check if storage directories exist"""
        storage_path = "/app/storage"
        directories = ['bills', 'vouchers']
        
        for directory in directories:
            dir_path = os.path.join(storage_path, directory)
            exists = os.path.exists(dir_path)
            self.log_test(f"Storage Directory {directory}", exists, f"Path: {dir_path}")
            
            if exists:
                # List files in directory
                try:
                    files = os.listdir(dir_path)
                    print(f"   📁 Files in {directory}: {len(files)} files")
                    if files:
                        print(f"   📄 Latest files: {files[-3:] if len(files) > 3 else files}")
                except Exception as e:
                    print(f"   ❌ Error listing files: {e}")

    def run_complete_payment_flow(self):
        """Run the complete payment flow test"""
        print("🚀 Starting Complete Payment Flow Test")
        print("=" * 60)
        
        # Step 1: Login as collaborator
        print("\n👨‍💼 Step 1: Login as Collaborator (carlos.rodriguez@coach.com)")
        if not self.test_login("collaborator"):
            print("❌ Cannot login as collaborator - stopping test")
            return False
        
        # Step 2: Get contracts
        print("\n📋 Step 2: Get Available Contracts")
        success, contracts, status = self.make_request('GET', '/contracts')
        if not success or not contracts:
            print("❌ Cannot get contracts - stopping test")
            return False
        
        # Find an active contract
        active_contract = None
        for contract in contracts:
            if contract.get('status') in ['active', 'approved']:
                active_contract = contract
                break
        
        if not active_contract:
            print("❌ No active contracts found - stopping test")
            return False
        
        print(f"✅ Using contract: {active_contract.get('title', 'N/A')} (ID: {active_contract.get('id', 'N/A')})")
        
        # Step 3: Create payment
        print("\n💰 Step 3: Create Payment (Cuenta de Cobro)")
        payment_success, payment_data = self.test_create_payment(active_contract['id'])
        if not payment_success:
            print("❌ Cannot create payment - stopping test")
            return False
        
        payment_id = payment_data.get('id')
        print(f"✅ Created payment with ID: {payment_id}")
        
        # Step 4: Verify initial status is DRAFT
        print("\n📊 Step 4: Verify Initial Status (BORRADOR)")
        self.test_payment_status(payment_id, 'draft')
        
        # Step 5: Upload bill PDF
        print("\n📄 Step 5: Upload Bill PDF (CRÍTICO)")
        upload_success, upload_data = self.test_upload_bill(payment_id)
        if not upload_success:
            print("❌ PDF upload failed - this is the critical test!")
            return False
        
        # Step 6: Verify status changed to PENDING_APPROVAL
        print("\n📊 Step 6: Verify Status Changed to PENDIENTE APROBACIÓN")
        self.test_payment_status(payment_id, 'pending_approval')
        
        # Step 7: Login as contador (accountant)
        print("\n💼 Step 7: Login as Contador (contador@sportsadmin.com)")
        if not self.test_login("contador"):
            print("❌ Cannot login as contador - stopping test")
            return False
        
        # Step 8: Find and approve the payment
        print("\n✅ Step 8: Approve Payment")
        approve_success, approve_data = self.test_approve_payment(payment_id)
        if not approve_success:
            print("❌ Cannot approve payment")
            return False
        
        # Step 9: Verify status changed to APPROVED
        print("\n📊 Step 9: Verify Status Changed to APROBADO")
        self.test_payment_status(payment_id, 'approved')
        
        # Step 10: Upload voucher (comprobante de pago)
        print("\n📄 Step 10: Upload Payment Voucher (Comprobante de Pago)")
        voucher_success, voucher_data = self.test_upload_voucher(payment_id)
        if not voucher_success:
            print("❌ Cannot upload voucher")
            return False
        
        # Step 11: Verify final status is PAID
        print("\n📊 Step 11: Verify Final Status (PAGADO)")
        self.test_payment_status(payment_id, 'paid')
        
        # Step 12: Check storage directories
        print("\n📁 Step 12: Check File Storage")
        self.check_storage_directories()
        
        return True

    def run_test(self):
        """Run all tests"""
        success = self.run_complete_payment_flow()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if success and self.tests_passed == self.tests_run:
            print("🎉 Complete Payment Flow Test PASSED!")
            print("✅ PDF upload functionality is working correctly")
            return True
        else:
            print(f"❌ Test FAILED - {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    """Main test runner"""
    tester = PaymentUploadTester()
    success = tester.run_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())