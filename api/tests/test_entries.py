import datetime as dt

API_KEY = {"X-API-Key": "dev_api_key"}


def test_auth_required(client):
    """Verify that GET /entries requires an API key and returns 401 without it."""
    r = client.get("/entries")
    assert r.status_code == 401


def test_post_entry_and_list(client):
    """Create an entry via POST /entries and confirm it appears in GET /entries."""
    payload = {
        "url": "https://example.com/job/1",
        "title": "Senior Engineer",
        "company": "Example",
        "workType": "Hybrid",
        "salaryRange": "$200-300K",
        "jobType": "Full-Time",
        "location": "NYC, NY",
        "applied": True,
        "userEmail": "me@example.com",
        "userId": "cid-1",
        "rating": 5,
        "notes": "testing",
        "timestamp": dt.datetime.utcnow().isoformat() + "Z",
    }
    r = client.post("/entries", json=payload, headers=API_KEY)
    assert r.status_code == 200 or r.status_code == 201
    data = r.json()
    assert "id" in data

    r = client.get("/entries?page=1&pageSize=10", headers=API_KEY)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


def test_validation_rating_range(client):
    """Ensure rating outside 1..5 fails validation with 422."""
    bad = {
        "url": "https://example.com/job/2",
        "rating": 10,
    }
    r = client.post("/entries", json=bad, headers=API_KEY)
    assert r.status_code == 422


def test_pagination(client):
    """Verify GET /entries respects page and pageSize parameters."""
    # create a few entries
    for i in range(3):
        client.post(
            "/entries",
            json={"url": f"https://example.com/{i}", "rating": 3},
            headers=API_KEY,
        )
    r = client.get("/entries?page=1&pageSize=2", headers=API_KEY)
    assert r.status_code == 200
    data = r.json()
    assert data["page"] == 1
    assert data["pageSize"] == 2
    assert len(data["items"]) <= 2
