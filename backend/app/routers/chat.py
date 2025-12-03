"""
Chat router for handling chatbot conversations
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging

from app.schemas.application import (
    ChatMessageRequest,
    ChatMessageResponse,
)
from app.services.chat_service import ChatService

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat/message", response_model=ChatMessageResponse)
async def send_chat_message(request: ChatMessageRequest):
    """
    Handle chat message and return AI response

    Args:
        request: Chat message request with user message, red flag, and context

    Returns:
        Chat message response with assistant's message

    Raises:
        HTTPException: If chat service fails
    """
    try:
        # Initialize chat service
        service = ChatService()

        # Send message and get response
        response_content = await service.send_message(
            user_message=request.message,
            red_flag=request.redFlag,
            app_data=request.applicationData,
            conversation_history=request.conversationHistory,
        )

        # Return successful response
        return ChatMessageResponse(
            role="assistant",
            content=response_content,
            timestamp=datetime.utcnow(),
            status="success",
        )

    except ValueError as e:
        # Handle validation errors
        logger.error(f"Validation error in chat: {e}")
        return ChatMessageResponse(
            role="assistant",
            content="I'm sorry, but I encountered an issue processing your request. Please try again.",
            timestamp=datetime.utcnow(),
            status="error",
            error=str(e),
        )

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in chat: {e}", exc_info=True)
        return ChatMessageResponse(
            role="assistant",
            content="I'm sorry, but something went wrong. Please try again later.",
            timestamp=datetime.utcnow(),
            status="error",
            error="Internal server error",
        )
