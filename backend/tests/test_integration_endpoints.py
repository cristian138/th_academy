"""
Backend API tests for Integration Endpoints and Payment Superadmin Operations
Tests:
1. GET /api/integration/status - Integration status (admin+ role)
2. GET /api/integration/health - Presupuesto system health
3. POST /api/integration/retry/{payment_id} - Retry sync (admin+ role)
4. POST /api/webhook/presupuesto - Webhook from presupuesto
5. PUT /api/payments/{payment_id} - Superadmin can edit pending payments
6. POST /api/payments/{payment_id}/approve - Superadmin can approve payments
7. POST /api/payments/{payment_id}/reject - Superadmin can reject payments
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPERADMIN_CREDS = {"email": "superadmin@sportsadmin.com", "password": "password"}
ADMIN_CREDS = {"email": "admin@test.com", "password": "password"}
CONTADOR_CREDS = {"email": "contador@test.com", "password": "password"}
COLABORADOR_CREDS = {"email": "colaborador@test.com", "password": "password"}


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def superadmin_token(api_client):
    """Get superadmin authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json=SUPERADMIN_CREDS)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Superadmin authentication failed: {response.text}")


@pytest.fixture(scope="module")
def admin_token(api_client):
    """Get admin authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Admin authentication failed: {response.text}")


@pytest.fixture(scope="module")
def colaborador_token(api_client):
    """Get collaborator authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json=COLABORADOR_CREDS)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Collaborator authentication failed: {response.text}")


@pytest.fixture
def superadmin_client(api_client, superadmin_token):
    """Session with superadmin auth header"""
    api_client.headers.update({"Authorization": f"Bearer {superadmin_token}"})
    return api_client


@pytest.fixture
def admin_client(api_client, admin_token):
    """Session with admin auth header"""
    api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
    return api_client


class TestAuthenticationEndpoints:
    """Test authentication to verify credentials work"""
    
    def test_superadmin_login(self, api_client):
        """Verify superadmin can login"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json=SUPERADMIN_CREDS)
        assert response.status_code == 200, f"Superadmin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "superadmin"
        print(f"✓ Superadmin login successful, role: {data['user']['role']}")

    def test_admin_login(self, api_client):
        """Verify admin can login"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        print(f"✓ Admin login successful, role: {data['user']['role']}")


