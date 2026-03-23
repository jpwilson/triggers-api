def test_get_inbox_empty(client):
    response = client.get("/api/v1/inbox")
    assert response.status_code == 200
    data = response.json()
    assert data["events"] == []
    assert data["count"] == 0


def test_get_inbox_with_events(client, sample_event):
    client.post("/api/v1/events", json=sample_event)
    client.post("/api/v1/events", json=sample_event)

    response = client.get("/api/v1/inbox")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert len(data["events"]) == 2


def test_get_inbox_filter_by_type(client, sample_event):
    client.post("/api/v1/events", json=sample_event)
    client.post(
        "/api/v1/events",
        json={**sample_event, "event_type": "payment.completed"},
    )

    response = client.get("/api/v1/inbox?event_type=order.created")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1


def test_get_inbox_filter_by_source(client, sample_event):
    client.post("/api/v1/events", json=sample_event)
    client.post(
        "/api/v1/events",
        json={**sample_event, "source": "stripe"},
    )

    response = client.get("/api/v1/inbox?source=shopify")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1


def test_acknowledge_events(client, sample_event):
    # Ingest events
    resp1 = client.post("/api/v1/events", json=sample_event)
    resp2 = client.post("/api/v1/events", json=sample_event)
    event_id1 = resp1.json()["event_id"]
    event_id2 = resp2.json()["event_id"]

    # Acknowledge
    response = client.post(
        "/api/v1/inbox/ack",
        json={"event_ids": [event_id1, event_id2]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert event_id1 in data["acknowledged"]
    assert event_id2 in data["acknowledged"]

    # Verify inbox is now empty
    inbox_resp = client.get("/api/v1/inbox")
    assert inbox_resp.json()["count"] == 0


def test_acknowledge_nonexistent_events(client):
    response = client.post(
        "/api/v1/inbox/ack",
        json={"event_ids": ["evt_nonexistent"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0


def test_acknowledge_already_delivered(client, sample_event):
    resp = client.post("/api/v1/events", json=sample_event)
    event_id = resp.json()["event_id"]

    # Ack once
    client.post("/api/v1/inbox/ack", json={"event_ids": [event_id]})

    # Ack again - should not count
    response = client.post("/api/v1/inbox/ack", json={"event_ids": [event_id]})
    data = response.json()
    assert data["count"] == 0


def test_inbox_pagination(client, sample_event):
    for _ in range(5):
        client.post("/api/v1/events", json=sample_event)

    response = client.get("/api/v1/inbox?limit=3")
    data = response.json()
    assert data["count"] == 3
    assert data["next_cursor"] is not None
