def test_ingest_event(client, sample_event):
    response = client.post("/api/v1/events", json=sample_event)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "accepted"
    assert data["event_id"].startswith("evt_")
    assert "received_at" in data


def test_ingest_event_missing_fields(client):
    response = client.post("/api/v1/events", json={"event_type": "test"})
    assert response.status_code == 422


def test_list_events(client, sample_event):
    # Ingest a few events
    client.post("/api/v1/events", json=sample_event)
    client.post("/api/v1/events", json=sample_event)

    response = client.get("/api/v1/events")
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 2


def test_list_events_filter_by_type(client, sample_event):
    client.post("/api/v1/events", json=sample_event)
    client.post(
        "/api/v1/events",
        json={**sample_event, "event_type": "order.updated"},
    )

    response = client.get("/api/v1/events?event_type=order.created")
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 1
    assert events[0]["event_type"] == "order.created"


def test_list_events_filter_by_source(client, sample_event):
    client.post("/api/v1/events", json=sample_event)
    client.post(
        "/api/v1/events",
        json={**sample_event, "source": "stripe"},
    )

    response = client.get("/api/v1/events?source=shopify")
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 1
    assert events[0]["source"] == "shopify"


def test_get_event(client, sample_event):
    create_resp = client.post("/api/v1/events", json=sample_event)
    event_id = create_resp.json()["event_id"]

    response = client.get(f"/api/v1/events/{event_id}")
    assert response.status_code == 200
    event = response.json()
    assert event["id"] == event_id
    assert event["event_type"] == "order.created"
    assert event["source"] == "shopify"
    assert event["payload"]["order_id"] == "12345"


def test_get_event_not_found(client):
    response = client.get("/api/v1/events/evt_nonexistent")
    assert response.status_code == 404


def test_delete_event(client, sample_event):
    create_resp = client.post("/api/v1/events", json=sample_event)
    event_id = create_resp.json()["event_id"]

    response = client.delete(f"/api/v1/events/{event_id}")
    assert response.status_code == 204

    # Verify deleted
    response = client.get(f"/api/v1/events/{event_id}")
    assert response.status_code == 404


def test_delete_event_not_found(client):
    response = client.delete("/api/v1/events/evt_nonexistent")
    assert response.status_code == 404


def test_ingest_event_with_timestamp(client, sample_event):
    sample_event["timestamp"] = "2024-01-15T10:30:00Z"
    response = client.post("/api/v1/events", json=sample_event)
    assert response.status_code == 201


def test_list_events_with_limit(client, sample_event):
    for _ in range(5):
        client.post("/api/v1/events", json=sample_event)

    response = client.get("/api/v1/events?limit=3")
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 3
