import httpx
import csv
from typing import Set, Tuple, Optional
from datetime import datetime, timedelta
import io


class BlacklistService:
    """Service to fetch and check names against Google Sheets blacklist"""

    def __init__(self):
        self.blacklist: Set[Tuple[str, str]] = set()
        self.last_fetch: Optional[datetime] = None
        self.cache_duration = timedelta(hours=1)
        self.sheet_url = "https://docs.google.com/spreadsheets/d/1fMGqPIbihu_Lr2YpgeIGhl1ypTBP7_hitBebu-yiKls/export?format=csv"

    async def fetch_blacklist(self) -> Set[Tuple[str, str]]:
        """
        Fetch blacklist from Google Sheets CSV export.

        Returns:
            Set of (first_name, last_name) tuples in lowercase
        """
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(self.sheet_url, timeout=10.0)
                response.raise_for_status()

                # Parse CSV content
                csv_content = response.text
                print(f"CSV Content:\n{csv_content}")
                csv_reader = csv.DictReader(io.StringIO(csv_content))

                blacklist = set()
                for row in csv_reader:
                    print(f"CSV Row: {row}")
                    # Strip whitespace from keys to handle "First_name " with trailing space
                    row_cleaned = {k.strip(): v for k, v in row.items()}
                    first_name = row_cleaned.get("First_name", "").strip().lower()
                    last_name = row_cleaned.get("Last_name", "").strip().lower()

                    # Only add if both names are present
                    if first_name and last_name:
                        blacklist.add((first_name, last_name))

                print(f"✓ Blacklist fetched successfully: {len(blacklist)} entries")
                print(f"  Blacklist contents: {blacklist}")
                return blacklist

        except Exception as e:
            # Log error and return empty set (fail open)
            print(f"Error fetching blacklist: {e}")
            return set()

    async def refresh_cache_if_needed(self) -> None:
        """
        Refresh cache if it's expired or empty.
        """
        now = datetime.now()

        # Check if cache needs refresh
        if (not self.blacklist or
            self.last_fetch is None or
            now - self.last_fetch > self.cache_duration):

            self.blacklist = await self.fetch_blacklist()
            self.last_fetch = now

    async def is_blacklisted(self, first_name: str, last_name: str) -> bool:
        """
        Check if a name appears in the blacklist.

        Args:
            first_name: First name to check
            last_name: Last name to check

        Returns:
            True if name is blacklisted, False otherwise
        """
        # Refresh cache if needed
        await self.refresh_cache_if_needed()

        # Normalize names to lowercase for case-insensitive matching
        first_name_lower = first_name.strip().lower()
        last_name_lower = last_name.strip().lower()

        # Check if name is in blacklist
        is_match = (first_name_lower, last_name_lower) in self.blacklist
        print(f"Checking name: ('{first_name_lower}', '{last_name_lower}') -> {'BLACKLISTED' if is_match else 'OK'}")
        return is_match
