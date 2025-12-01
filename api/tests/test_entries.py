"""
Tests for entries router - CRUD operations for job entries
Following AAA pattern and Given-When-Then naming convention
Note: DEV_MODE is enabled in conftest.py, bypassing JWT auth
"""
import datetime as dt


def test_given_no_auth_when_get_entries_then_works_in_dev_mode(client):
    """In dev mode, requests work without authentication."""
    # Arrange - no auth headers needed in dev mode

    # Act
    r = client.get("/entries/")

    # Assert
    assert r.status_code == 200


def test_given_valid_payload_when_post_entry_then_creates_and_lists(client):
    """Create an entry via POST /entries and confirm it appears in GET /entries."""
    # Arrange
    payload = {
        "jobUrl": "https://example.com/job/1",
        "jobTitle": "Senior Engineer",
        "companyName": "Example Corp",
        "remoteType": "hybrid",
        "salaryRange": "$200-300K",
        "roleType": "full_time",
        "location": "NYC, NY",
        "applicationStatus": "applied",
        "interestLevel": "high",
        "notes": "testing",
    }

    # Act
    r = client.post("/entries", json=payload)

    # Assert
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert "created_at" in data

    # Verify it appears in list
    r = client.get("/entries/?page=1&pageSize=10")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


def test_given_invalid_interest_level_when_post_entry_then_returns_422(client):
    """Ensure invalid interestLevel fails validation with 422."""
    # Arrange
    bad_payload = {
        "jobUrl": "https://example.com/job/2",
        "interestLevel": "super_high",  # Invalid - must be high/medium/low
    }

    # Act
    r = client.post("/entries", json=bad_payload)

    # Assert
    assert r.status_code == 422


def test_given_multiple_entries_when_paginate_then_respects_page_size(client):
    """Verify GET /entries respects page and pageSize parameters."""
    # Arrange - create a few entries
    for i in range(3):
        client.post("/entries", json={"jobUrl": f"https://example.com/pagination/{i}"})

    # Act
    r = client.get("/entries/?page=1&pageSize=2")

    # Assert
    assert r.status_code == 200
    data = r.json()
    assert data["page"] == 1
    assert data["pageSize"] == 2
    assert len(data["items"]) <= 2


def test_given_job_url_filter_when_list_entries_then_filters_results(client):
    """Verify GET /entries filters by jobUrl parameter."""
    # Arrange
    unique_url = f"https://example.com/unique-job-{dt.datetime.utcnow().timestamp()}"
    client.post("/entries", json={"jobUrl": unique_url, "jobTitle": "Unique Job"})

    # Act
    r = client.get(f"/entries/?jobUrl={unique_url}")

    # Assert
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert any(item["jobUrl"] == unique_url for item in data["items"])
