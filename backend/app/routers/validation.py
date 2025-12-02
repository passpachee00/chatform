from fastapi import APIRouter
from app.schemas.application import ApplicationData, ValidationResponse
from app.services.rule_engine import RuleEngine

router = APIRouter()


@router.post("/validate", response_model=ValidationResponse)
async def validate_application(data: ApplicationData):
    """
    Validate application data and return red flags

    Args:
        data: Application form data

    Returns:
        ValidationResponse with list of red flags
    """
    rule_engine = RuleEngine()
    red_flags = await rule_engine.validate(data)

    return ValidationResponse(red_flags=red_flags)
