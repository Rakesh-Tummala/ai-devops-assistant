def test_health_check_requires_no_key(client):
    client.headers.pop("X-App-Key", None)
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "Running"


def test_protected_route_rejects_missing_key(client):
    client.headers.pop("X-App-Key", None)
    resp = client.get("/deployment-status/")
    assert resp.status_code == 401


def test_protected_route_rejects_wrong_key(client):
    client.headers.update({"X-App-Key": "wrong-key"})
    resp = client.get("/deployment-status/")
    assert resp.status_code == 401


def test_protected_route_accepts_correct_key(client):
    resp = client.get("/deployment-status/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "Idle"
