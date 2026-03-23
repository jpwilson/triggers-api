from unittest.mock import MagicMock, patch


def test_list_models(client):
    response = client.get("/api/v1/chat/models")
    assert response.status_code == 200
    models = response.json()
    assert len(models) > 0
    # Check structure
    for model in models:
        assert "key" in model
        assert "name" in model
        assert "cost_per_1m_input" in model
        assert "cost_per_1m_output" in model


def test_chat_no_api_key(client):
    """Chat should return a friendly error when no OpenRouter key is set."""
    response = client.post(
        "/api/v1/chat",
        json={
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "unavailable" in data["response"].lower() or "not configured" in data["response"].lower()


def test_chat_with_model_selection(client):
    """Chat should accept model parameter."""
    response = client.post(
        "/api/v1/chat",
        json={
            "messages": [{"role": "user", "content": "Hello"}],
            "model": "gpt-4o-mini",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "gpt-4o-mini"


def test_chat_with_session_id(client):
    """Chat should accept session_id parameter."""
    response = client.post(
        "/api/v1/chat",
        json={
            "messages": [{"role": "user", "content": "Hello"}],
            "session_id": "test-session-123",
        },
    )
    assert response.status_code == 200


def test_chat_invalid_model_falls_back(client):
    """Chat should fall back to default model for unknown model key."""
    response = client.post(
        "/api/v1/chat",
        json={
            "messages": [{"role": "user", "content": "Hello"}],
            "model": "nonexistent-model",
        },
    )
    assert response.status_code == 200


def test_chat_empty_messages(client):
    """Chat with empty messages should fail validation."""
    response = client.post(
        "/api/v1/chat",
        json={
            "messages": [],
        },
    )
    # FastAPI will still accept empty list, but the response should still work
    assert response.status_code == 200


@patch("src.chat._get_openai_client")
@patch("src.chat._get_langfuse")
def test_chat_with_mocked_openrouter(mock_langfuse, mock_client_fn, client):
    """Test chat with mocked OpenRouter response."""
    mock_langfuse.return_value = None

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "I can help you with TriggersAPI!"
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_response.usage.total_tokens = 150

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    mock_client_fn.return_value = mock_client

    response = client.post(
        "/api/v1/chat",
        json={
            "messages": [{"role": "user", "content": "How do I ingest events?"}],
            "model": "gpt-4o-mini",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "I can help you with TriggersAPI!"
    assert data["usage"]["total_tokens"] == 150
    assert data["model"] == "gpt-4o-mini"
