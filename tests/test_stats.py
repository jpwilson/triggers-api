def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "triggers-api"


def test_stats_empty(client):
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_events"] == 0
    assert data["total_subscriptions"] == 0
    assert data["success_rate"] == 100.0


def test_stats_with_events(client, sample_event):
    client.post("/api/v1/events", json=sample_event)
    client.post("/api/v1/events", json=sample_event)
    client.post("/api/v1/events", json=sample_event)

    response = client.get("/api/v1/stats")
    data = response.json()
    assert data["total_events"] == 3


def test_stats_with_subscriptions(client, sample_subscription):
    client.post("/api/v1/subscriptions", json=sample_subscription)

    response = client.get("/api/v1/stats")
    data = response.json()
    assert data["total_subscriptions"] == 1
    assert data["active_subscriptions"] == 1
