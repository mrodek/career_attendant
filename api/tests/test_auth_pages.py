"""
Tests for routers/auth_page.py - Authentication HTML pages
Following AAA pattern and Given-When-Then naming convention
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestAuthCallbackPage:
    """Tests for /auth/callback endpoint"""

    def test_given_valid_token_and_userid_when_callback_then_shows_success(self):
        # Arrange
        token = "test_jwt_token"
        user_id = "user_123"
        email = "test@example.com"

        # Act
        response = client.get(
            f"/auth/callback?token={token}&userId={user_id}&email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert "Signed In" in response.text
        assert "test@example.com" in response.text

    def test_given_token_and_userid_no_email_when_callback_then_shows_userid(self):
        # Arrange
        token = "test_jwt_token"
        user_id = "user_456"

        # Act
        response = client.get(
            f"/auth/callback?token={token}&userId={user_id}"
        )

        # Assert
        assert response.status_code == 200
        assert "Signed In" in response.text
        assert "user_456" in response.text

    def test_given_no_token_when_callback_then_shows_error(self):
        # Arrange - no parameters

        # Act
        response = client.get("/auth/callback")

        # Assert
        assert response.status_code == 200
        assert "Authentication Failed" in response.text
        assert "No token received" in response.text

    def test_given_only_userid_when_callback_then_shows_error(self):
        # Arrange
        user_id = "user_789"

        # Act
        response = client.get(f"/auth/callback?userId={user_id}")

        # Assert
        assert response.status_code == 200
        assert "Authentication Failed" in response.text

    def test_given_only_token_when_callback_then_shows_error(self):
        # Arrange
        token = "test_token_only"

        # Act
        response = client.get(f"/auth/callback?token={token}")

        # Assert
        assert response.status_code == 200
        assert "Authentication Failed" in response.text


class TestAuthLoginPage:
    """Tests for /auth/login endpoint"""

    def test_given_request_when_login_page_then_returns_html(self):
        # Arrange - simple GET request

        # Act
        response = client.get("/auth/login")

        # Assert
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_given_request_when_login_page_then_contains_clerk_script(self):
        # Arrange - simple GET request

        # Act
        response = client.get("/auth/login")

        # Assert
        assert response.status_code == 200
        assert "clerk" in response.text.lower()
        assert "clerk.browser.js" in response.text

    def test_given_request_when_login_page_then_contains_title(self):
        # Arrange - simple GET request

        # Act
        response = client.get("/auth/login")

        # Assert
        assert response.status_code == 200
        assert "Career Attendant" in response.text
        assert "Sign In" in response.text

    def test_given_request_when_login_page_then_contains_callback_url(self):
        # Arrange - simple GET request

        # Act
        response = client.get("/auth/login")

        # Assert
        assert response.status_code == 200
        assert "/auth/callback" in response.text

    def test_given_request_when_login_page_then_includes_clerk_key_attribute(self):
        # Arrange - simple GET request

        # Act
        response = client.get("/auth/login")

        # Assert - The clerk publishable key attribute should be present in HTML
        assert response.status_code == 200
        assert "data-clerk-publishable-key" in response.text

    def test_given_request_when_login_page_then_has_loading_indicator(self):
        # Arrange - simple GET request

        # Act
        response = client.get("/auth/login")

        # Assert
        assert response.status_code == 200
        assert "Loading" in response.text
        assert "spinner" in response.text

    def test_given_request_when_login_page_then_has_clerk_container(self):
        # Arrange - simple GET request

        # Act
        response = client.get("/auth/login")

        # Assert
        assert response.status_code == 200
        assert "clerk-container" in response.text


class TestPublicEndpointAccess:
    """Tests to verify auth pages are publicly accessible"""

    def test_given_no_auth_when_access_callback_then_allowed(self):
        # Arrange - no authentication headers

        # Act
        response = client.get("/auth/callback")

        # Assert
        assert response.status_code == 200  # Not 401

    def test_given_no_auth_when_access_login_then_allowed(self):
        # Arrange - no authentication headers

        # Act
        response = client.get("/auth/login")

        # Assert
        assert response.status_code == 200  # Not 401
