from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.chat import chat_completion, get_available_models

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="Conversation messages")
    model: Optional[str] = Field(None, description="Model key (e.g., 'gpt-4o-mini')")
    session_id: Optional[str] = Field(None, description="Session ID for tracing")


@router.post("", response_model=Dict[str, Any])
async def send_chat_message(request: ChatRequest):
    """Send a message to the TriggersAPI assistant.

    The assistant is scoped to help with TriggersAPI usage — event ingestion,
    delivery, subscriptions, and debugging.
    """
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    result = chat_completion(
        messages=messages,
        model_key=request.model,
        session_id=request.session_id,
    )
    return result


@router.get("/models", response_model=List[Dict[str, Any]])
async def list_models():
    """List available LLM models and their costs."""
    return get_available_models()
