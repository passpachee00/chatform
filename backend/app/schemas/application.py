from pydantic import BaseModel
from typing import Optional


class ApplicationData(BaseModel):
    """Application form data"""
    currentAddress: Optional[str] = None
    occupation: Optional[str] = None
    jobTitle: Optional[str] = None
    companyName: Optional[str] = None
    companyAddress: Optional[str] = None
    monthlyIncome: Optional[float] = None
    incomeSource: Optional[str] = None
    currentAssets: Optional[float] = None
    countryIncomeSources: Optional[str] = None


class RedFlag(BaseModel):
    """Red flag structure"""
    rule: str
    message: str
    affectedFields: list[str]


class ValidationResponse(BaseModel):
    """Response from validation endpoint"""
    red_flags: list[RedFlag]
