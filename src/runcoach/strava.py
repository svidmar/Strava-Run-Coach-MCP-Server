"""Strava API client."""

import asyncio
from datetime import datetime, timedelta
from typing import Any

import httpx

from .auth import get_valid_token, load_tokens

STRAVA_API_BASE = "https://www.strava.com/api/v3"


class StravaClient:
    """Async client for Strava API."""

    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=STRAVA_API_BASE,
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _get_access_token(self) -> str:
        """Get a valid access token."""
        tokens = load_tokens()
        if not tokens:
            raise ValueError(
                "No tokens found. Run 'python -m runcoach.auth' to authenticate."
            )

        client_id = tokens.get("client_id")
        client_secret = tokens.get("client_secret")

        if not client_id or not client_secret:
            raise ValueError(
                "Client credentials not found in tokens. Re-run authentication."
            )

        token = get_valid_token(client_id, client_secret)
        if not token:
            raise ValueError("Failed to get valid token. Re-run authentication.")

        return token

    async def _request(
        self, method: str, endpoint: str, **kwargs
    ) -> dict[str, Any] | list[Any]:
        """Make an authenticated request to the Strava API."""
        token = self._get_access_token()
        client = await self._get_client()

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"

        response = await client.request(method, endpoint, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()

    async def get_athlete(self) -> dict[str, Any]:
        """Get the authenticated athlete's profile."""
        return await self._request("GET", "/athlete")

    async def get_athlete_stats(self, athlete_id: int) -> dict[str, Any]:
        """Get athlete statistics including PRs."""
        return await self._request("GET", f"/athletes/{athlete_id}/stats")

    async def get_activities(
        self,
        per_page: int = 30,
        page: int = 1,
        before: int | None = None,
        after: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get the athlete's activities (single page)."""
        params = {"per_page": per_page, "page": page}
        if before:
            params["before"] = before
        if after:
            params["after"] = after

        return await self._request("GET", "/athlete/activities", params=params)

    async def get_all_activities(
        self,
        before: int | None = None,
        after: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get all athlete's activities (handles pagination)."""
        all_activities = []
        page = 1
        per_page = 200  # Max allowed by Strava

        while True:
            activities = await self.get_activities(
                per_page=per_page,
                page=page,
                before=before,
                after=after,
            )
            if not activities:
                break
            all_activities.extend(activities)
            if len(activities) < per_page:
                break
            page += 1

        return all_activities

    async def get_activity(
        self, activity_id: int, include_all_efforts: bool = False
    ) -> dict[str, Any]:
        """Get detailed information about an activity."""
        params = {"include_all_efforts": str(include_all_efforts).lower()}
        return await self._request("GET", f"/activities/{activity_id}", params=params)

    async def get_activity_streams(
        self,
        activity_id: int,
        keys: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get activity streams (time series data)."""
        if keys is None:
            keys = ["time", "distance", "heartrate", "cadence", "altitude", "velocity_smooth"]

        params = {
            "keys": ",".join(keys),
            "key_by_type": "true",
        }
        return await self._request(
            "GET", f"/activities/{activity_id}/streams", params=params
        )

    async def get_activity_laps(self, activity_id: int) -> list[dict[str, Any]]:
        """Get laps for an activity."""
        return await self._request("GET", f"/activities/{activity_id}/laps")


def format_pace(meters_per_second: float) -> str:
    """Convert m/s to min/km pace string."""
    if meters_per_second <= 0:
        return "N/A"
    seconds_per_km = 1000 / meters_per_second
    minutes = int(seconds_per_km // 60)
    seconds = int(seconds_per_km % 60)
    return f"{minutes}:{seconds:02d}/km"


def format_distance(meters: float) -> str:
    """Format distance in km."""
    km = meters / 1000
    return f"{km:.2f} km"


def format_duration(seconds: int) -> str:
    """Format duration as HH:MM:SS or MM:SS."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_activity_summary(activity: dict[str, Any], compact: bool = False) -> dict[str, Any]:
    """Format an activity into a readable summary."""
    avg_speed = activity.get("average_speed", 0)
    distance = activity.get("distance", 0)
    moving_time = activity.get("moving_time", 0)
    elapsed_time = activity.get("elapsed_time", moving_time)  # Use elapsed_time, fall back to moving_time

    if compact:
        # Minimal format for large lists
        pace = format_pace(avg_speed) if activity.get("type") == "Run" else None
        return {
            "id": activity.get("id"),
            "date": activity.get("start_date_local", "")[:10],
            "name": activity.get("name"),
            "distance": format_distance(distance),
            "time": format_duration(elapsed_time),  # Use elapsed_time for compact view
            "pace": pace,
            "hr": activity.get("average_heartrate"),
        }

    return {
        "id": activity.get("id"),
        "name": activity.get("name"),
        "type": activity.get("type"),
        "date": activity.get("start_date_local", "")[:10],
        "distance": format_distance(distance),
        "distance_meters": distance,
        "moving_time": format_duration(moving_time),
        "moving_time_seconds": moving_time,
        "elapsed_time": format_duration(elapsed_time),  # Add elapsed_time
        "elapsed_time_seconds": elapsed_time,  # Add elapsed_time in seconds
        "pace": format_pace(avg_speed) if activity.get("type") == "Run" else None,
        "average_speed_mps": avg_speed,
        "elevation_gain": f"{activity.get('total_elevation_gain', 0):.0f}m",
        "average_heartrate": activity.get("average_heartrate"),
        "max_heartrate": activity.get("max_heartrate"),
        "suffer_score": activity.get("suffer_score"),
        "calories": activity.get("calories"),
    }
