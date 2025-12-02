from app.schemas.application import ApplicationData, RedFlag
from app.services.distance_service import DistanceService
from typing import List


class RuleEngine:
    """Rule engine to validate application data"""

    def __init__(self):
        self.distance_service = DistanceService()

    async def check_distance_rule(self, data: ApplicationData) -> RedFlag | None:
        """
        Check if home and work addresses are within 150km

        Args:
            data: Application data

        Returns:
            RedFlag if validation fails, None if passes
        """
        current_addr = data.currentAddress
        company_addr = data.companyAddress

        # Skip if either address is missing
        if not current_addr or not company_addr:
            return None

        # Calculate distance using distance service
        is_within_limit, distance = await self.distance_service.check_distance_within_limit(
            current_addr,
            company_addr,
            limit_km=150.0
        )

        # If we couldn't calculate distance (geocoding failed)
        if distance is None:
            return RedFlag(
                rule="distance_check",
                message="Could not verify addresses. Please ensure both addresses are valid.",
                affectedFields=["currentAddress", "companyAddress"]
            )

        # If distance exceeds limit
        if not is_within_limit:
            return RedFlag(
                rule="distance_check",
                message=f"Home and work addresses are {distance:.1f}km apart (limit: 150km)",
                affectedFields=["currentAddress", "companyAddress"]
            )

        # Distance is within limit - pass
        return None

    async def validate(self, data: ApplicationData) -> List[RedFlag]:
        """
        Run all validation rules on application data

        Args:
            data: Application data to validate

        Returns:
            List of red flags (empty if all rules pass)
        """
        red_flags = []

        # Run distance check
        distance_flag = await self.check_distance_rule(data)
        if distance_flag:
            red_flags.append(distance_flag)

        # Add more rules here in the future
        # e.g., company_exists_flag = await self.check_company_exists(data)

        return red_flags
