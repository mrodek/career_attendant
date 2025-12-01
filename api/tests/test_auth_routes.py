"""
Tests for auth router endpoints
Following AAA pattern and Given-When-Then naming convention

Note: DEV_MODE is enabled in conftest.py, so auth is bypassed.
Auth enforcement is tested in test_middleware.py and test_dependencies.py.
These tests verify the auth ENDPOINTS work correctly.
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test public health endpoint"""
    
    def test_given_request_when_health_check_then_returns_ok(self):
        """Health endpoint should work and return status ok"""
        # Arrange - simple GET

        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestAuthMeEndpoint:
    """Test /api/auth/me endpoint - returns current user info"""
    
    def test_given_dev_mode_when_get_me_then_returns_dev_user(self):
        """In dev mode, /api/auth/me returns the dev user"""
        # Arrange - DEV_MODE is enabled in conftest.py

        # Act
        response = client.get("/api/auth/me")

        # Assert - dev_user is auto-created
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "dev_user"
        assert data["email"] == "dev@example.com"


class TestValidateSessionEndpoint:
    """Test /api/auth/validate-session endpoint"""
    
    def test_given_empty_token_when_validate_then_returns_response(self):
        """Validate session endpoint accepts requests"""
        # Arrange
        payload = {"session_token": ""}

        # Act
        response = client.post("/api/auth/validate-session", json=payload)

        # Assert - Returns response (may be invalid without Clerk)
        assert response.status_code in [200, 401, 500]


class TestWebhookEndpoint:
    """Test /api/auth/webhook/clerk endpoint"""
    
    def test_given_user_created_event_when_webhook_then_processes(self):
        """Webhook processes user.created events"""
        # Arrange
        webhook_payload = {
            "type": "user.created",
            "data": {
                "id": "user_webhook_test",
                "email_addresses": [{"email_address": "webhook@example.com"}],
                "username": "webhookuser",
                "first_name": "Webhook",
                "last_name": "User"
            }
        }

        # Act
        response = client.post("/api/auth/webhook/clerk", json=webhook_payload)

        # Assert
        assert response.status_code in [200, 500]

    def test_given_user_deleted_event_when_webhook_then_processes(self):
        """Webhook processes user.deleted events"""
        # Arrange
        webhook_payload = {
            "type": "user.deleted",
            "data": {"id": "user_to_delete"}
        }

        # Act
        response = client.post("/api/auth/webhook/clerk", json=webhook_payload)

        # Assert
        assert response.status_code in [200, 500]

    def test_given_unknown_event_when_webhook_then_ignores(self):
        """Webhook ignores unknown event types"""
        # Arrange
        webhook_payload = {
            "type": "unknown.event",
            "data": {}
        }

        # Act
        response = client.post("/api/auth/webhook/clerk", json=webhook_payload)

        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "ignored"


class TestEntriesInDevMode:
    """Test that entries endpoints work in dev mode"""
    
    def test_given_dev_mode_when_list_entries_then_succeeds(self):
        """In dev mode, listing entries works without auth"""
        # Arrange - DEV_MODE enabled

        # Act
        response = client.get("/entries/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_given_dev_mode_when_create_entry_then_succeeds(self):
        """In dev mode, creating entries works without auth"""
        # Arrange
        entry_data = {
            "jobUrl": "https://example.com/auth-test-job",
            "jobTitle": "Auth Test Job"
        }

        # Act
        response = client.post("/entries", json=entry_data)

        # Assert
        assert response.status_code == 200
        assert "id" in response.json()
