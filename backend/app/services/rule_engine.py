from app.schemas.application import ApplicationData, RedFlag
from app.services.distance_service import DistanceService
from app.services.blacklist_service import BlacklistService
from app.services.employer_verification_service import EmployerVerificationService
from typing import List
import asyncio


# Source of Funds alignment matrix
# Maps employment type -> allowed source of funds
SOURCE_OF_FUNDS_ALIGNMENT = {
    "Business Owner": ["Inheritance", "Savings", "Investments", "Pension", "Business Income"],
    "Government Officer": ["Salary", "Inheritance", "Savings", "Investments", "Pension"],
    "Self-Employed": ["Inheritance", "Savings", "Investments", "Pension", "Business Income"],
    "State Enterprise Officer": ["Salary", "Inheritance", "Savings", "Investments", "Pension"],
    "Freelancer": ["Inheritance", "Savings", "Investments", "Pension", "Salary"],
    "Student": ["Inheritance", "Savings", "Investments"],
    "Company Employee": ["Salary", "Inheritance", "Savings", "Investments"],
    "Politician": ["Salary", "Inheritance", "Savings", "Investments", "Pension"],
    "Unemployed": ["Inheritance", "Savings", "Investments", "Pension"],
}


class RuleEngine:
    """Rule engine to validate application data"""

    def __init__(self):
        self.distance_service = DistanceService()
        self.blacklist_service = BlacklistService()
        self.employer_verification_service = EmployerVerificationService()

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

    async def check_political_exposure_rule(self, data: ApplicationData) -> RedFlag | None:
        """
        Check if applicant has political exposure requiring review

        Args:
            data: Application data

        Returns:
            RedFlag if political exposure detected, None otherwise
        """
        # Get pre-screening data
        pre_screening = data.preScreening

        # Skip if not answered or answered "no"
        if not pre_screening or pre_screening.response != 'yes':
            return None

        # If answered "yes", always flag for manual review
        # (even if explanation provided - compliance requirement)
        explanation_preview = pre_screening.explanation[:100] if pre_screening.explanation else ""

        return RedFlag(
            rule="political_exposure_check",
            message=f"Applicant indicated political exposure: {explanation_preview}...",
            affectedFields=["preScreening"],
            debugInfo={
                "response": pre_screening.response,
                "explanation": pre_screening.explanation,
                "chatMessageCount": len(pre_screening.chatHistory) if pre_screening.chatHistory else 0
            }
        )

    async def check_employer_verification_rule(self, data: ApplicationData) -> RedFlag | None:
        """
        Verify employer legitimacy through multiple sources

        Args:
            data: Application data

        Returns:
            RedFlag if employer cannot be verified, None if passes
        """
        company_name = data.companyName
        company_website = data.companyWebsite

        # Skip if company name is missing
        if not company_name or not company_name.strip():
            return None

        # Run verification
        result = await self.employer_verification_service.verify_employer(
            company_name,
            company_website
        )

        if not result["passed"]:
            return RedFlag(
                rule="employer_verification_check",
                message=f"Could not verify employer '{company_name}'",
                affectedFields=["companyName", "companyWebsite"],
                debugInfo=result
            )

        # Verification passed
        return None

    async def check_source_of_funds_alignment_rule(self, data: ApplicationData) -> RedFlag | None:
        """
        Check if source of funds aligns with employment type

        Args:
            data: Application data

        Returns:
            RedFlag if misalignment detected, None if passes
        """
        employment_type = data.employmentType
        source_of_funds = data.sourceOfFunds

        # Skip if either field is missing or empty
        if not employment_type or not employment_type.strip():
            return None
        if not source_of_funds or not source_of_funds.strip():
            return None

        # Normalize
        employment_type = employment_type.strip()
        source_of_funds = source_of_funds.strip()

        # Check employment type exists in matrix
        if employment_type not in SOURCE_OF_FUNDS_ALIGNMENT:
            return RedFlag(
                rule="source_of_funds_alignment_check",
                message=f"Unable to validate source of funds alignment for employment type '{employment_type}'",
                affectedFields=["employmentType", "sourceOfFunds"],
                debugInfo={"employmentType": employment_type, "sourceOfFunds": source_of_funds, "reason": "unknown_employment_type"}
            )

        allowed_sources = SOURCE_OF_FUNDS_ALIGNMENT[employment_type]

        # Check if source of funds is in allowed list
        if source_of_funds not in allowed_sources:
            return RedFlag(
                rule="source_of_funds_alignment_check",
                message=f"The source of funds '{source_of_funds}' doesn't typically align with employment type '{employment_type}'. Can you provide more details?",
                affectedFields=["employmentType", "sourceOfFunds"],
                debugInfo={"employmentType": employment_type, "sourceOfFunds": source_of_funds, "allowedSources": allowed_sources}
            )

        return None

    async def validate(self, data: ApplicationData) -> List[RedFlag]:
        """
        Run all validation rules on application data in parallel

        Args:
            data: Application data to validate

        Returns:
            List of red flags (empty if all rules pass)
        """
        # Run all validation rules in parallel for better performance
        results = await asyncio.gather(
            self.check_blacklist_rule(data),
            self.check_employer_verification_rule(data),
            self.check_distance_rule(data),
            self.check_political_exposure_rule(data),
            self.check_source_of_funds_alignment_rule(data),
        )

        # Filter out None values (passed validations)
        red_flags = [flag for flag in results if flag is not None]

        return red_flags
