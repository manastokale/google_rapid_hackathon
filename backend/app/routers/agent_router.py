"""Agent chat endpoint."""

from fastapi import APIRouter

from app.agent.runner import run_agent_query
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    result = await run_agent_query(request.message, request.session_id)
    return ChatResponse(**result)

