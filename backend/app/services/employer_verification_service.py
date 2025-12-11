"""
Employer Verification Service

Validates employer legitimacy through three independent sources:
1. Google Sheets Allowlist - Internal trusted company list
2. DataForThai Registry - Thailand business registry
3. Perplexity Web Search - AI-powered web validation

Logic: If ANY check passes → PASS | If ALL checks fail → FAIL
"""

import httpx
import csv
import io
import os
import asyncio
from typing import Optional, Dict, Any, Set
from datetime import datetime, timedelta


class EmployerVerificationService:
    """Service to verify employer legitimacy through multiple sources"""

    def __init__(self):
        # Google Sheets allowlist cache
        self.allowlist: Set[str] = set()
        self.last_fetch: Optional[datetime] = None
        self.cache_duration = timedelta(hours=1)
        self.sheet_url = os.getenv(
            "EMPLOYER_ALLOWLIST_SHEET_URL",
            "https://docs.google.com/spreadsheets/d/1FIZ9GabtynZvnaXAcqaTtUG3hM1M4mt95gFc3YgxC9k/export?format=csv"
        )

        # Perplexity API
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        self.perplexity_model = "sonar"

    async def fetch_allowlist(self) -> Set[str]:
        """
        Fetch employer allowlist from Google Sheets CSV export

        Returns:
            Set of company names in lowercase
        """
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(self.sheet_url, timeout=10.0)
                response.raise_for_status()

                # Parse CSV content
                csv_content = response.text
                print(f"[Employer Allowlist] CSV Content:\n{csv_content}")
                csv_reader = csv.DictReader(io.StringIO(csv_content))

                allowlist = set()
                for row in csv_reader:
                    # Strip whitespace from keys and normalize to lowercase for case-insensitive matching
                    row_cleaned = {k.strip().lower(): v for k, v in row.items()}
                    company_name = row_cleaned.get("company_name", "").strip().lower()

                    if company_name:
                        allowlist.add(company_name)

                print(f"✓ Employer allowlist fetched: {len(allowlist)} entries")
                print(f"  Allowlist contents: {allowlist}")
                return allowlist

        except Exception as e:
            print(f"Error fetching employer allowlist: {e}")
            return set()

    async def refresh_cache_if_needed(self) -> None:
        """
        Refresh allowlist cache if expired or empty
        """
        now = datetime.now()

        if (not self.allowlist or
            self.last_fetch is None or
            now - self.last_fetch > self.cache_duration):

            self.allowlist = await self.fetch_allowlist()
            self.last_fetch = now

    async def check_google_sheet_allowlist(self, company_name: str) -> bool:
        """
        Check if company is in Google Sheets allowlist

        Args:
            company_name: Company name to check

        Returns:
            True if found in allowlist, False otherwise
        """
        try:
            # Refresh cache if needed
            await self.refresh_cache_if_needed()

            # Normalize to lowercase for case-insensitive matching
            company_name_lower = company_name.strip().lower()

            # Check if in allowlist
            is_allowed = company_name_lower in self.allowlist
            print(f"[Google Sheet Check] '{company_name}' -> {'PASS' if is_allowed else 'FAIL'}")
            return is_allowed

        except Exception as e:
            print(f"Error in Google Sheet check: {e}")
            return False

    async def check_dataforthai_registry(self, company_name: str) -> bool:
        """
        Check if company exists in DataForThai business registry

        Args:
            company_name: Company name to search

        Returns:
            True if company found, False otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                # DataForThai API requires specific headers (especially referer and x-requested-with)
                response = await client.post(
                    "https://www.dataforthai.com/api/company",
                    data={
                        "mode": "search_comp",
                        "data[searchtext]": company_name
                    },
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                        "Accept": "application/json, text/javascript, */*; q=0.01",
                        "Referer": f"https://www.dataforthai.com/business/search/{company_name}",
                        "X-Requested-With": "XMLHttpRequest",
                        "Origin": "https://www.dataforthai.com",
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
                    },
                    timeout=10.0
                )
                response.raise_for_status()

                data = response.json()

                # Check if search was successful and returned results
                is_found = (
                    data.get("status") == "1" and
                    isinstance(data.get("data"), list) and
                    len(data.get("data", [])) > 0
                )

                if is_found:
                    print(f"[DataForThai Check] '{company_name}' -> PASS (found {len(data['data'])} matches)")
                    print(f"  First match: {data['data'][0].get('jp_tname', 'N/A')}")
                else:
                    print(f"[DataForThai Check] '{company_name}' -> FAIL (no matches)")

                return is_found

        except Exception as e:
            print(f"Error in DataForThai check: {e}")
            return False

    async def check_perplexity_web(self, company_name: str, website: Optional[str], additional_context: Optional[str] = None) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if company appears legitimate via Perplexity web search
        using JSON structured output for Thailand securities broker compliance

        Args:
            company_name: Company name to verify
            website: Optional company website for additional context
            additional_context: Optional additional details (address, industry, what they do, etc.)

        Returns:
            Tuple of (is_legitimate: bool, response_data: dict or None)
        """
        if not self.perplexity_api_key:
            print("[Perplexity Check] API key not configured, skipping")
            return False, None

        try:
            # System prompt with Thailand securities broker context
            system_prompt = """You are assisting a licensed securities broker in Thailand to verify a client's declared occupation and employer from their trading account application.
Your current task is ONLY to decide whether the given employer is a legitimate business entity.

Use reliable public web sources such as:
- Google and Google Maps
- Company website and credible news sources
- Thailand DBD (Department of Business Development)
- DataForThai
- SET and SEC registries
- Well-known international business directories (Bloomberg, Reuters, Crunchbase, LinkedIn company pages)
- Other trusted Thai business registries

Guidelines:
- Consider a business legitimate if there is clear, consistent evidence that it exists as a real company or registered business entity.
- If the name is too generic, ambiguous, or refers to multiple different entities and you cannot tell which one the client means, treat it as NO.
- If you find strong evidence it is a scam, fake company, or unrelated to a business, treat it as NO.
- When information is limited or conflicting, err on the side of NO rather than guessing.
- Companies outside Thailand must have a possibility of a presence in Thailand. Use common sense: a local bakery in rural America would be NO, but a Malaysia software company would be YES.

**Securities Industry Exclusion:**
- Companies in the securities/brokerage industry must be NO (regulatory requirement)

You must return the result as a JSON object with this structure:
{
  "result": "YES or NO in uppercase",
  "explanation": "short explanation of why you decided YES or NO, referencing the evidence used",
  "closest_company_name": "the closest matching company name you found, or null if none",
  "closest_company_website": "the main website of the closest matching company, or null if none"
}

Follow the JSON structure exactly. Do not include any fields other than these four."""

            # User message
            website_text = f"Their website is: {website}." if website else ""
            context_text = f"Additional context: {additional_context}." if additional_context else ""
            user_message = f'Company name: "{company_name}".\n{website_text}\n{context_text}'.strip()

            # JSON schema for structured output
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "result": {
                                "type": "string",
                                "enum": ["YES", "NO"]
                            },
                            "explanation": {
                                "type": "string"
                            },
                            "closest_company_name": {
                                "type": ["string", "null"]
                            },
                            "closest_company_website": {
                                "type": ["string", "null"]
                            }
                        },
                        "required": ["result", "explanation"],
                        "additionalProperties": False
                    }
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    json={
                        "model": self.perplexity_model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message}
                        ],
                        "max_tokens": 256,
                        "temperature": 0.0,
                        "response_format": response_format
                    },
                    headers={
                        "Authorization": f"Bearer {self.perplexity_api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=15.0
                )
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"]

                # Parse JSON response
                import json
                result_data = json.loads(content)

                # Only YES passes
                is_legitimate = result_data.get("result") == "YES"

                print(f"[Perplexity Check] '{company_name}' -> {'PASS' if is_legitimate else 'FAIL'}")
                print(f"  Result: {result_data.get('result')}")
                print(f"  Explanation: {result_data.get('explanation', 'N/A')[:100]}...")
                if result_data.get("closest_company_name"):
                    print(f"  Matched: {result_data.get('closest_company_name')}")

                return is_legitimate, result_data

        except Exception as e:
            print(f"Error in Perplexity check: {e}")
            return False, None

    async def verify_employer(
        self,
        company_name: str,
        website: Optional[str] = None,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify employer through two sources in parallel

        Args:
            company_name: Company name to verify
            website: Optional company website
            additional_context: Optional additional details (address, industry, what they do)

        Returns:
            Dictionary with verification results:
            {
                "passed": bool,  # True if ANY check passed
                "checks": {
                    "google_sheet": bool,
                    "perplexity": bool
                },
                "passed_by": str  # Source that verified, or "none"
            }
        """
        print(f"\n=== Employer Verification: '{company_name}' ===")

        # Run two checks in parallel (DataForThai commented out - unreliable)
        results = await asyncio.gather(
            self.check_google_sheet_allowlist(company_name),
            # self.check_dataforthai_registry(company_name),  # Disabled: unreliable for short names
            self.check_perplexity_web(company_name, website, additional_context),
            return_exceptions=True  # Don't fail if one API errors
        )

        # Extract results (handle exceptions)
        google_sheet_pass = results[0] if not isinstance(results[0], Exception) else False
        # dataforthai_pass = results[1] if not isinstance(results[1], Exception) else False

        # Perplexity returns tuple (bool, dict)
        perplexity_result = results[1] if not isinstance(results[1], Exception) else (False, None)
        perplexity_pass = perplexity_result[0] if isinstance(perplexity_result, tuple) else False
        perplexity_data = perplexity_result[1] if isinstance(perplexity_result, tuple) else None

        # Determine overall pass (ANY pass = PASS)
        passed = google_sheet_pass or perplexity_pass

        # Determine which source passed
        if google_sheet_pass:
            passed_by = "google_sheet"
        elif perplexity_pass:
            passed_by = "perplexity"
        else:
            passed_by = "none"

        result = {
            "passed": passed,
            "checks": {
                "google_sheet": google_sheet_pass,
                # "dataforthai": dataforthai_pass,  # Disabled
                "perplexity": perplexity_pass
            },
            "passed_by": passed_by
        }

        # Include Perplexity detailed response if available
        if perplexity_data:
            result["perplexity_details"] = {
                "result": perplexity_data.get("result"),
                "explanation": perplexity_data.get("explanation"),
                "closest_company_name": perplexity_data.get("closest_company_name"),
                "closest_company_website": perplexity_data.get("closest_company_website")
            }

        print(f"=== Result: {'PASS' if passed else 'FAIL'} (by {passed_by}) ===\n")

        return result
