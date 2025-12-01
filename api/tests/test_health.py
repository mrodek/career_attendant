def test_given_request_when_health_check_then_returns_ok_status(client):
    """Ensure the health endpoint responds 200 OK with status ok."""
    # Arrange - simple GET request

    # Act
    r = client.get("/health")

    # Assert
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    # Health endpoint also returns dev_mode and clerk_frontend_api
    assert "dev_mode" in data
