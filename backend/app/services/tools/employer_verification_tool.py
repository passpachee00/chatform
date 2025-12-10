"""
Employer Verification Tool Handler

Provides tool for verifying employer legitimacy through multiple sources.
"""

from typing import Dict, Any, Optional
from app.services.tools.base import ToolHandler
from app.services.employer_verification_service import EmployerVerificationService


class EmployerVerificationToolHandler(ToolHandler):
    """Tool for verifying employer legitimacy"""

    def __init__(self):
        self.verification_service = EmployerVerificationService()

    @property
    def name(self) -> str:
        return "verify_employer"

    def get_schema(self) -> Dict[str, Any]:
        """Return OpenAI function schema"""
        return {
            "name": self.name,
            "description": "Verify if a company/employer is legitimate by checking multiple sources (Google Sheets allowlist, Perplexity AI web search). Use this when you need to check if a company name is real or when the user provides a corrected company name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "The company name to verify (e.g., 'SCB Bank', 'Google', 'บริษัท อัลฟ่า ยูนิเทรด จำกัด')"
                    },
                    "company_website": {
                        "type": "string",
                        "description": "Optional company website URL for additional verification context",
                        "nullable": True
                    }
                },
                "required": ["company_name"],
                "additionalProperties": False
            }
        }

    async def execute(
        self,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Execute employer verification"""
        company_name = arguments["company_name"]
        company_website = arguments.get("company_website")

        # Run verification (calls existing service)
        result = await self.verification_service.verify_employer(
            company_name=company_name,
            website=company_website
        )

        # Format result
        return self._format_result(result)

    def _format_result(self, result: Dict[str, Any]) -> str:
        """Format verification result for chatbot consumption"""
        passed = result.get("passed", False)
        passed_by = result.get("passed_by", "none")
        checks = result.get("checks", {})
        perplexity_details = result.get("perplexity_details", {})

        if passed:
            message = "✅ VERIFICATION PASSED\n\n"
            message += f"The company was verified by: {passed_by}\n\n"

            if perplexity_details:
                message += "**Perplexity AI found:**\n"
                message += f"- Result: {perplexity_details.get('result', 'N/A')}\n"
                message += f"- Explanation: {perplexity_details.get('explanation', 'N/A')}\n"
                if perplexity_details.get('closest_company_name'):
                    message += f"- Official Name: {perplexity_details.get('closest_company_name')}\n"
                if perplexity_details.get('closest_company_website'):
                    message += f"- Website: {perplexity_details.get('closest_company_website')}\n"
        else:
            message = "❌ VERIFICATION FAILED\n\n"
            message += "The company could not be verified through:\n"
            message += f"- Google Sheets Allowlist: {'✓ Pass' if checks.get('google_sheet') else '✗ Fail'}\n"
            message += f"- Perplexity Web Search: {'✓ Pass' if checks.get('perplexity') else '✗ Fail'}\n\n"

            if perplexity_details:
                message += "**Perplexity AI Response:**\n"
                message += f"{perplexity_details.get('explanation', 'No explanation available')}\n"

        return message
