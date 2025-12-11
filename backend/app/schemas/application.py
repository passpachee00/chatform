from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import datetime


class PreScreeningData(BaseModel):
    """Pre-screening data structure"""
    response: Literal["yes", "no"]
    explanation: str
    chatHistory: List[dict]  # List of ChatMessage dicts


class ApplicationData(BaseModel):
    """Application form data"""
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    currentAddress: Optional[str] = None
    employmentType: Optional[str] = None
    jobTitle: Optional[str] = None
    companyName: Optional[str] = None
    companyAddress: Optional[str] = None
    companyWebsite: Optional[str] = None
    monthlyIncome: Optional[float] = None
    sourceOfFunds: Optional[str] = None
    currentAssets: Optional[float] = None
    countryIncomeSources: Optional[str] = None

    # Pre-screening field
    preScreening: Optional[PreScreeningData] = None


class RedFlag(BaseModel):
    """Red flag structure"""
    rule: str
    message: str
    affectedFields: list[str]
    debugInfo: Optional[dict] = None  # Additional debug information


class ValidationResponse(BaseModel):
    """Response from validation endpoint"""
    red_flags: list[RedFlag]


# Chat-related schemas
class ChatMessage(BaseModel):
    """Single chat message"""
    role: Literal["user", "assistant"]
    content: str
    timestamp: Optional[datetime] = None


class ChatMessageRequest(BaseModel):
    """Request to send chat message"""
    message: str
    redFlag: RedFlag
    applicationData: ApplicationData
    conversationHistory: list[ChatMessage] = []


class ChatMessageResponse(BaseModel):
    """Response from chat endpoint"""
    role: Literal["assistant"]
    content: str
    timestamp: datetime
    status: Literal["success", "error"]
    error: Optional[str] = None
