def test_health(client):
    """Ensure the health endpoint responds 200 OK with the expected JSON body."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
