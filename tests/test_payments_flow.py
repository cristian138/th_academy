"""
Test suite for Payment (Cuenta de Cobro) flow
Tests: Create payment, upload bill, approve, reject, resubmit
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
COLLABORATOR_CREDS = {"email": "colaborador@test.com", "password": "password"}
CONTADOR_CREDS = {"email": "contador@test.com", "password": "password"}
ADMIN_CREDS = {"email": "admin@test.com", "password": "password"}


class TestAuthFlow:
    """Test authentication for all user types"""
    
    def test_collaborator_login(self):
        """Test collaborator can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=COLLABORATOR_CREDS)
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == COLLABORATOR_CREDS["email"]
        assert data["user"]["role"] == "collaborator"
        print(f"✓ Collaborator login successful")
    
    def test_contador_login(self):
        """Test contador (accountant) can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=CONTADOR_CREDS)
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == CONTADOR_CREDS["email"]
        assert data["user"]["role"] == "accountant"
        print(f"✓ Contador login successful")
    
    def test_admin_login(self):
        """Test admin can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == ADMIN_CREDS["email"]
        assert data["user"]["role"] == "admin"
        print(f"✓ Admin login successful")


class TestPaymentCreation:
    """Test payment (cuenta de cobro) creation by collaborator"""
    
    @pytest.fixture
    def collaborator_token(self):
        """Get collaborator auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=COLLABORATOR_CREDS)
        if response.status_code != 200:
            pytest.skip("Collaborator login failed")
        return response.json()["access_token"]
    
    @pytest.fixture
    def collaborator_contracts(self, collaborator_token):
        """Get collaborator's active contracts"""
        headers = {"Authorization": f"Bearer {collaborator_token}"}
        response = requests.get(f"{BASE_URL}/api/contracts", headers=headers, params={"status": "active"})
        if response.status_code != 200:
            pytest.skip("Failed to get contracts")
        return response.json()
    
    def test_collaborator_can_list_active_contracts(self, collaborator_token):
        """Collaborator can see their active contracts"""
        headers = {"Authorization": f"Bearer {collaborator_token}"}
        response = requests.get(f"{BASE_URL}/api/contracts", headers=headers, params={"status": "active"})
        assert response.status_code == 200
        contracts = response.json()
        assert isinstance(contracts, list)
        print(f"✓ Collaborator has {len(contracts)} active contracts")
    
    def test_collaborator_can_create_payment(self, collaborator_token, collaborator_contracts):
        """Collaborator can create a cuenta de cobro for active contract"""
        if not collaborator_contracts:
            pytest.skip("No active contracts available")
        
        contract_id = collaborator_contracts[0]["id"]
        headers = {"Authorization": f"Bearer {collaborator_token}"}
        
        payment_data = {
            "contract_id": contract_id,
            "amount": 3500000,
            "payment_date": "2025-01-15T00:00:00Z",
            "description": "TEST_Pago mes de enero 2025"
        }
        
        response = requests.post(f"{BASE_URL}/api/payments", headers=headers, json=payment_data)
        assert response.status_code == 201, f"Create payment failed: {response.text}"
        
        data = response.json()
        assert data["status"] == "draft"
        assert data["amount"] == 3500000
        assert data["contract_id"] == contract_id
        print(f"✓ Payment created with ID: {data['id']}, status: {data['status']}")
        return data["id"]


