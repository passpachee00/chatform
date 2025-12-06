"""
Pre-screening chat router for gathering political exposure information
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import datetime

router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message model"""
    role: Literal["user", "assistant"]
    content: str
    timestamp: Optional[datetime] = None


class PreScreeningChatRequest(BaseModel):
    """Request for pre-screening chat"""
    message: str
    conversationHistory: List[ChatMessage] = []


class PreScreeningChatResponse(BaseModel):
    """Response from pre-screening chat"""
    role: Literal["assistant"]
    content: str
    timestamp: datetime


@router.post("/prescreening/chat", response_model=PreScreeningChatResponse)
async def prescreening_chat(request: PreScreeningChatRequest):
    """
    Handle pre-screening chat conversation

    This endpoint gathers information about political exposure for AI review
    """
    try:
        from app.services.chat_service import ChatService

        chat_service = ChatService()

        # System prompt focused on gathering information for review agent
        system_prompt = """You are a helpful assistant gathering information for a pre-screening questionnaire.

The applicant has indicated they may fall into one of two categories:
1. They are a US citizen, OR
2. They or an immediate family member holds a political or government position.

Your job is to:
- Determine whether either category applies.
- If neither applies, confirm that and conclude. Ask clear, specific follow-up questions to gather relevant details for the AI review agent
- Understand their specific situation 
- Do NOT ask about relatives unless the applicant mentions them.
- Be professional, concise, and friendly
- When you have gathered sufficient information, thank the customer and acknowledge you have received enough details
- If unsure restate what you know and ask them to confirm
Keep responses brief and focused. The information you collect will be passed to a review agent."""


        # Build message array for OpenAI
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history
        for msg in request.conversationHistory:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # Add current user message
        messages.append({
            "role": "user",
            "content": request.message
        })

        # Get response from ChatService
        response_content = await chat_service.get_completion(messages)

        return PreScreeningChatResponse(
            role="assistant",
            content=response_content,
            timestamp=datetime.now()
        )

    except Exception as e:
        print(f"Error in prescreening chat: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat message: {str(e)}"
        )
