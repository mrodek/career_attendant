"""
Tests for auth/middleware.py - Authentication middleware
Following AAA pattern and Given-When-Then naming convention
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.auth.middleware import AuthMiddleware, get_jwks_keys, auth_error_response


class TestAuthErrorResponse:
    """Tests for auth_error_response helper function"""

    def test_given_401_status_when_create_error_then_returns_json_response(self):
        # Arrange
        status_code = 401
        detail = "Unauthorized access"

        # Act
        result = auth_error_response(status_code, detail)

        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 401

    def test_given_500_status_when_create_error_then_returns_correct_body(self):
        # Arrange
        status_code = 500
        detail = "Internal server error"

        # Act
        result = auth_error_response(status_code, detail)

        # Assert
        assert result.status_code == 500
        # JSONResponse body is bytes, decode and check
        assert b"Internal server error" in result.body


class TestGetJwksKeys:
    """Tests for get_jwks_keys function"""

    @pytest.mark.asyncio
    @patch('app.auth.middleware._jwks_cache', None)
    @patch('app.auth.middleware.settings')
    async def test_given_no_jwks_url_when_get_keys_then_returns_none(self, mock_settings):
        # Arrange
        mock_settings.clerk_jwks_url = ""

        # Act
        result = await get_jwks_keys()

        # Assert
        assert result is None

    @pytest.mark.asyncio
    @patch('app.auth.middleware._jwks_cache', {'keys': [{'kid': 'test'}]})
    async def test_given_cached_keys_when_get_keys_then_returns_cache(self):
        # Arrange - cache already set via patch

        # Act
        result = await get_jwks_keys()

        # Assert
        assert result == {'keys': [{'kid': 'test'}]}

    @pytest.mark.asyncio
    @patch('app.auth.middleware._jwks_cache', None)
    @patch('app.auth.middleware.settings')
    @patch('app.auth.middleware.httpx.AsyncClient')
    async def test_given_valid_url_when_get_keys_then_fetches_and_caches(
        self, mock_client_class, mock_settings
    ):
        # Arrange
        mock_settings.clerk_jwks_url = "https://clerk.example.com/.well-known/jwks.json"
        mock_response = MagicMock()
        mock_response.json.return_value = {'keys': [{'kid': 'new_key'}]}
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client

        # Act
        result = await get_jwks_keys()

        # Assert
        assert result == {'keys': [{'kid': 'new_key'}]}

    @pytest.mark.asyncio
    @patch('app.auth.middleware._jwks_cache', None)
    @patch('app.auth.middleware.settings')
    @patch('app.auth.middleware.httpx.AsyncClient')
    async def test_given_network_error_when_get_keys_then_returns_none(
        self, mock_client_class, mock_settings
    ):
        # Arrange
        mock_settings.clerk_jwks_url = "https://clerk.example.com/.well-known/jwks.json"
        
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Network error")
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client

        # Act
        result = await get_jwks_keys()

        # Assert
        assert result is None


class TestAuthMiddleware:
    """Tests for AuthMiddleware class"""

    @pytest.fixture
    def middleware(self):
        return AuthMiddleware()

    @pytest.fixture
    def mock_call_next(self):
        async def call_next(request):
            return JSONResponse(content={"status": "ok"})
        return call_next

    @pytest.mark.asyncio
    async def test_given_health_endpoint_when_request_then_skips_auth(
        self, middleware, mock_call_next
    ):
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/health"
        mock_request.headers = {}

        # Act
        result = await middleware(mock_request, mock_call_next)

        # Assert
        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_given_docs_endpoint_when_request_then_skips_auth(
        self, middleware, mock_call_next
    ):
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/docs"
        mock_request.headers = {}

        # Act
        result = await middleware(mock_request, mock_call_next)

        # Assert
        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_given_auth_login_when_request_then_skips_auth(
        self, middleware, mock_call_next
    ):
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/auth/login"
        mock_request.headers = {}

        # Act
        result = await middleware(mock_request, mock_call_next)

        # Assert
        assert result.status_code == 200

    @pytest.mark.asyncio
    @patch('app.auth.middleware.settings')
    async def test_given_dev_mode_when_request_then_bypasses_auth(
        self, mock_settings, middleware, mock_call_next
    ):
        # Arrange
        mock_settings.dev_mode = True
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/entries"
        mock_request.headers = {}
        mock_request.state = MagicMock()

        # Act
        result = await middleware(mock_request, mock_call_next)

        # Assert
        assert result.status_code == 200
        assert mock_request.state.user_id == "dev_user"

    @pytest.mark.asyncio
    @patch('app.auth.middleware.settings')
    async def test_given_missing_auth_header_when_request_then_returns_401(
        self, mock_settings, middleware
    ):
        # Arrange
        mock_settings.dev_mode = False
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/entries"
        mock_request.headers = MagicMock()
        mock_request.headers.get.return_value = None

        async def call_next(req):
            return JSONResponse(content={"status": "ok"})

        # Act
        result = await middleware(mock_request, call_next)

        # Assert
        assert result.status_code == 401
        assert b"authorization" in result.body.lower()

    @pytest.mark.asyncio
    @patch('app.auth.middleware.settings')
    async def test_given_invalid_auth_format_when_request_then_returns_401(
        self, mock_settings, middleware
    ):
        # Arrange
        mock_settings.dev_mode = False
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/entries"
        mock_request.headers = MagicMock()
        mock_request.headers.get.return_value = "InvalidFormat token123"

        async def call_next(req):
            return JSONResponse(content={"status": "ok"})

        # Act
        result = await middleware(mock_request, call_next)

        # Assert
        assert result.status_code == 401

    @pytest.mark.asyncio
    @patch('app.auth.middleware.settings')
    @patch('app.auth.middleware.jwt')
    async def test_given_token_missing_kid_when_request_then_returns_401(
        self, mock_jwt, mock_settings, middleware
    ):
        # Arrange
        mock_settings.dev_mode = False
        mock_jwt.get_unverified_header.return_value = {}  # No 'kid'
        
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/entries"
        mock_request.headers = MagicMock()
        mock_request.headers.get.return_value = "Bearer valid_token"

        async def call_next(req):
            return JSONResponse(content={"status": "ok"})

        # Act
        result = await middleware(mock_request, call_next)

        # Assert
        assert result.status_code == 401
        assert b"key ID" in result.body

    @pytest.mark.asyncio
    @patch('app.auth.middleware.settings')
    @patch('app.auth.middleware.jwt')
    @patch('app.auth.middleware.get_jwks_keys')
    async def test_given_jwks_unavailable_when_request_then_returns_500(
        self, mock_get_jwks, mock_jwt, mock_settings, middleware
    ):
        # Arrange
        mock_settings.dev_mode = False
        mock_jwt.get_unverified_header.return_value = {'kid': 'test_kid'}
        mock_get_jwks.return_value = None  # JWKS fetch failed
        
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/entries"
        mock_request.headers = MagicMock()
        mock_request.headers.get.return_value = "Bearer valid_token"

        async def call_next(req):
            return JSONResponse(content={"status": "ok"})

        # Act
        result = await middleware(mock_request, call_next)

        # Assert
        assert result.status_code == 500
        assert b"JWKS" in result.body

    @pytest.mark.asyncio
    @patch('app.auth.middleware.settings')
    @patch('app.auth.middleware.jwt')
    @patch('app.auth.middleware.get_jwks_keys')
    async def test_given_no_matching_key_when_request_then_returns_401(
        self, mock_get_jwks, mock_jwt, mock_settings, middleware
    ):
        # Arrange
        mock_settings.dev_mode = False
        mock_jwt.get_unverified_header.return_value = {'kid': 'unknown_kid'}
        mock_get_jwks.return_value = {'keys': [{'kid': 'different_kid'}]}
        
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/entries"
        mock_request.headers = MagicMock()
        mock_request.headers.get.return_value = "Bearer valid_token"

        async def call_next(req):
            return JSONResponse(content={"status": "ok"})

        # Act
        result = await middleware(mock_request, call_next)

        # Assert
        assert result.status_code == 401
        assert b"matching key" in result.body

    @pytest.mark.asyncio
    @patch('app.auth.middleware.settings')
    @patch('app.auth.middleware.jwt')
    @patch('app.auth.middleware.get_jwks_keys')
    async def test_given_valid_jwt_when_request_then_sets_user_state(
        self, mock_get_jwks, mock_jwt, mock_settings, middleware, mock_call_next
    ):
        # Arrange
        mock_settings.dev_mode = False
        mock_jwt.get_unverified_header.return_value = {'kid': 'test_kid'}
        mock_get_jwks.return_value = {'keys': [{'kid': 'test_kid', 'n': 'xxx', 'e': 'AQAB'}]}
        mock_jwt.decode.return_value = {
            'sub': 'user_123',
            'sid': 'session_456',
            'email': 'test@example.com'
        }
        
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/entries"
        mock_request.headers = MagicMock()
        mock_request.headers.get.return_value = "Bearer valid_jwt_token"
        mock_request.state = MagicMock()

        # Act
        result = await middleware(mock_request, mock_call_next)

        # Assert
        assert result.status_code == 200
        assert mock_request.state.user_id == 'user_123'
        assert mock_request.state.session_id == 'session_456'
        assert mock_request.state.user_email == 'test@example.com'
