import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./triggers.db")
API_KEY = os.getenv("API_KEY", "dev-api-key")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Langfuse
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_BASE_URL = os.getenv("LANGFUSE_BASE_URL", "https://us.cloud.langfuse.com")

# Available models via OpenRouter
AVAILABLE_MODELS = {
    "claude-sonnet-4": {
        "id": "anthropic/claude-sonnet-4",
        "name": "Claude Sonnet 4",
        "cost_per_1m_input": 3.0,
        "cost_per_1m_output": 15.0,
    },
    "gpt-4o": {
        "id": "openai/gpt-4o",
        "name": "GPT-4o",
        "cost_per_1m_input": 2.50,
        "cost_per_1m_output": 10.0,
    },
    "gpt-4o-mini": {
        "id": "openai/gpt-4o-mini",
        "name": "GPT-4o Mini",
        "cost_per_1m_input": 0.15,
        "cost_per_1m_output": 0.60,
    },
    "llama-3.1-70b": {
        "id": "meta-llama/llama-3.1-70b-instruct",
        "name": "Llama 3.1 70B",
        "cost_per_1m_input": 0.50,
        "cost_per_1m_output": 0.75,
    },
    "mistral-large": {
        "id": "mistralai/mistral-large-latest",
        "name": "Mistral Large",
        "cost_per_1m_input": 2.0,
        "cost_per_1m_output": 6.0,
    },
}

DEFAULT_MODEL = "gpt-4o-mini"
