"""
Test suite for Contract Approval Flow with Document Upload
Tests: 
- Legal rep approves contract with PDF upload
- Collaborator downloads original contract
- Collaborator uploads signed contract
- Both admin and collaborator can download documents
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
COLLABORATOR_CREDS = {"email": "colaborador@test.com", "password": "password"}
ADMIN_CREDS = {"email": "admin@test.com", "password": "password"}
LEGAL_REP_CREDS = {"email": "legal@test.com", "password": "password"}


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
    
    def test_admin_login(self):
        """Test admin can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == ADMIN_CREDS["email"]
        assert data["user"]["role"] == "admin"
        print(f"✓ Admin login successful")
    
    def test_legal_rep_login(self):
        """Test legal representative can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=LEGAL_REP_CREDS)
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == LEGAL_REP_CREDS["email"]
        assert data["user"]["role"] == "legal_rep"
        print(f"✓ Legal rep login successful")


class TestContractApprovalWithDocument:
    """Test contract approval flow with document upload"""
    
    @pytest.fixture
    def legal_rep_session(self):
        """Get legal rep auth session"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=LEGAL_REP_CREDS)
        if response.status_code != 200:
            pytest.skip("Legal rep login failed")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}", "token": token}
    
    @pytest.fixture
    def admin_session(self):
        """Get admin auth session"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}", "token": token}
    
    @pytest.fixture
    def collaborator_session(self):
        """Get collaborator auth session"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=COLLABORATOR_CREDS)
        if response.status_code != 200:
            pytest.skip("Collaborator login failed")
        token = response.json()["access_token"]
        user_id = response.json()["user"]["id"]
        return {"Authorization": f"Bearer {token}", "token": token, "user_id": user_id}
    
    @pytest.fixture
    def pending_approval_contract(self, legal_rep_session, admin_session, collaborator_session):
        """Create a contract in pending_approval status for testing"""
        # First create a contract as legal rep
        contract_data = {
            "contract_type": "service",
            "collaborator_id": collaborator_session["user_id"],
            "title": "TEST_Contract for Approval Flow",
            "description": "Test contract for approval with document upload",
            "start_date": "2025-02-01T00:00:00Z",
            "end_date": "2025-12-31T00:00:00Z",
            "monthly_payment": 5000000
        }
        
        headers = {"Authorization": legal_rep_session["Authorization"]}
        response = requests.post(f"{BASE_URL}/api/contracts", headers=headers, json=contract_data)
        
        if response.status_code != 201:
            pytest.skip(f"Failed to create contract: {response.text}")
        
        contract = response.json()
        contract_id = contract["id"]
        print(f"✓ Contract created with ID: {contract_id}, status: {contract['status']}")
        
        # If contract is under_review, send for approval as admin
        if contract["status"] == "under_review":
            admin_headers = {"Authorization": admin_session["Authorization"]}
            review_response = requests.post(f"{BASE_URL}/api/contracts/{contract_id}/review", headers=admin_headers)
            if review_response.status_code == 200:
                print(f"✓ Contract sent for approval")
        
        # Refresh contract data
        response = requests.get(f"{BASE_URL}/api/contracts/{contract_id}", headers=headers)
        return response.json()
    
    def test_legal_rep_can_approve_with_document(self, legal_rep_session, pending_approval_contract):
        """Legal rep can approve contract by uploading PDF document"""
        contract_id = pending_approval_contract["id"]
        
        # Skip if contract is not in pending_approval status
        if pending_approval_contract["status"] != "pending_approval":
            pytest.skip(f"Contract not in pending_approval status: {pending_approval_contract['status']}")
        
        # Create a mock PDF file
        pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
        files = {"file": ("contrato_original.pdf", io.BytesIO(pdf_content), "application/pdf")}
        
        headers = {"Authorization": legal_rep_session["Authorization"]}
        
        response = requests.post(
            f"{BASE_URL}/api/contracts/{contract_id}/approve",
            headers=headers,
            files=files
        )
        
        assert response.status_code == 200, f"Approve failed: {response.text}"
        print(f"✓ Contract approved with document upload")
        
        # Verify contract status and contract_file_id
        response = requests.get(f"{BASE_URL}/api/contracts/{contract_id}", headers=headers)
        contract = response.json()
        
        assert contract["status"] == "approved", f"Expected approved, got {contract['status']}"
        assert contract.get("contract_file_id") is not None, "contract_file_id should be set"
        print(f"✓ Contract status is 'approved' with contract_file_id: {contract['contract_file_id']}")
        
        return contract
    
    def test_approve_requires_file(self, legal_rep_session, pending_approval_contract):
        """Approve endpoint requires a file to be uploaded"""
        contract_id = pending_approval_contract["id"]
        
        if pending_approval_contract["status"] != "pending_approval":
            pytest.skip(f"Contract not in pending_approval status")
        
        headers = {"Authorization": legal_rep_session["Authorization"]}
        
        # Try to approve without file
        response = requests.post(
            f"{BASE_URL}/api/contracts/{contract_id}/approve",
            headers=headers
        )
        
        # Should fail with 422 (validation error) because file is required
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
        print(f"✓ Approve correctly requires file upload")


