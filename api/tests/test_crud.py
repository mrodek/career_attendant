"""
Tests for crud.py - Database operations for users and entries
Following AAA pattern and Given-When-Then naming convention
"""
import pytest
import uuid
from unittest.mock import MagicMock, patch, call
from sqlalchemy.orm import Session

from app.crud import upsert_user_by_email, create_entry, get_or_create_job, get_saved_job_by_url
from app.models import User, SavedJob, Job
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


class TestGetOrCreateJob:
    """Tests for get_or_create_job function"""

    def test_given_new_job_url_when_get_or_create_job_then_creates_job(self):
        # Arrange
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.one_or_none.return_value = None
        payload = EntryIn(
            jobUrl="https://example.com/job/new",
            jobTitle="Software Engineer",
            companyName="Test Corp"
        )

        # Act
        job, created = get_or_create_job(mock_db, payload)

        # Assert
        assert created is True
        mock_db.add.assert_called_once()
        added_job = mock_db.add.call_args[0][0]
        assert isinstance(added_job, Job)
        assert added_job.job_url == "https://example.com/job/new"
        assert added_job.job_title == "Software Engineer"
        assert added_job.company_name == "Test Corp"

    def test_given_existing_job_url_when_get_or_create_job_then_returns_existing(self):
        # Arrange
        mock_db = MagicMock(spec=Session)
        existing_job = Job(
            id=uuid.uuid4(),
            job_url="https://example.com/job/existing",
            job_title="Existing Job",
            saved_count=5
        )
        mock_db.query.return_value.filter.return_value.one_or_none.return_value = existing_job
        payload = EntryIn(jobUrl="https://example.com/job/existing")

        # Act
        job, created = get_or_create_job(mock_db, payload)

        # Assert
        assert created is False
        assert job == existing_job
        mock_db.add.assert_not_called()

    def test_given_existing_job_with_missing_data_when_new_data_provided_then_updates(self):
        # Arrange
        mock_db = MagicMock(spec=Session)
        existing_job = Job(
            id=uuid.uuid4(),
            job_url="https://example.com/job/partial",
            job_title=None,  # Missing title
            company_name=None,
            saved_count=0
        )
        mock_db.query.return_value.filter.return_value.one_or_none.return_value = existing_job
        payload = EntryIn(
            jobUrl="https://example.com/job/partial",
            jobTitle="New Title",
            companyName="New Company"
        )

        # Act
        job, created = get_or_create_job(mock_db, payload)

        # Assert
        assert created is False
        assert job.job_title == "New Title"
        assert job.company_name == "New Company"
        mock_db.flush.assert_called()  # Should flush to save updates


class TestCreateEntry:
    """Tests for create_entry function - creates Job + SavedJob"""

    def test_given_user_and_payload_when_create_entry_then_creates_job_and_saved_job(self):
        # Arrange
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.one_or_none.return_value = None  # No existing job
        user = User(id="user_123", email="test@example.com")
        payload = EntryIn(
            jobUrl="https://example.com/job/1",
            jobTitle="Software Engineer",
            companyName="Test Corp",
            interestLevel="high",
            notes="Great opportunity"
        )

        # Act
        result = create_entry(mock_db, user, payload)

        # Assert
        # Should have called add twice: once for Job, once for SavedJob
        assert mock_db.add.call_count == 2
        
        # First add should be the Job
        first_add = mock_db.add.call_args_list[0][0][0]
        assert isinstance(first_add, Job)
        assert first_add.job_url == "https://example.com/job/1"
        assert first_add.job_title == "Software Engineer"
        
        # Second add should be the SavedJob
        second_add = mock_db.add.call_args_list[1][0][0]
        assert isinstance(second_add, SavedJob)
        assert second_add.user_id == "user_123"
        assert second_add.interest_level == "high"
        assert second_add.notes == "Great opportunity"

    def test_given_full_payload_when_create_entry_then_job_and_saved_job_fields_correct(self):
        # Arrange
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.one_or_none.return_value = None
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
        # Job fields (first add)
        added_job = mock_db.add.call_args_list[0][0][0]
        assert added_job.job_title == "Senior Developer"
        assert added_job.company_name == "Big Tech"
        assert added_job.job_description == "Build amazing things"
        assert added_job.salary_range == "$200-300K"
        assert added_job.location == "San Francisco, CA"
        assert added_job.remote_type == "hybrid"
        assert added_job.role_type == "full_time"
        assert added_job.source == "linkedin"
        
        # SavedJob fields (second add)
        added_saved_job = mock_db.add.call_args_list[1][0][0]
        assert added_saved_job.interest_level == "high"
        assert added_saved_job.application_status == "applied"
        assert added_saved_job.notes == "Great opportunity"

    def test_given_minimal_payload_when_create_entry_then_defaults_applied(self):
        # Arrange
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.one_or_none.return_value = None
        user = User(id="user_789", email="test@example.com")
        payload = EntryIn(jobUrl="https://example.com/job/minimal")

        # Act
        result = create_entry(mock_db, user, payload)

        # Assert
        added_saved_job = mock_db.add.call_args_list[1][0][0]
        assert added_saved_job.application_status == "saved"  # default value
        assert added_saved_job.interest_level is None
        assert added_saved_job.notes is None

    def test_given_existing_job_when_create_entry_then_increments_saved_count(self):
        # Arrange
        mock_db = MagicMock(spec=Session)
        existing_job = Job(
            id=uuid.uuid4(),
            job_url="https://example.com/job/popular",
            saved_count=5
        )
        mock_db.query.return_value.filter.return_value.one_or_none.return_value = existing_job
        user = User(id="user_abc", email="test@example.com")
        payload = EntryIn(jobUrl="https://example.com/job/popular")

        # Act
        result = create_entry(mock_db, user, payload)

        # Assert
        assert existing_job.saved_count == 6  # Incremented from 5
