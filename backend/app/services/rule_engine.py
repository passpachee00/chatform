from app.schemas.application import ApplicationData, RedFlag
from app.services.distance_service import DistanceService
from app.services.blacklist_service import BlacklistService
from typing import List


class RuleEngine:
    """Rule engine to validate application data"""

    def __init__(self):
        self.distance_service = DistanceService()
        self.blacklist_service = BlacklistService()

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

        # Geocode addresses to get coordinates
        current_coords = await self.distance_service.geocode_address(current_addr)
        company_coords = await self.distance_service.geocode_address(company_addr)

        # Calculate distance
        is_within_limit, distance = await self.distance_service.check_distance_within_limit(
            current_addr,
            company_addr,
            limit_km=150.0
        )

        # Prepare debug info
        debug_info = {
            "currentAddress": {
                "address": current_addr,
                "lat": current_coords[0] if current_coords else None,
                "lng": current_coords[1] if current_coords else None
            },
            "companyAddress": {
                "address": company_addr,
                "lat": company_coords[0] if company_coords else None,
                "lng": company_coords[1] if company_coords else None
            },
            "distance_km": distance
        }

        # If we couldn't calculate distance (geocoding failed)
        if distance is None:
            return RedFlag(
                rule="distance_check",
                message="Could not verify addresses. Please ensure both addresses are valid.",
                affectedFields=["currentAddress", "companyAddress"],
                debugInfo=debug_info
            )

        # If distance exceeds limit
        if not is_within_limit:
            return RedFlag(
                rule="distance_check",
                message=f"Home and work addresses are {distance:.1f}km apart (limit: 150km)",
                affectedFields=["currentAddress", "companyAddress"],
                debugInfo=debug_info
            )

        # Distance is within limit - pass (return None for pass, but we could return debug info too)
        return None

    async def check_blacklist_rule(self, data: ApplicationData) -> RedFlag | None:
        """
        Check if applicant's name appears in blacklist

        Args:
            data: Application data

        Returns:
            RedFlag if name is blacklisted, None if passes
        """
        first_name = data.firstName
        last_name = data.lastName

        # Skip if either name is missing
        if not first_name or not last_name:
            return None

        # Check if name is blacklisted
        is_blacklisted = await self.blacklist_service.is_blacklisted(
            first_name,
            last_name
        )

        if is_blacklisted:
            return RedFlag(
                rule="blacklist_check",
                message=f"Name '{first_name} {last_name}' appears in restricted list",
                affectedFields=["firstName", "lastName"]
            )

        # Name not blacklisted - pass
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

        # Run blacklist check
        blacklist_flag = await self.check_blacklist_rule(data)
        if blacklist_flag:
            red_flags.append(blacklist_flag)

        # Run distance check
        distance_flag = await self.check_distance_rule(data)
        if distance_flag:
            red_flags.append(distance_flag)

        # Add more rules here in the future
        # e.g., company_exists_flag = await self.check_company_exists(data)

        return red_flags