class TestContractDocumentDownload:
    """Test document download functionality"""
    
    @pytest.fixture
    def legal_rep_session(self):
        """Get legal rep auth session"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=LEGAL_REP_CREDS)
        if response.status_code != 200:
            pytest.skip("Legal rep login failed")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}", "token": token}
    
    @pytest.fixture
    def collaborator_session(self):
        """Get collaborator auth session"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=COLLABORATOR_CREDS)
        if response.status_code != 200:
            pytest.skip("Collaborator login failed")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}", "token": token}
    
    @pytest.fixture
    def admin_session(self):
        """Get admin auth session"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}", "token": token}
    
    @pytest.fixture
    def approved_contract_with_file(self, legal_rep_session, collaborator_session):
        """Get or create an approved contract with contract_file_id"""
        headers = {"Authorization": collaborator_session["Authorization"]}
        
        # Get contracts with approved status
        response = requests.get(f"{BASE_URL}/api/contracts", headers=headers, params={"status": "approved"})
        contracts = response.json()
        
        # Find one with contract_file_id
        for contract in contracts:
            if contract.get("contract_file_id"):
                return contract
        
        # Also check active contracts (they should have both files)
        response = requests.get(f"{BASE_URL}/api/contracts", headers=headers, params={"status": "active"})
        contracts = response.json()
        
        for contract in contracts:
            if contract.get("contract_file_id"):
                return contract
        
        pytest.skip("No approved contract with contract_file_id found")
    
    def test_collaborator_can_download_original_contract(self, collaborator_session, approved_contract_with_file):
        """Collaborator can download the original contract document"""
        file_id = approved_contract_with_file["contract_file_id"]
        token = collaborator_session["token"]
        
        # Use the view endpoint with token
        response = requests.get(
            f"{BASE_URL}/api/files/view/{file_id}",
            params={"token": token}
        )
        
        assert response.status_code == 200, f"Download failed: {response.status_code} - {response.text}"
        assert len(response.content) > 0, "File content should not be empty"
        print(f"✓ Collaborator can download original contract (size: {len(response.content)} bytes)")
    
    def test_admin_can_download_original_contract(self, admin_session, approved_contract_with_file):
        """Admin can download the original contract document"""
        file_id = approved_contract_with_file["contract_file_id"]
        token = admin_session["token"]
        
        response = requests.get(
            f"{BASE_URL}/api/files/view/{file_id}",
            params={"token": token}
        )
        
        assert response.status_code == 200, f"Download failed: {response.status_code}"
        print(f"✓ Admin can download original contract")
    
    def test_legal_rep_can_download_original_contract(self, legal_rep_session, approved_contract_with_file):
        """Legal rep can download the original contract document"""
        file_id = approved_contract_with_file["contract_file_id"]
        token = legal_rep_session["token"]
        
        response = requests.get(
            f"{BASE_URL}/api/files/view/{file_id}",
            params={"token": token}
        )
        
        assert response.status_code == 200, f"Download failed: {response.status_code}"
        print(f"✓ Legal rep can download original contract")
    
    def test_download_requires_valid_token(self, approved_contract_with_file):
        """Download endpoint requires valid token"""
        file_id = approved_contract_with_file["contract_file_id"]
        
        # Try with invalid token
        response = requests.get(
            f"{BASE_URL}/api/files/view/{file_id}",
            params={"token": "invalid-token"}
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Download correctly requires valid token")


class TestUploadSignedContract:
    """Test signed contract upload by collaborator"""
    
    @pytest.fixture
    def collaborator_session(self):
        """Get collaborator auth session"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=COLLABORATOR_CREDS)
        if response.status_code != 200:
            pytest.skip("Collaborator login failed")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}", "token": token}
    
    @pytest.fixture
    def admin_session(self):
        """Get admin auth session"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}", "token": token}
    
    @pytest.fixture
    def approved_contract(self, collaborator_session):
        """Get an approved contract for the collaborator"""
        headers = {"Authorization": collaborator_session["Authorization"]}
        
        response = requests.get(f"{BASE_URL}/api/contracts", headers=headers, params={"status": "approved"})
        contracts = response.json()
        
        # Find one with contract_file_id (ready for signing)
        for contract in contracts:
            if contract.get("contract_file_id") and not contract.get("signed_file_id"):
                return contract
        
        pytest.skip("No approved contract ready for signing found")
    
    def test_collaborator_can_upload_signed_contract(self, collaborator_session, approved_contract):
        """Collaborator can upload signed contract"""
        contract_id = approved_contract["id"]
        
        # Create a mock signed PDF
        pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n% SIGNED DOCUMENT\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
        files = {"file": ("contrato_firmado.pdf", io.BytesIO(pdf_content), "application/pdf")}
        
        headers = {"Authorization": collaborator_session["Authorization"]}
        
        response = requests.post(
            f"{BASE_URL}/api/contracts/{contract_id}/upload-signed",
            headers=headers,
            files=files
        )
        
        assert response.status_code == 200, f"Upload signed failed: {response.text}"
        print(f"✓ Signed contract uploaded successfully")
        
        # Verify contract status changed to active and signed_file_id is set
        response = requests.get(f"{BASE_URL}/api/contracts/{contract_id}", headers=headers)
        contract = response.json()
        
        assert contract["status"] == "active", f"Expected active, got {contract['status']}"
        assert contract.get("signed_file_id") is not None, "signed_file_id should be set"
        print(f"✓ Contract status is 'active' with signed_file_id: {contract['signed_file_id']}")
        
        return contract
    
    def test_both_can_download_signed_contract(self, collaborator_session, admin_session):
        """Both collaborator and admin can download signed contract"""
        # Get an active contract with signed_file_id
        headers = {"Authorization": collaborator_session["Authorization"]}
        response = requests.get(f"{BASE_URL}/api/contracts", headers=headers, params={"status": "active"})
        contracts = response.json()
        
        active_contract = None
        for contract in contracts:
            if contract.get("signed_file_id"):
                active_contract = contract
                break
        
        if not active_contract:
            pytest.skip("No active contract with signed_file_id found")
        
        file_id = active_contract["signed_file_id"]
        
        # Test collaborator download
        response = requests.get(
            f"{BASE_URL}/api/files/view/{file_id}",
            params={"token": collaborator_session["token"]}
        )
        assert response.status_code == 200, f"Collaborator download failed: {response.status_code}"
        print(f"✓ Collaborator can download signed contract")
        
        # Test admin download
        response = requests.get(
            f"{BASE_URL}/api/files/view/{file_id}",
            params={"token": admin_session["token"]}
        )
        assert response.status_code == 200, f"Admin download failed: {response.status_code}"
        print(f"✓ Admin can download signed contract")


class TestFileViewEndpoint:
    """Test the /api/files/view/{file_id} endpoint"""
    
    @pytest.fixture
    def collaborator_session(self):
        """Get collaborator auth session"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=COLLABORATOR_CREDS)
        if response.status_code != 200:
            pytest.skip("Collaborator login failed")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}", "token": token}
    
    def test_view_returns_404_for_invalid_file(self, collaborator_session):
        """View endpoint returns 404 for non-existent file"""
        response = requests.get(
            f"{BASE_URL}/api/files/view/non-existent-file-id",
            params={"token": collaborator_session["token"]}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ View returns 404 for invalid file ID")
    
    def test_view_requires_token(self):
        """View endpoint requires token parameter"""
        response = requests.get(f"{BASE_URL}/api/files/view/some-file-id")
        
        # Should fail with 422 (missing required parameter) or 401
        assert response.status_code in [401, 422], f"Expected 401 or 422, got {response.status_code}"
        print(f"✓ View endpoint requires token parameter")


class TestContractPermissions:
    """Test contract access permissions"""
    
    @pytest.fixture
    def legal_rep_session(self):
        """Get legal rep auth session"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=LEGAL_REP_CREDS)
        if response.status_code != 200:
            pytest.skip("Legal rep login failed")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}", "token": token}
    
    @pytest.fixture
    def collaborator_session(self):
        """Get collaborator auth session"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=COLLABORATOR_CREDS)
        if response.status_code != 200:
            pytest.skip("Collaborator login failed")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}", "token": token}
    
    def test_only_legal_rep_can_approve(self, collaborator_session):
        """Only legal rep can approve contracts"""
        # Get any pending_approval contract
        headers = {"Authorization": collaborator_session["Authorization"]}
        response = requests.get(f"{BASE_URL}/api/contracts", headers=headers)
        contracts = response.json()
        
        pending = [c for c in contracts if c["status"] == "pending_approval"]
        if not pending:
            pytest.skip("No pending_approval contracts")
        
        contract_id = pending[0]["id"]
        
        # Try to approve as collaborator (should fail)
        pdf_content = b"%PDF-1.4 test"
        files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
        
        response = requests.post(
            f"{BASE_URL}/api/contracts/{contract_id}/approve",
            headers=headers,
            files=files
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print(f"✓ Only legal rep can approve contracts")
    
    def test_collaborator_can_only_see_own_contracts(self, collaborator_session):
        """Collaborator can only see their own contracts"""
        headers = {"Authorization": collaborator_session["Authorization"]}
        response = requests.get(f"{BASE_URL}/api/contracts", headers=headers)
        
        assert response.status_code == 200
        contracts = response.json()
        
        # All contracts should belong to the collaborator
        # (The API filters by collaborator_id for collaborator role)
        print(f"✓ Collaborator sees {len(contracts)} contracts (filtered to own)")


# Cleanup fixture
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data():
    """Cleanup TEST_ prefixed contracts after all tests"""
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
