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

    # Verify it appears in list with nested job data
    r = client.get("/entries/?page=1&pageSize=10")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    
    # Verify nested job structure exists
    item = data["items"][0]
    assert "job" in item
    assert "jobUrl" in item["job"]


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
    # Arrange - create a few entries with unique URLs
    base_time = dt.datetime.utcnow().timestamp()
    for i in range(3):
        client.post("/entries", json={"jobUrl": f"https://example.com/pagination/{base_time}/{i}"})

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


def test_given_duplicate_job_url_when_post_entry_then_returns_409(client):
    """Ensure saving the same job twice returns 409 Conflict."""
    # Arrange
    unique_url = f"https://example.com/duplicate-test-{dt.datetime.utcnow().timestamp()}"
    payload = {"jobUrl": unique_url, "jobTitle": "First Save"}
    
    # First save should succeed
    r = client.post("/entries", json=payload)
    assert r.status_code == 200

    # Act - try to save the same URL again
    r = client.post("/entries", json={"jobUrl": unique_url, "jobTitle": "Second Save"})

    # Assert
    assert r.status_code == 409
    assert "already saved" in r.json()["detail"].lower()


def test_given_saved_entry_when_list_entries_then_returns_nested_job_data(client):
    """Verify GET /entries returns nested job data structure."""
    # Arrange
    unique_url = f"https://example.com/nested-test-{dt.datetime.utcnow().timestamp()}"
    payload = {
        "jobUrl": unique_url,
        "jobTitle": "Nested Test Job",
        "companyName": "Test Corp",
        "salaryRange": "$150-200K",
        "location": "Remote",
        "remoteType": "remote",
        "roleType": "full_time",
        "interestLevel": "high",
        "applicationStatus": "saved",
        "notes": "Testing nested structure",
    }
    client.post("/entries", json=payload)

    # Act
    r = client.get(f"/entries/?jobUrl={unique_url}")

    # Assert
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    
    item = data["items"][0]
    
    # Verify nested job object
    assert "job" in item
    job = item["job"]
    assert job["jobUrl"] == unique_url
    assert job["jobTitle"] == "Nested Test Job"
    assert job["companyName"] == "Test Corp"
    assert job["salaryRange"] == "$150-200K"
    assert job["remoteType"] == "remote"
    assert job["roleType"] == "full_time"
    
    # Verify user-specific fields at top level
    assert item["interestLevel"] == "high"
    assert item["applicationStatus"] == "saved"
    assert item["notes"] == "Testing nested structure"
    
    # Verify backward-compatible flattened fields
    assert item["jobUrl"] == unique_url
    assert item["jobTitle"] == "Nested Test Job"


def test_given_saved_entry_when_list_entries_then_includes_ai_workflow_fields(client):
    """Verify GET /entries includes AI workflow fields (initially null)."""
    # Arrange
    unique_url = f"https://example.com/ai-fields-test-{dt.datetime.utcnow().timestamp()}"
    client.post("/entries", json={"jobUrl": unique_url})

    # Act
    r = client.get(f"/entries/?jobUrl={unique_url}")

    # Assert
    assert r.status_code == 200
    item = r.json()["items"][0]
    
    # AI fields should be present but null initially
    assert "jobFitScore" in item
    assert "jobFitReason" in item
    assert "targetedResumeUrl" in item
    assert "targetedCoverLetterUrl" in item
    assert "aiWorkflowStatus" in item
    assert item["jobFitScore"] is None
    assert item["aiWorkflowStatus"] is None


def test_given_saved_entry_when_patch_then_updates_fields(client):
    """Verify PATCH /entries/{id} updates user-specific fields."""
    # Arrange - create an entry
    unique_url = f"https://example.com/patch-test-{dt.datetime.utcnow().timestamp()}"
    r = client.post("/entries", json={
        "jobUrl": unique_url,
        "interestLevel": "low",
        "applicationStatus": "saved",
        "notes": "Original notes",
    })
    entry_id = r.json()["id"]

    # Act - update the entry
    r = client.patch(f"/entries/{entry_id}", json={
        "interestLevel": "high",
        "applicationStatus": "applied",
        "notes": "Updated notes",
    })

    # Assert - patch returns success
    assert r.status_code == 200
    assert r.json()["updated"] is True

    # Verify changes persisted
    r = client.get(f"/entries/?jobUrl={unique_url}")
    item = r.json()["items"][0]
    assert item["interestLevel"] == "high"
    assert item["applicationStatus"] == "applied"
    assert item["notes"] == "Updated notes"


def test_given_nonexistent_entry_when_patch_then_returns_404(client):
    """Verify PATCH /entries/{id} returns 404 for non-existent entry."""
    # Arrange
    fake_id = "00000000-0000-0000-0000-000000000000"

    # Act
    r = client.patch(f"/entries/{fake_id}", json={"notes": "Test"})

    # Assert
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


def test_given_saved_entry_when_delete_then_removes_entry(client):
    """Verify DELETE /entries/{id} removes the entry."""
    # Arrange - create an entry
    unique_url = f"https://example.com/delete-test-{dt.datetime.utcnow().timestamp()}"
    r = client.post("/entries", json={"jobUrl": unique_url})
    entry_id = r.json()["id"]

    # Confirm it exists
    r = client.get(f"/entries/?jobUrl={unique_url}")
    assert r.json()["total"] == 1

    # Act - delete the entry
    r = client.delete(f"/entries/{entry_id}")

    # Assert
    assert r.status_code == 200
    assert r.json()["deleted"] is True

    # Verify it's gone
    r = client.get(f"/entries/?jobUrl={unique_url}")
    assert r.json()["total"] == 0


def test_given_nonexistent_entry_when_delete_then_returns_404(client):
    """Verify DELETE /entries/{id} returns 404 for non-existent entry."""
    # Arrange
    fake_id = "00000000-0000-0000-0000-000000000000"

    # Act
    r = client.delete(f"/entries/{fake_id}")

    # Assert
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


def test_given_saved_entry_when_patch_partial_then_updates_only_provided_fields(client):
    """Verify PATCH only updates fields provided, leaving others unchanged."""
    # Arrange - create an entry with multiple fields
    unique_url = f"https://example.com/partial-patch-{dt.datetime.utcnow().timestamp()}"
    r = client.post("/entries", json={
        "jobUrl": unique_url,
        "interestLevel": "medium",
        "applicationStatus": "saved",
        "notes": "Original notes",
    })
    entry_id = r.json()["id"]

    # Act - update only notes
    r = client.patch(f"/entries/{entry_id}", json={"notes": "Only notes updated"})

    # Assert
    assert r.status_code == 200
    
    # Verify only notes changed, other fields unchanged
    r = client.get(f"/entries/?jobUrl={unique_url}")
    item = r.json()["items"][0]
    assert item["notes"] == "Only notes updated"
    assert item["interestLevel"] == "medium"  # Unchanged
    assert item["applicationStatus"] == "saved"  # Unchanged
