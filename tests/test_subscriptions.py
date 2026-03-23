def test_create_subscription(client, sample_subscription):
    response = client.post("/api/v1/subscriptions", json=sample_subscription)
    assert response.status_code == 201
    sub = response.json()
    assert sub["id"].startswith("sub_")
    assert sub["name"] == "Test Webhook"
    assert sub["status"] == "active"
    assert sub["retry_enabled"] is True


def test_list_subscriptions(client, sample_subscription):
    client.post("/api/v1/subscriptions", json=sample_subscription)
    client.post(
        "/api/v1/subscriptions",
        json={**sample_subscription, "name": "Another Webhook"},
    )

    response = client.get("/api/v1/subscriptions")
    assert response.status_code == 200
    subs = response.json()
    assert len(subs) == 2


def test_list_subscriptions_filter_by_status(client, sample_subscription):
    client.post("/api/v1/subscriptions", json=sample_subscription)

    response = client.get("/api/v1/subscriptions?status=active")
    subs = response.json()
    assert len(subs) == 1

    response = client.get("/api/v1/subscriptions?status=paused")
    subs = response.json()
    assert len(subs) == 0


def test_get_subscription(client, sample_subscription):
    create_resp = client.post("/api/v1/subscriptions", json=sample_subscription)
    sub_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/subscriptions/{sub_id}")
    assert response.status_code == 200
    sub = response.json()
    assert sub["id"] == sub_id
    assert sub["event_types"] == ["order.created"]


def test_get_subscription_not_found(client):
    response = client.get("/api/v1/subscriptions/sub_nonexistent")
    assert response.status_code == 404


def test_update_subscription(client, sample_subscription):
    create_resp = client.post("/api/v1/subscriptions", json=sample_subscription)
    sub_id = create_resp.json()["id"]

    response = client.patch(
        f"/api/v1/subscriptions/{sub_id}",
        json={"name": "Updated Webhook", "status": "paused"},
    )
    assert response.status_code == 200
    sub = response.json()
    assert sub["name"] == "Updated Webhook"
    assert sub["status"] == "paused"


def test_update_subscription_not_found(client):
    response = client.patch(
        "/api/v1/subscriptions/sub_nonexistent",
        json={"name": "Updated"},
    )
    assert response.status_code == 404


def test_delete_subscription(client, sample_subscription):
    create_resp = client.post("/api/v1/subscriptions", json=sample_subscription)
    sub_id = create_resp.json()["id"]

    response = client.delete(f"/api/v1/subscriptions/{sub_id}")
    assert response.status_code == 204

    # Verify deleted
    response = client.get(f"/api/v1/subscriptions/{sub_id}")
    assert response.status_code == 404


def test_delete_subscription_not_found(client):
    response = client.delete("/api/v1/subscriptions/sub_nonexistent")
    assert response.status_code == 404


def test_subscription_deliveries_empty(client, sample_subscription):
    create_resp = client.post("/api/v1/subscriptions", json=sample_subscription)
    sub_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/subscriptions/{sub_id}/deliveries")
    assert response.status_code == 200
    assert response.json() == []


def test_create_subscription_minimal(client):
    response = client.post(
        "/api/v1/subscriptions",
        json={
            "name": "Minimal Sub",
            "endpoint_url": "https://example.com/hook",
        },
    )
    assert response.status_code == 201
    sub = response.json()
    assert sub["event_types"] is None
    assert sub["sources"] is None
