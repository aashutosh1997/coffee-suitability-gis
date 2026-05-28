def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_version_reports_config_version(client):
    resp = client.get("/version")
    assert resp.status_code == 200
    body = resp.json()
    assert body["model_config_version"] == "2026.1"
    assert "version" in body