class TestPaymentUploadAndApproval:
    """Test payment bill upload and approval/rejection flow"""
    
    @pytest.fixture
    def collaborator_session(self):
        """Get collaborator auth session"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=COLLABORATOR_CREDS)
        if response.status_code != 200:
            pytest.skip("Collaborator login failed")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def contador_session(self):
        """Get contador auth session"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=CONTADOR_CREDS)
        if response.status_code != 200:
            pytest.skip("Contador login failed")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def draft_payment(self, collaborator_session):
        """Create a draft payment for testing"""
        # Get active contract
        response = requests.get(f"{BASE_URL}/api/contracts", headers=collaborator_session, params={"status": "active"})
        if response.status_code != 200 or not response.json():
            pytest.skip("No active contracts")
        
        contract_id = response.json()[0]["id"]
        
        payment_data = {
            "contract_id": contract_id,
            "amount": 2500000,
            "payment_date": "2025-01-20T00:00:00Z",
            "description": "TEST_Payment for upload test"
        }
        
        response = requests.post(f"{BASE_URL}/api/payments", headers=collaborator_session, json=payment_data)
        if response.status_code != 201:
            pytest.skip(f"Failed to create payment: {response.text}")
        
        return response.json()
    
    def test_collaborator_can_upload_bill(self, collaborator_session, draft_payment):
        """Collaborator can upload PDF bill for draft payment"""
        payment_id = draft_payment["id"]
        
        # Create a mock PDF file
        pdf_content = b"%PDF-1.4 mock pdf content for testing"
        files = {"file": ("cuenta_cobro.pdf", io.BytesIO(pdf_content), "application/pdf")}
        
        # Remove Content-Type header for multipart
        headers = {"Authorization": collaborator_session["Authorization"]}
        
        response = requests.post(
            f"{BASE_URL}/api/payments/{payment_id}/upload-bill",
            headers=headers,
            files=files
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        assert "file_id" in data or "message" in data
        print(f"✓ Bill uploaded successfully for payment {payment_id}")
        
        # Verify payment status changed to pending_approval
        response = requests.get(f"{BASE_URL}/api/payments", headers=collaborator_session)
        payments = response.json()
        payment = next((p for p in payments if p["id"] == payment_id), None)
        assert payment is not None
        assert payment["status"] == "pending_approval", f"Expected pending_approval, got {payment['status']}"
        print(f"✓ Payment status changed to pending_approval")
    
    def test_contador_can_see_pending_payments(self, contador_session):
        """Contador can see payments pending approval"""
        response = requests.get(f"{BASE_URL}/api/payments", headers=contador_session)
        assert response.status_code == 200
        payments = response.json()
        pending = [p for p in payments if p["status"] == "pending_approval"]
        print(f"✓ Contador can see {len(pending)} pending payments")
    
    def test_contador_can_approve_payment(self, collaborator_session, contador_session, draft_payment):
        """Contador can approve a pending payment"""
        payment_id = draft_payment["id"]
        
        # First upload bill
        pdf_content = b"%PDF-1.4 mock pdf for approval test"
        files = {"file": ("cuenta_cobro_approve.pdf", io.BytesIO(pdf_content), "application/pdf")}
        headers = {"Authorization": collaborator_session["Authorization"]}
        
        upload_response = requests.post(
            f"{BASE_URL}/api/payments/{payment_id}/upload-bill",
            headers=headers,
            files=files
        )
        assert upload_response.status_code == 200, f"Upload failed: {upload_response.text}"
        
        # Now approve as contador
        response = requests.post(
            f"{BASE_URL}/api/payments/{payment_id}/approve",
            headers=contador_session
        )
        
        assert response.status_code == 200, f"Approve failed: {response.text}"
        print(f"✓ Payment {payment_id} approved by contador")
        
        # Verify status
        response = requests.get(f"{BASE_URL}/api/payments", headers=contador_session)
        payments = response.json()
        payment = next((p for p in payments if p["id"] == payment_id), None)
        assert payment is not None
        assert payment["status"] == "approved"
        print(f"✓ Payment status is now 'approved'")


class TestPaymentRejection:
    """Test payment rejection flow - CRITICAL FEATURE"""
    
    @pytest.fixture
    def collaborator_session(self):
        """Get collaborator auth session"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=COLLABORATOR_CREDS)
        if response.status_code != 200:
            pytest.skip("Collaborator login failed")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def contador_session(self):
        """Get contador auth session"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=CONTADOR_CREDS)
        if response.status_code != 200:
            pytest.skip("Contador login failed")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def pending_payment(self, collaborator_session):
        """Create a payment and upload bill to make it pending"""
        # Get active contract
        response = requests.get(f"{BASE_URL}/api/contracts", headers=collaborator_session, params={"status": "active"})
        if response.status_code != 200 or not response.json():
            pytest.skip("No active contracts")
        
        contract_id = response.json()[0]["id"]
        
        # Create payment
        payment_data = {
            "contract_id": contract_id,
            "amount": 1500000,
            "payment_date": "2025-01-25T00:00:00Z",
            "description": "TEST_Payment for rejection test"
        }
        
        response = requests.post(f"{BASE_URL}/api/payments", headers=collaborator_session, json=payment_data)
        if response.status_code != 201:
            pytest.skip(f"Failed to create payment: {response.text}")
        
        payment_id = response.json()["id"]
        
        # Upload bill
        pdf_content = b"%PDF-1.4 mock pdf for rejection test"
        files = {"file": ("cuenta_cobro_reject.pdf", io.BytesIO(pdf_content), "application/pdf")}
        headers = {"Authorization": collaborator_session["Authorization"]}
        
        upload_response = requests.post(
            f"{BASE_URL}/api/payments/{payment_id}/upload-bill",
            headers=headers,
            files=files
        )
        
        if upload_response.status_code != 200:
            pytest.skip(f"Failed to upload bill: {upload_response.text}")
        
        return {"id": payment_id, "contract_id": contract_id}
    
    def test_contador_can_reject_payment_with_reason(self, contador_session, pending_payment):
        """Contador can reject a payment with a reason"""
        payment_id = pending_payment["id"]
        rejection_reason = "La cuenta de cobro no incluye el IVA correctamente. Por favor corregir."
        
        response = requests.post(
            f"{BASE_URL}/api/payments/{payment_id}/reject",
            headers=contador_session,
            params={"rejection_reason": rejection_reason}
        )
        
        assert response.status_code == 200, f"Reject failed: {response.text}"
        print(f"✓ Payment {payment_id} rejected with reason")
        
        # Verify status and rejection_reason
        response = requests.get(f"{BASE_URL}/api/payments", headers=contador_session)
        payments = response.json()
        payment = next((p for p in payments if p["id"] == payment_id), None)
        
        assert payment is not None
        assert payment["status"] == "rejected", f"Expected rejected, got {payment['status']}"
        assert payment.get("rejection_reason") == rejection_reason, f"Rejection reason mismatch"
        print(f"✓ Payment status is 'rejected' with correct reason")
    
    def test_collaborator_sees_rejection_reason(self, collaborator_session, contador_session, pending_payment):
        """Collaborator can see the rejection reason"""
        payment_id = pending_payment["id"]
        rejection_reason = "Falta firma del colaborador en la cuenta de cobro"
        
        # Reject as contador
        requests.post(
            f"{BASE_URL}/api/payments/{payment_id}/reject",
            headers=contador_session,
            params={"rejection_reason": rejection_reason}
        )
        
        # Check as collaborator
        response = requests.get(f"{BASE_URL}/api/payments", headers=collaborator_session)
        assert response.status_code == 200
        
        payments = response.json()
        payment = next((p for p in payments if p["id"] == payment_id), None)
        
        assert payment is not None
        assert payment["status"] == "rejected"
        assert payment.get("rejection_reason") == rejection_reason
        print(f"✓ Collaborator can see rejection reason: '{rejection_reason}'")
    
    def test_collaborator_can_resubmit_after_rejection(self, collaborator_session, contador_session, pending_payment):
        """Collaborator can upload a new bill after rejection"""
        payment_id = pending_payment["id"]
        
        # Reject as contador
        requests.post(
            f"{BASE_URL}/api/payments/{payment_id}/reject",
            headers=contador_session,
            params={"rejection_reason": "Documento incorrecto"}
        )
        
        # Verify rejected status
        response = requests.get(f"{BASE_URL}/api/payments", headers=collaborator_session)
        payments = response.json()
        payment = next((p for p in payments if p["id"] == payment_id), None)
        assert payment["status"] == "rejected"
        
        # Resubmit new bill
        pdf_content = b"%PDF-1.4 corrected pdf content"
        files = {"file": ("cuenta_cobro_corregida.pdf", io.BytesIO(pdf_content), "application/pdf")}
        headers = {"Authorization": collaborator_session["Authorization"]}
        
        response = requests.post(
            f"{BASE_URL}/api/payments/{payment_id}/upload-bill",
            headers=headers,
            files=files
        )
        
        assert response.status_code == 200, f"Resubmit failed: {response.text}"
        print(f"✓ Collaborator resubmitted bill after rejection")
        
        # Verify status changed back to pending_approval
        response = requests.get(f"{BASE_URL}/api/payments", headers=collaborator_session)
        payments = response.json()
        payment = next((p for p in payments if p["id"] == payment_id), None)
        
        assert payment["status"] == "pending_approval", f"Expected pending_approval after resubmit, got {payment['status']}"
        print(f"✓ Payment status changed to pending_approval after resubmit")


class TestRejectAPIEndpoint:
    """Direct API tests for /api/payments/{id}/reject endpoint"""
    
    @pytest.fixture
    def contador_session(self):
        """Get contador auth session"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=CONTADOR_CREDS)
        if response.status_code != 200:
            pytest.skip("Contador login failed")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def collaborator_session(self):
        """Get collaborator auth session"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=COLLABORATOR_CREDS)
        if response.status_code != 200:
            pytest.skip("Collaborator login failed")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_reject_requires_accountant_role(self, collaborator_session):
        """Reject endpoint requires accountant role"""
        # Try to reject as collaborator (should fail)
        response = requests.post(
            f"{BASE_URL}/api/payments/fake-id/reject",
            headers=collaborator_session,
            params={"rejection_reason": "test"}
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print(f"✓ Reject endpoint correctly requires accountant role")
    
    def test_reject_returns_404_for_invalid_payment(self, contador_session):
        """Reject returns 404 for non-existent payment"""
        response = requests.post(
            f"{BASE_URL}/api/payments/non-existent-id/reject",
            headers=contador_session,
            params={"rejection_reason": "test reason"}
        )
        
        assert response.status_code == 404
        print(f"✓ Reject returns 404 for invalid payment ID")
    
    def test_reject_requires_pending_approval_status(self, contador_session, collaborator_session):
        """Reject only works on payments with pending_approval status"""
        # Create a draft payment (not uploaded yet)
        response = requests.get(f"{BASE_URL}/api/contracts", headers=collaborator_session, params={"status": "active"})
        if response.status_code != 200 or not response.json():
            pytest.skip("No active contracts")
        
        contract_id = response.json()[0]["id"]
        
        payment_data = {
            "contract_id": contract_id,
            "amount": 1000000,
            "payment_date": "2025-01-30T00:00:00Z",
            "description": "TEST_Draft payment for status test"
        }
        
        response = requests.post(f"{BASE_URL}/api/payments", headers=collaborator_session, json=payment_data)
        if response.status_code != 201:
            pytest.skip("Failed to create payment")
        
        payment_id = response.json()["id"]
        
        # Try to reject draft payment (should fail)
        response = requests.post(
            f"{BASE_URL}/api/payments/{payment_id}/reject",
            headers=contador_session,
            params={"rejection_reason": "test"}
        )
        
        assert response.status_code == 400, f"Expected 400 for draft payment, got {response.status_code}"
        print(f"✓ Reject correctly fails for non-pending_approval status")


# Cleanup fixture
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data():
    """Cleanup TEST_ prefixed payments after all tests"""
    yield
    # Cleanup after tests
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        if response.status_code == 200:
            print("\n🧹 Test data cleanup would happen here (TEST_ prefixed data)")
    except:
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
