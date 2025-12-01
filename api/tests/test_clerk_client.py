"""
Tests for auth/clerk_client.py - Clerk API client integration
Following AAA pattern and Given-When-Then naming convention
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy.orm import Session

from app.auth.clerk_client import ClerkClient
from app.models import User


class TestClerkClientInit:
    """Tests for ClerkClient initialization"""

    @patch('app.auth.clerk_client.settings')
    def test_given_no_secret_key_when_init_then_client_is_none(self, mock_settings):
        # Arrange
        mock_settings.clerk_secret_key = ""

        # Act
        client = ClerkClient()

        # Assert
        assert client.client is None

    @patch('app.auth.clerk_client.settings')
    @patch('app.auth.clerk_client.Clerk')
    def test_given_secret_key_when_init_then_creates_clerk_client(
        self, mock_clerk_class, mock_settings
    ):
        # Arrange
        mock_settings.clerk_secret_key = "sk_test_secret_key"

        # Act
        client = ClerkClient()

        # Assert
        mock_clerk_class.assert_called_once_with(bearer_auth="sk_test_secret_key")
        assert client.client is not None


class TestVerifySession:
    """Tests for verify_session method"""

    @pytest.mark.asyncio
    @patch('app.auth.clerk_client.settings')
    async def test_given_no_client_when_verify_session_then_returns_none(self, mock_settings):
        # Arrange
        mock_settings.clerk_secret_key = ""
        client = ClerkClient()

        # Act
        result = await client.verify_session("some_token")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    @patch('app.auth.clerk_client.settings')
    @patch('app.auth.clerk_client.Clerk')
    async def test_given_valid_session_when_verify_then_returns_session_dict(
        self, mock_clerk_class, mock_settings
    ):
        # Arrange
        mock_settings.clerk_secret_key = "sk_test_key"
        mock_clerk_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            'user_id': 'user_123',
            'expire_at': '2024-12-31T23:59:59Z'
        }
        mock_clerk_instance.sessions.verify = AsyncMock(return_value=mock_response)
        mock_clerk_class.return_value = mock_clerk_instance

        client = ClerkClient()

        # Act
        result = await client.verify_session("valid_session_token")

        # Assert
        assert result == {'user_id': 'user_123', 'expire_at': '2024-12-31T23:59:59Z'}

    @pytest.mark.asyncio
    @patch('app.auth.clerk_client.settings')
    @patch('app.auth.clerk_client.Clerk')
    async def test_given_invalid_session_when_verify_then_returns_none(
        self, mock_clerk_class, mock_settings
    ):
        # Arrange
        mock_settings.clerk_secret_key = "sk_test_key"
        mock_clerk_instance = MagicMock()
        mock_clerk_instance.sessions.verify = AsyncMock(side_effect=Exception("Invalid session"))
        mock_clerk_class.return_value = mock_clerk_instance

        client = ClerkClient()

        # Act
        result = await client.verify_session("invalid_token")

        # Assert
        assert result is None


class TestGetUser:
    """Tests for get_user method"""

    @pytest.mark.asyncio
    @patch('app.auth.clerk_client.settings')
    async def test_given_no_client_when_get_user_then_returns_none(self, mock_settings):
        # Arrange
        mock_settings.clerk_secret_key = ""
        client = ClerkClient()

        # Act
        result = await client.get_user("user_123")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    @patch('app.auth.clerk_client.settings')
    @patch('app.auth.clerk_client.Clerk')
    async def test_given_valid_user_id_when_get_user_then_returns_user_dict(
        self, mock_clerk_class, mock_settings
    ):
        # Arrange
        mock_settings.clerk_secret_key = "sk_test_key"
        mock_clerk_instance = MagicMock()
        mock_user = MagicMock()
        mock_user.to_dict.return_value = {
            'id': 'user_123',
            'email_addresses': [{'email_address': 'test@example.com'}],
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User'
        }
        mock_clerk_instance.users.get = AsyncMock(return_value=mock_user)
        mock_clerk_class.return_value = mock_clerk_instance

        client = ClerkClient()

        # Act
        result = await client.get_user("user_123")

        # Assert
        assert result['id'] == 'user_123'
        assert result['username'] == 'testuser'

    @pytest.mark.asyncio
    @patch('app.auth.clerk_client.settings')
    @patch('app.auth.clerk_client.Clerk')
    async def test_given_invalid_user_id_when_get_user_then_returns_none(
        self, mock_clerk_class, mock_settings
    ):
        # Arrange
        mock_settings.clerk_secret_key = "sk_test_key"
        mock_clerk_instance = MagicMock()
        mock_clerk_instance.users.get = AsyncMock(side_effect=Exception("User not found"))
        mock_clerk_class.return_value = mock_clerk_instance

        client = ClerkClient()

        # Act
        result = await client.get_user("nonexistent_user")

        # Assert
        assert result is None


class TestSyncUserToDb:
    """Tests for sync_user_to_db method"""

    @pytest.mark.asyncio
    @patch('app.auth.clerk_client.settings')
    async def test_given_new_user_when_sync_then_creates_user(self, mock_settings):
        # Arrange
        mock_settings.clerk_secret_key = "sk_test_key"
        client = ClerkClient()
        
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        
        clerk_user = {
            'id': 'user_new',
            'email_addresses': [{'email_address': 'new@example.com'}],
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User'
        }

        # Act
        result = await client.sync_user_to_db(clerk_user, mock_db)

        # Assert
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        added_user = mock_db.add.call_args[0][0]
        assert added_user.id == 'user_new'
        assert added_user.email == 'new@example.com'
        assert added_user.full_name == 'New User'

    @pytest.mark.asyncio
    @patch('app.auth.clerk_client.settings')
    async def test_given_existing_user_when_sync_then_updates_user(self, mock_settings):
        # Arrange
        mock_settings.clerk_secret_key = "sk_test_key"
        client = ClerkClient()
        
        existing_user = User(
            id='user_existing',
            email='old@example.com',
            username='olduser',
            full_name='Old Name'
        )
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter_by.return_value.first.return_value = existing_user
        
        clerk_user = {
            'id': 'user_existing',
            'email_addresses': [{'email_address': 'updated@example.com'}],
            'username': 'updateduser',
            'first_name': 'Updated',
            'last_name': 'Name'
        }

        # Act
        result = await client.sync_user_to_db(clerk_user, mock_db)

        # Assert
        mock_db.add.assert_not_called()  # Should not add, only update
        mock_db.commit.assert_called_once()
        assert existing_user.email == 'updated@example.com'
        assert existing_user.username == 'updateduser'
        assert existing_user.full_name == 'Updated Name'

    @pytest.mark.asyncio
    @patch('app.auth.clerk_client.settings')
    async def test_given_user_no_email_when_sync_then_returns_none(self, mock_settings):
        # Arrange
        mock_settings.clerk_secret_key = "sk_test_key"
        client = ClerkClient()
        
        mock_db = MagicMock(spec=Session)
        
        clerk_user = {
            'id': 'user_no_email',
            'email_addresses': [],  # No emails
            'username': 'noemailer'
        }

        # Act
        result = await client.sync_user_to_db(clerk_user, mock_db)

        # Assert
        assert result is None
        mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    @patch('app.auth.clerk_client.settings')
    async def test_given_user_with_only_first_name_when_sync_then_uses_first_name_only(
        self, mock_settings
    ):
        # Arrange
        mock_settings.clerk_secret_key = "sk_test_key"
        client = ClerkClient()
        
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        
        clerk_user = {
            'id': 'user_firstname',
            'email_addresses': [{'email_address': 'first@example.com'}],
            'first_name': 'FirstOnly',
            'last_name': ''
        }

        # Act
        result = await client.sync_user_to_db(clerk_user, mock_db)

        # Assert
        added_user = mock_db.add.call_args[0][0]
        assert added_user.full_name == 'FirstOnly'
