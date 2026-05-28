def test_point_returns_doc03_contract(client):
    resp = client.post(
        "/assess",
        json={"geometry": {"type": "Point", "coordinates": [83.89, 28.07]}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["model_config_version"] == "2026.1"
    assert "overall" in body
    assert "class" in body["overall"]
    names = {f["name"] for f in body["factors"]}
    assert {"altitude", "temperature", "precipitation", "slope", "shading"} <= names
    # Every factor carries its weight + a provenance source block (contract is real).
    for factor in body["factors"]:
        assert "weight" in factor
        assert "source" in factor


def test_polygon_enqueues_async_job(client):
    polygon = {
        "type": "Polygon",
        "coordinates": [
            [[83.8, 28.0], [83.9, 28.0], [83.9, 28.1], [83.8, 28.1], [83.8, 28.0]]
        ],
    }
    resp = client.post("/assess", json={"geometry": polygon})
    assert resp.status_code == 202
    assert "job_id" in resp.json()
