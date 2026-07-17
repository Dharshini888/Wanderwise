from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.ai_service import chat_with_assistant

router = APIRouter(prefix="/api/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    message: str
    destination: str = ""


def _chat(data: ChatRequest):
    try:
        reply = chat_with_assistant(data.message, data.destination)
        return {"reply": reply, "response": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask")
def ask(data: ChatRequest):
    return _chat(data)


@router.post("/message")
def message(data: ChatRequest):
    """Alias for /ask — matches frontend Chat.jsx call."""
    return _chat(data)