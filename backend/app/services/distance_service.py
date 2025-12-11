import httpx
import os
from geopy.distance import geodesic
from typing import Optional, Tuple


class DistanceService:
    """Service to calculate distance between two addresses using Google Geocoding API"""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        self.geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"

    async def geocode_address(self, address: str) -> Tuple[Optional[Tuple[float, float]], str]:
        """
        Convert address to (latitude, longitude) using Google Geocoding API

        Args:
            address: Address string to geocode

        Returns:
            Tuple of ((lat, lng) or None, google_status_code)
            Examples:
            - Success: ((13.7563, 100.5018), "OK")
            - Failure: (None, "ZERO_RESULTS")
            - Error: (None, "REQUEST_DENIED")
            - Empty: (None, "EMPTY_ADDRESS")
        """
        if not address or not address.strip():
            return (None, "EMPTY_ADDRESS")

        params = {
            "address": address,
            "key": self.api_key
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.geocode_url, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()

                if data["status"] == "OK" and len(data["results"]) > 0:
                    location = data["results"][0]["geometry"]["location"]
                    return ((location["lat"], location["lng"]), "OK")
                else:
                    # Return Google's actual error status
                    google_status = data.get("status", "UNKNOWN_ERROR")
                    print(f"Geocoding failed for '{address}': {google_status}")
                    return (None, google_status)

            except Exception as e:
                print(f"Error geocoding address '{address}': {e}")
                return (None, "UNKNOWN_ERROR")

    async def calculate_distance(
        self,
        address_a: str,
        address_b: str
    ) -> Tuple[Optional[float], str, str]:
        """
        Calculate straight-line distance (in km) between two addresses

        Args:
            address_a: First address
            address_b: Second address

        Returns:
            Tuple of (distance_km or None, status_a, status_b)
            Examples:
            - Success: (15.5, "OK", "OK")
            - Failure: (None, "ZERO_RESULTS", "OK")
        """
        # Geocode both addresses
        coords_a, status_a = await self.geocode_address(address_a)
        coords_b, status_b = await self.geocode_address(address_b)

        if not coords_a or not coords_b:
            return (None, status_a, status_b)

        # Calculate geodesic distance
        distance_km = geodesic(coords_a, coords_b).kilometers

        return (distance_km, status_a, status_b)

    async def check_distance_within_limit(
        self,
        address_a: str,
        address_b: str,
        limit_km: float = 150.0
    ) -> Tuple[bool, Optional[float], str, str]:
        """
        Check if two addresses are within the specified distance limit

        Args:
            address_a: First address
            address_b: Second address
            limit_km: Maximum allowed distance in km (default: 150)

        Returns:
            Tuple of (is_within_limit, actual_distance_km, status_a, status_b)
        """
        distance, status_a, status_b = await self.calculate_distance(address_a, address_b)

        if distance is None:
            # If we can't calculate distance, we can't verify
            return (False, None, status_a, status_b)

        is_within_limit = distance <= limit_km
        return (is_within_limit, distance, status_a, status_b)
