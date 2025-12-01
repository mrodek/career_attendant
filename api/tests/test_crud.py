"""
Tests for crud.py - Database operations for users and entries
Following AAA pattern and Given-When-Then naming convention
"""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.crud import upsert_user_by_email, create_entry
from app.models import User, SavedJob
from app.schemas import EntryIn


class TestUpsertUserByEmail:
    """Tests for upsert_user_by_email function"""

    def test_given_none_email_when_upsert_user_then_returns_none(self):
        # Arrange
        mock_db = MagicMock(spec=Session)

        # Act
        result = upsert_user_by_email(mock_db, email=None)

        # Assert
        assert result is None
        mock_db.query.assert_not_called()

    def test_given_existing_email_when_upsert_user_then_returns_existing_user(self):
        # Arrange
        mock_db = MagicMock(spec=Session)
        existing_user = User(id="existing_123", email="test@example.com")
        mock_db.query.return_value.filter.return_value.one_or_none.return_value = existing_user

        # Act
        result = upsert_user_by_email(mock_db, email="test@example.com")

        # Assert
        assert result == existing_user
        assert result.email == "test@example.com"

    def test_given_new_email_with_user_id_when_upsert_user_then_creates_user_with_id(self):
        # Arrange
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.one_or_none.return_value = None

        # Act
        result = upsert_user_by_email(mock_db, email="new@example.com", user_id="user_abc123")

        # Assert
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        added_user = mock_db.add.call_args[0][0]
        assert added_user.id == "user_abc123"
        assert added_user.email == "new@example.com"

    def test_given_new_email_without_user_id_when_upsert_user_then_generates_uuid(self):
        # Arrange
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.one_or_none.return_value = None

        # Act
        result = upsert_user_by_email(mock_db, email="new@example.com")

        # Assert
        mock_db.add.assert_called_once()
        added_user = mock_db.add.call_args[0][0]
        assert added_user.email == "new@example.com"
        assert added_user.id is not None  # UUID was generated

    def test_given_user_id_exists_when_upsert_user_then_returns_existing_by_id(self):
        # Arrange
        mock_db = MagicMock(spec=Session)
        existing_user = User(id="user_xyz", email="other@example.com")
        
        # First query (by email) returns None, second query (by id) returns user
        mock_db.query.return_value.filter.return_value.one_or_none.side_effect = [
            None,  # email lookup
            existing_user  # id lookup
        ]

        # Act
        result = upsert_user_by_email(mock_db, email="new@example.com", user_id="user_xyz")

        # Assert
        assert result == existing_user


class TestCreateEntry:
    """Tests for create_entry function"""

    def test_given_user_and_payload_when_create_entry_then_creates_saved_job(self):
        # Arrange
        mock_db = MagicMock(spec=Session)
        user = User(id="user_123", email="test@example.com")
        payload = EntryIn(
            jobUrl="https://example.com/job/1",
            jobTitle="Software Engineer",
            companyName="Test Corp"
        )

        # Act
        result = create_entry(mock_db, user, payload)

        # Assert
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        added_entry = mock_db.add.call_args[0][0]
        assert added_entry.user_id == "user_123"
        assert added_entry.job_url == "https://example.com/job/1"
        assert added_entry.job_title == "Software Engineer"
        assert added_entry.company_name == "Test Corp"

    def test_given_no_user_when_create_entry_then_user_id_is_none(self):
        # Arrange
        mock_db = MagicMock(spec=Session)
        payload = EntryIn(jobUrl="https://example.com/job/2")

        # Act
        result = create_entry(mock_db, user=None, payload=payload)

        # Assert
        added_entry = mock_db.add.call_args[0][0]
        assert added_entry.user_id is None
        assert added_entry.job_url == "https://example.com/job/2"

    def test_given_full_payload_when_create_entry_then_all_fields_populated(self):
        # Arrange
        mock_db = MagicMock(spec=Session)
        user = User(id="user_456", email="test@example.com")
        payload = EntryIn(
            jobUrl="https://example.com/job/3",
            jobTitle="Senior Developer",
            companyName="Big Tech",
            jobDescription="Build amazing things",
            salaryRange="$200-300K",
            location="San Francisco, CA",
            remoteType="hybrid",
            roleType="full_time",
            interestLevel="high",
            applicationStatus="applied",
            notes="Great opportunity",
            source="linkedin"
        )

        # Act
        result = create_entry(mock_db, user, payload)

        # Assert
        added_entry = mock_db.add.call_args[0][0]
        assert added_entry.job_title == "Senior Developer"
        assert added_entry.company_name == "Big Tech"
        assert added_entry.job_description == "Build amazing things"
        assert added_entry.salary_range == "$200-300K"
        assert added_entry.location == "San Francisco, CA"
        assert added_entry.remote_type == "hybrid"
        assert added_entry.role_type == "full_time"
        assert added_entry.interest_level == "high"
        assert added_entry.application_status == "applied"
        assert added_entry.notes == "Great opportunity"
        assert added_entry.source == "linkedin"

    def test_given_minimal_payload_when_create_entry_then_defaults_applied(self):
        # Arrange
        mock_db = MagicMock(spec=Session)
        user = User(id="user_789", email="test@example.com")
        payload = EntryIn(jobUrl="https://example.com/job/minimal")

        # Act
        result = create_entry(mock_db, user, payload)

        # Assert
        added_entry = mock_db.add.call_args[0][0]
        assert added_entry.job_url == "https://example.com/job/minimal"
        assert added_entry.job_title is None
        assert added_entry.company_name is None
        assert added_entry.application_status == "saved"  # default value
