"""
Tests for auth/dependencies.py - Authentication dependencies
Following AAA pattern and Given-When-Then naming convention
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import (
    get_current_user_id,
    get_current_user,
    require_subscription_tier,
    check_feature_access
)
from app.models import User, FeatureAccess


class TestGetCurrentUserId:
    """Tests for get_current_user_id dependency"""

    @pytest.mark.asyncio
    async def test_given_user_id_in_state_when_get_user_id_then_returns_id(self):
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.state.user_id = "user_123"

        # Act
        result = await get_current_user_id(mock_request)

        # Assert
        assert result == "user_123"

    @pytest.mark.asyncio
    async def test_given_no_user_id_in_state_when_get_user_id_then_raises_401(self):
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock(spec=[])  # No user_id attribute

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_id(mock_request)
        
        assert exc_info.value.status_code == 401
        assert "Authentication required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_given_none_user_id_when_get_user_id_then_raises_401(self):
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.state.user_id = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_id(mock_request)
        
        assert exc_info.value.status_code == 401


class TestGetCurrentUser:
    """Tests for get_current_user dependency"""

    @pytest.mark.asyncio
    async def test_given_existing_user_when_get_user_then_returns_user(self):
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.state.user_id = "user_existing"
        
        mock_db = MagicMock(spec=Session)
        existing_user = User(
            id="user_existing",
            email="existing@example.com",
            subscription_tier="free"
        )
        mock_db.query.return_value.filter_by.return_value.first.return_value = existing_user

        # Act
        result = await get_current_user(mock_request, mock_db)

        # Assert
        assert result == existing_user
        assert result.email == "existing@example.com"

    @pytest.mark.asyncio
    async def test_given_clerk_user_not_in_db_when_get_user_then_auto_creates(self):
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.state.user_id = "user_new_clerk"
        mock_request.state.user_email = "newclerk@example.com"
        
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        # Act
        result = await get_current_user(mock_request, mock_db)

        # Assert
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        added_user = mock_db.add.call_args[0][0]
        assert added_user.id == "user_new_clerk"
        assert added_user.email == "newclerk@example.com"
        assert added_user.subscription_tier == "free"

    @pytest.mark.asyncio
    async def test_given_clerk_user_no_email_when_get_user_then_uses_fallback_email(self):
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.state.user_id = "user_no_email"
        mock_request.state.user_email = None
        
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        # Act
        result = await get_current_user(mock_request, mock_db)

        # Assert
        added_user = mock_db.add.call_args[0][0]
        assert added_user.email == "user_no_email@clerk.user"

    @pytest.mark.asyncio
    @patch('app.auth.dependencies.settings')
    async def test_given_dev_mode_dev_user_when_get_user_then_creates_dev_user(self, mock_settings):
        # Arrange
        mock_settings.dev_mode = True
        mock_request = MagicMock(spec=Request)
        mock_request.state.user_id = "dev_user"
        mock_request.state.user_email = None
        
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        # Act
        result = await get_current_user(mock_request, mock_db)

        # Assert
        added_user = mock_db.add.call_args[0][0]
        assert added_user.id == "dev_user"
        assert added_user.email == "dev@example.com"
        assert added_user.full_name == "Dev User"

    @pytest.mark.asyncio
    async def test_given_unknown_user_id_format_when_get_user_then_raises_404(self):
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.state.user_id = "invalid_id_format"  # Doesn't start with "user_"
        mock_request.state.user_email = None
        
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, mock_db)
        
        assert exc_info.value.status_code == 404
        assert "User not found" in exc_info.value.detail


class TestRequireSubscriptionTier:
    """Tests for require_subscription_tier dependency factory"""

    @pytest.mark.asyncio
    async def test_given_free_user_free_required_when_check_then_passes(self):
        # Arrange
        user = User(id="user_1", email="test@example.com", subscription_tier="free")
        tier_checker = require_subscription_tier("free")

        # Act
        result = await tier_checker(user)

        # Assert
        assert result == user

    @pytest.mark.asyncio
    async def test_given_pro_user_basic_required_when_check_then_passes(self):
        # Arrange
        user = User(id="user_2", email="test@example.com", subscription_tier="pro")
        tier_checker = require_subscription_tier("basic")

        # Act
        result = await tier_checker(user)

        # Assert
        assert result == user

    @pytest.mark.asyncio
    async def test_given_free_user_pro_required_when_check_then_raises_403(self):
        # Arrange
        user = User(id="user_3", email="test@example.com", subscription_tier="free")
        tier_checker = require_subscription_tier("pro")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await tier_checker(user)
        
        assert exc_info.value.status_code == 403
        assert "pro subscription" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_given_basic_user_pro_required_when_check_then_raises_403(self):
        # Arrange
        user = User(id="user_4", email="test@example.com", subscription_tier="basic")
        tier_checker = require_subscription_tier("pro")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await tier_checker(user)
        
        assert exc_info.value.status_code == 403


class TestCheckFeatureAccess:
    """Tests for check_feature_access dependency"""

    @pytest.mark.asyncio
    async def test_given_no_feature_record_when_check_access_then_returns_true(self):
        # Arrange
        user = User(id="user_1", email="test@example.com")
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        # Act
        result = await check_feature_access("ai_analysis", user, mock_db)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_given_access_granted_when_check_access_then_returns_true(self):
        # Arrange
        user = User(id="user_2", email="test@example.com")
        mock_db = MagicMock(spec=Session)
        feature = FeatureAccess(
            user_id="user_2",
            feature_name="ai_analysis",
            access_granted=True,
            usage_count=5,
            usage_limit=100
        )
        mock_db.query.return_value.filter_by.return_value.first.return_value = feature

        # Act
        result = await check_feature_access("ai_analysis", user, mock_db)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_given_access_denied_when_check_access_then_raises_403(self):
        # Arrange
        user = User(id="user_3", email="test@example.com")
        mock_db = MagicMock(spec=Session)
        feature = FeatureAccess(
            user_id="user_3",
            feature_name="premium_feature",
            access_granted=False
        )
        mock_db.query.return_value.filter_by.return_value.first.return_value = feature

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await check_feature_access("premium_feature", user, mock_db)
        
        assert exc_info.value.status_code == 403
        assert "premium_feature" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_given_usage_limit_reached_when_check_access_then_raises_429(self):
        # Arrange
        user = User(id="user_4", email="test@example.com")
        mock_db = MagicMock(spec=Session)
        feature = FeatureAccess(
            user_id="user_4",
            feature_name="api_calls",
            access_granted=True,
            usage_count=100,
            usage_limit=100
        )
        mock_db.query.return_value.filter_by.return_value.first.return_value = feature

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await check_feature_access("api_calls", user, mock_db)
        
        assert exc_info.value.status_code == 429
        assert "Usage limit reached" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_given_no_usage_limit_when_check_access_then_returns_true(self):
        # Arrange
        user = User(id="user_5", email="test@example.com")
        mock_db = MagicMock(spec=Session)
        feature = FeatureAccess(
            user_id="user_5",
            feature_name="unlimited_feature",
            access_granted=True,
            usage_count=1000,
            usage_limit=None  # No limit
        )
        mock_db.query.return_value.filter_by.return_value.first.return_value = feature

        # Act
        result = await check_feature_access("unlimited_feature", user, mock_db)

        # Assert
        assert result is True
