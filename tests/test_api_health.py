"""Health endpoint."""

from anchorprune import __version__


def test_health_endpoint(api_client):
    resp = api_client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["version"] == __version__
