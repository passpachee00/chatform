import httpx
import os
from geopy.distance import geodesic
from typing import Optional, Tuple


class DistanceService:
    """Service to calculate distance between two addresses using Google Geocoding API"""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        self.geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"

    async def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Convert address to (latitude, longitude) using Google Geocoding API

        Args:
            address: Address string to geocode

        Returns:
            Tuple of (lat, lng) or None if geocoding fails
        """
        if not address or not address.strip():
            return None

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
                    return (location["lat"], location["lng"])
                else:
                    print(f"Geocoding failed for '{address}': {data.get('status')}")
                    return None

            except Exception as e:
                print(f"Error geocoding address '{address}': {e}")
                return None

    async def calculate_distance(
        self,
        address_a: str,
        address_b: str
    ) -> Optional[float]:
        """
        Calculate straight-line distance (in km) between two addresses

        Args:
            address_a: First address
            address_b: Second address

        Returns:
            Distance in kilometers, or None if geocoding fails
        """
        # Geocode both addresses
        coords_a = await self.geocode_address(address_a)
        coords_b = await self.geocode_address(address_b)

        if not coords_a or not coords_b:
            return None

        # Calculate geodesic distance
        distance_km = geodesic(coords_a, coords_b).kilometers

        return distance_km

    async def check_distance_within_limit(
        self,
        address_a: str,
        address_b: str,
        limit_km: float = 150.0
    ) -> Tuple[bool, Optional[float]]:
        """
        Check if two addresses are within the specified distance limit

        Args:
            address_a: First address
            address_b: Second address
            limit_km: Maximum allowed distance in km (default: 150)

        Returns:
            Tuple of (is_within_limit, actual_distance_km)
        """
        distance = await self.calculate_distance(address_a, address_b)

        if distance is None:
            # If we can't calculate distance, we can't verify
            return (False, None)

        is_within_limit = distance <= limit_km
        return (is_within_limit, distance)