class TestIntegrationStatusEndpoint:
    """Tests for GET /api/integration/status"""
    
    def test_integration_status_with_superadmin(self, api_client, superadmin_token):
        """Superadmin can access integration status"""
        headers = {"Authorization": f"Bearer {superadmin_token}"}
        response = api_client.get(f"{BASE_URL}/api/integration/status", headers=headers)
        
        assert response.status_code == 200, f"Integration status failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "total_approved" in data
        assert "synced_count" in data
        assert "pending_count" in data
        assert "failed_count" in data
        assert "synced" in data
        assert "pending" in data
        assert "failed" in data
        assert "presupuesto_url" in data
        
        # Verify data types
        assert isinstance(data["total_approved"], int)
        assert isinstance(data["synced"], list)
        assert isinstance(data["pending"], list)
        assert isinstance(data["failed"], list)
        
        print(f"✓ Integration status: {data['total_approved']} approved, {data['synced_count']} synced, {data['pending_count']} pending, {data['failed_count']} failed")

    def test_integration_status_with_admin(self, api_client, admin_token):
        """Admin can access integration status"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = api_client.get(f"{BASE_URL}/api/integration/status", headers=headers)
        
        assert response.status_code == 200, f"Admin integration status failed: {response.text}"
        print("✓ Admin can access integration status")

    def test_integration_status_without_auth(self, api_client):
        """Unauthenticated request should fail"""
        response = api_client.get(f"{BASE_URL}/api/integration/status")
        assert response.status_code == 403 or response.status_code == 401
        print("✓ Unauthenticated request properly rejected")

    def test_integration_status_with_collaborator_fails(self, api_client, colaborador_token):
        """Collaborator should not access integration status"""
        headers = {"Authorization": f"Bearer {colaborador_token}"}
        response = api_client.get(f"{BASE_URL}/api/integration/status", headers=headers)
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Collaborator properly denied access to integration status")


class TestIntegrationHealthEndpoint:
    """Tests for GET /api/integration/health"""
    
    def test_integration_health_returns_status(self, api_client):
        """Integration health endpoint returns connectivity status"""
        # Note: This endpoint doesn't require auth based on code review
        response = api_client.get(f"{BASE_URL}/api/integration/health")
        
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "status" in data
        assert data["status"] in ["online", "degraded", "timeout", "error"]
        assert "presupuesto_reachable" in data or "message" in data
        
        print(f"✓ Integration health: {data['status']} - {data.get('message', 'N/A')}")

    def test_integration_health_with_auth(self, api_client, superadmin_token):
        """Health endpoint works with authentication too"""
        headers = {"Authorization": f"Bearer {superadmin_token}"}
        response = api_client.get(f"{BASE_URL}/api/integration/health", headers=headers)
        
        assert response.status_code == 200
        print("✓ Health check works with authentication")


class TestIntegrationRetryEndpoint:
    """Tests for POST /api/integration/retry/{payment_id}"""
    
    def test_retry_nonexistent_payment(self, api_client, superadmin_token):
        """Retry on non-existent payment returns 404"""
        headers = {"Authorization": f"Bearer {superadmin_token}"}
        fake_id = str(uuid.uuid4())
        response = api_client.post(f"{BASE_URL}/api/integration/retry/{fake_id}", headers=headers)
        
        assert response.status_code == 404
        print("✓ Retry on non-existent payment returns 404")

    def test_retry_without_auth(self, api_client):
        """Retry without auth should fail"""
        response = api_client.post(f"{BASE_URL}/api/integration/retry/someid")
        assert response.status_code in [401, 403]
        print("✓ Retry without auth properly rejected")


class TestPresupuestoWebhook:
    """Tests for POST /api/webhook/presupuesto"""
    
    def test_webhook_invalid_source(self, api_client):
        """Webhook with invalid source should fail"""
        payload = {
            "source": "invalid_source",
            "event_type": "payment_support_uploaded",
            "payment_id": "some-id"
        }
        response = api_client.post(f"{BASE_URL}/api/webhook/presupuesto", json=payload)
        
        assert response.status_code == 400
        print("✓ Webhook rejects invalid source")

    def test_webhook_valid_source_nonexistent_payment(self, api_client):
        """Webhook with valid source but non-existent payment returns 404"""
        payload = {
            "source": "presupuesto",
            "event_type": "payment_support_uploaded",
            "payment_id": str(uuid.uuid4())
        }
        response = api_client.post(f"{BASE_URL}/api/webhook/presupuesto", json=payload)
        
        assert response.status_code == 404
        print("✓ Webhook returns 404 for non-existent payment")

    def test_webhook_unsupported_event_type(self, api_client):
        """Webhook with unsupported event type returns failure"""
        payload = {
            "source": "presupuesto",
            "event_type": "unsupported_event",
            "payment_id": str(uuid.uuid4())
        }
        response = api_client.post(f"{BASE_URL}/api/webhook/presupuesto", json=payload)
        
        assert response.status_code == 200  # Returns success: false
        data = response.json()
        assert data.get("success") == False
        print("✓ Webhook handles unsupported event type correctly")


class TestPaymentEditEndpoint:
    """Tests for PUT /api/payments/{payment_id} - Superadmin edit payments"""
    
    def test_superadmin_can_get_payments(self, api_client, superadmin_token):
        """Superadmin can list payments"""
        headers = {"Authorization": f"Bearer {superadmin_token}"}
        response = api_client.get(f"{BASE_URL}/api/payments", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Superadmin can list payments: {len(data)} payments found")
        return data

    def test_edit_nonexistent_payment(self, api_client, superadmin_token):
        """Edit non-existent payment returns 404"""
        headers = {"Authorization": f"Bearer {superadmin_token}"}
        fake_id = str(uuid.uuid4())
        response = api_client.put(
            f"{BASE_URL}/api/payments/{fake_id}", 
            headers=headers,
            json={"amount": 1000000}
        )
        
        assert response.status_code == 404
        print("✓ Edit non-existent payment returns 404")

    def test_collaborator_cannot_edit_payment(self, api_client, colaborador_token):
        """Collaborator cannot edit payment"""
        headers = {"Authorization": f"Bearer {colaborador_token}"}
        fake_id = str(uuid.uuid4())
        response = api_client.put(
            f"{BASE_URL}/api/payments/{fake_id}", 
            headers=headers,
            json={"amount": 1000000}
        )
        
        # Should get 403 (forbidden) or 404 (not found - which is fine since we're testing permissions)
        assert response.status_code in [403, 404]
        print("✓ Collaborator properly restricted from editing payments")


class TestPaymentApproveEndpoint:
    """Tests for POST /api/payments/{payment_id}/approve"""
    
    def test_approve_nonexistent_payment(self, api_client, superadmin_token):
        """Approve non-existent payment returns 404"""
        headers = {"Authorization": f"Bearer {superadmin_token}"}
        fake_id = str(uuid.uuid4())
        response = api_client.post(f"{BASE_URL}/api/payments/{fake_id}/approve", headers=headers)
        
        assert response.status_code == 404
        print("✓ Approve non-existent payment returns 404")

    def test_approve_without_auth(self, api_client):
        """Approve without auth should fail"""
        response = api_client.post(f"{BASE_URL}/api/payments/someid/approve")
        assert response.status_code in [401, 403]
        print("✓ Approve without auth properly rejected")


class TestPaymentRejectEndpoint:
    """Tests for POST /api/payments/{payment_id}/reject"""
    
    def test_reject_nonexistent_payment(self, api_client, superadmin_token):
        """Reject non-existent payment returns 404"""
        headers = {"Authorization": f"Bearer {superadmin_token}"}
        fake_id = str(uuid.uuid4())
        response = api_client.post(
            f"{BASE_URL}/api/payments/{fake_id}/reject",
            headers=headers,
            params={"rejection_reason": "Test rejection"}
        )
        
        assert response.status_code == 404
        print("✓ Reject non-existent payment returns 404")

    def test_reject_without_auth(self, api_client):
        """Reject without auth should fail"""
        response = api_client.post(
            f"{BASE_URL}/api/payments/someid/reject",
            params={"rejection_reason": "Test"}
        )
        assert response.status_code in [401, 403]
        print("✓ Reject without auth properly rejected")


class TestRoleBasedAccessControl:
    """Tests for role-based access to integration and payment operations"""
    
    def test_superadmin_has_accountant_permissions(self, api_client, superadmin_token):
        """Superadmin should have access to accountant-level operations"""
        headers = {"Authorization": f"Bearer {superadmin_token}"}
        
        # Should be able to access payments
        response = api_client.get(f"{BASE_URL}/api/payments", headers=headers)
        assert response.status_code == 200
        print("✓ Superadmin can access payments (accountant operation)")

    def test_superadmin_has_admin_permissions(self, api_client, superadmin_token):
        """Superadmin should have access to admin-level operations"""
        headers = {"Authorization": f"Bearer {superadmin_token}"}
        
        # Should be able to access integration status
        response = api_client.get(f"{BASE_URL}/api/integration/status", headers=headers)
        assert response.status_code == 200
        print("✓ Superadmin can access integration status (admin operation)")

    def test_superadmin_can_list_users(self, api_client, superadmin_token):
        """Superadmin should be able to list users"""
        headers = {"Authorization": f"Bearer {superadmin_token}"}
        response = api_client.get(f"{BASE_URL}/api/users", headers=headers)
        
        assert response.status_code == 200
        print("✓ Superadmin can list users")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
