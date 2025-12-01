"""Tests for config.py - Application settings and configuration
Following AAA pattern and Given-When-Then naming convention

Note: Settings tests are limited because os.getenv() is called at class definition time
and conftest.py sets DEV_MODE=true before tests run.
"""
from app.config import Settings, get_cors_origins


class TestSettings:
    """Tests for Settings class - basic validation"""

    def test_given_settings_instance_when_check_attributes_then_has_required_fields(self):
        # Arrange & Act
        settings = Settings()

        # Assert - verify all expected attributes exist
        assert hasattr(settings, 'api_key')
        assert hasattr(settings, 'app_port')
        assert hasattr(settings, 'cors_origins')
        assert hasattr(settings, 'database_url')
        assert hasattr(settings, 'dev_mode')
        assert hasattr(settings, 'clerk_secret_key')
        assert hasattr(settings, 'clerk_publishable_key')
        assert hasattr(settings, 'clerk_jwks_url')
        assert hasattr(settings, 'frontend_url')
        assert hasattr(settings, 'extension_id')

    def test_given_settings_when_check_types_then_correct_types(self):
        # Arrange & Act
        settings = Settings()

        # Assert
        assert isinstance(settings.api_key, str)
        assert isinstance(settings.app_port, int)
        assert isinstance(settings.cors_origins, str)
        assert isinstance(settings.dev_mode, bool)

    def test_given_test_environment_when_create_settings_then_dev_mode_is_true(self):
        # Arrange - conftest.py sets DEV_MODE=true
        
        # Act
        settings = Settings()

        # Assert - in test environment, dev_mode should be true
        assert settings.dev_mode is True


class TestGetCorsOrigins:
    """Tests for get_cors_origins function"""

    def test_given_wildcard_origins_when_get_cors_then_returns_wildcard_list(self):
        # Arrange
        settings = Settings()
        settings.cors_origins = "*"

        # Act
        result = get_cors_origins(settings)

        # Assert
        assert result == ["*"]

    def test_given_single_origin_when_get_cors_then_returns_single_item_list(self):
        # Arrange
        settings = Settings()
        settings.cors_origins = "http://localhost:3000"

        # Act
        result = get_cors_origins(settings)

        # Assert
        assert result == ["http://localhost:3000"]

    def test_given_multiple_origins_when_get_cors_then_returns_split_list(self):
        # Arrange
        settings = Settings()
        settings.cors_origins = "http://localhost:3000,https://example.com,https://app.example.com"

        # Act
        result = get_cors_origins(settings)

        # Assert
        assert result == [
            "http://localhost:3000",
            "https://example.com",
            "https://app.example.com"
        ]

    def test_given_origins_with_spaces_when_get_cors_then_trims_whitespace(self):
        # Arrange
        settings = Settings()
        settings.cors_origins = "http://localhost:3000 , https://example.com , https://app.example.com"

        # Act
        result = get_cors_origins(settings)

        # Assert
        assert result == [
            "http://localhost:3000",
            "https://example.com",
            "https://app.example.com"
        ]

    def test_given_empty_entries_when_get_cors_then_filters_empty(self):
        # Arrange
        settings = Settings()
        settings.cors_origins = "http://localhost:3000,,https://example.com,"

        # Act
        result = get_cors_origins(settings)

        # Assert
        assert result == ["http://localhost:3000", "https://example.com"]
