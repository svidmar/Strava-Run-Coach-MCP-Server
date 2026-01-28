"""Local JSON storage for goals, races, and activity cache."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent.parent.parent / "data"
ACTIVITIES_CACHE_FILE = "activities_cache.json"


def _ensure_data_dir() -> Path:
    """Ensure the data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def _load_json(filename: str) -> list[dict[str, Any]]:
    """Load a JSON file from the data directory."""
    filepath = _ensure_data_dir() / filename
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    return []


def _save_json(filename: str, data: list[dict[str, Any]]) -> None:
    """Save data to a JSON file in the data directory."""
    filepath = _ensure_data_dir() / filename
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


# Goals storage
GOALS_FILE = "goals.json"


def get_goals() -> list[dict[str, Any]]:
    """Get all running goals."""
    return _load_json(GOALS_FILE)


def get_goal(goal_id: str) -> dict[str, Any] | None:
    """Get a specific goal by ID."""
    goals = get_goals()
    for goal in goals:
        if goal.get("id") == goal_id:
            return goal
    return None


def add_goal(
    goal_type: str,
    target: str,
    deadline: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """
    Add a new running goal.

    Args:
        goal_type: Type of goal (e.g., "distance", "pace", "race", "consistency")
        target: The target to achieve (e.g., "sub-20 5K", "50km/week", "run 4x/week")
        deadline: Optional deadline date (YYYY-MM-DD format)
        notes: Optional notes about the goal

    Returns:
        The created goal object
    """
    goals = get_goals()

    goal = {
        "id": str(uuid.uuid4())[:8],
        "type": goal_type,
        "target": target,
        "deadline": deadline,
        "notes": notes,
        "created_at": datetime.now().isoformat(),
        "completed": False,
    }

    goals.append(goal)
    _save_json(GOALS_FILE, goals)
    return goal


def update_goal(goal_id: str, **updates) -> dict[str, Any] | None:
    """
    Update an existing goal.

    Args:
        goal_id: The ID of the goal to update
        **updates: Fields to update (type, target, deadline, notes, completed)

    Returns:
        The updated goal or None if not found
    """
    goals = get_goals()

    for i, goal in enumerate(goals):
        if goal.get("id") == goal_id:
            # Only update allowed fields
            allowed = {"type", "target", "deadline", "notes", "completed"}
            for key, value in updates.items():
                if key in allowed:
                    goal[key] = value
            goal["updated_at"] = datetime.now().isoformat()
            goals[i] = goal
            _save_json(GOALS_FILE, goals)
            return goal

    return None


def delete_goal(goal_id: str) -> bool:
    """Delete a goal by ID."""
    goals = get_goals()
    original_len = len(goals)
    goals = [g for g in goals if g.get("id") != goal_id]

    if len(goals) < original_len:
        _save_json(GOALS_FILE, goals)
        return True
    return False


# Races storage
RACES_FILE = "races.json"


def get_races() -> list[dict[str, Any]]:
    """Get all upcoming races."""
    return _load_json(RACES_FILE)


def get_race(race_id: str) -> dict[str, Any] | None:
    """Get a specific race by ID."""
    races = get_races()
    for race in races:
        if race.get("id") == race_id:
            return race
    return None


def add_race(
    name: str,
    date: str,
    distance: str,
    goal_time: str | None = None,
    location: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """
    Add an upcoming race.

    Args:
        name: Race name
        date: Race date (YYYY-MM-DD format)
        distance: Race distance (e.g., "5K", "10K", "Half Marathon", "Marathon")
        goal_time: Optional goal finish time
        location: Optional race location
        notes: Optional notes

    Returns:
        The created race object
    """
    races = get_races()

    race = {
        "id": str(uuid.uuid4())[:8],
        "name": name,
        "date": date,
        "distance": distance,
        "goal_time": goal_time,
        "location": location,
        "notes": notes,
        "created_at": datetime.now().isoformat(),
    }

    races.append(race)
    _save_json(RACES_FILE, races)
    return race


def update_race(race_id: str, **updates) -> dict[str, Any] | None:
    """
    Update an existing race.

    Args:
        race_id: The ID of the race to update
        **updates: Fields to update

    Returns:
        The updated race or None if not found
    """
    races = get_races()

    for i, race in enumerate(races):
        if race.get("id") == race_id:
            allowed = {"name", "date", "distance", "goal_time", "location", "notes"}
            for key, value in updates.items():
                if key in allowed:
                    race[key] = value
            race["updated_at"] = datetime.now().isoformat()
            races[i] = race
            _save_json(RACES_FILE, races)
            return race

    return None


def delete_race(race_id: str) -> bool:
    """Delete a race by ID."""
    races = get_races()
    original_len = len(races)
    races = [r for r in races if r.get("id") != race_id]

    if len(races) < original_len:
        _save_json(RACES_FILE, races)
        return True
    return False


# Activities cache
def save_activities_cache(activities: list[dict[str, Any]]) -> None:
    """Save activities to local cache."""
    cache = {
        "updated_at": datetime.now().isoformat(),
        "count": len(activities),
        "activities": activities,
    }
    _save_json(ACTIVITIES_CACHE_FILE, cache)


def get_activities_cache() -> dict[str, Any] | None:
    """Get cached activities."""
    filepath = _ensure_data_dir() / ACTIVITIES_CACHE_FILE
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    return None


def query_cached_activities(
    activity_type: str | None = None,
    year: int | None = None,
    min_distance_km: float | None = None,
    max_distance_km: float | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Query cached activities with filters."""
    cache = get_activities_cache()
    if not cache:
        return []

    activities = cache.get("activities", [])

    # Apply filters
    if activity_type:
        activities = [a for a in activities if a.get("type") == activity_type]

    if year:
        activities = [
            a for a in activities
            if a.get("start_date_local", "").startswith(str(year))
        ]

    if min_distance_km is not None:
        min_meters = min_distance_km * 1000
        activities = [a for a in activities if a.get("distance", 0) >= min_meters]

    if max_distance_km is not None:
        max_meters = max_distance_km * 1000
        activities = [a for a in activities if a.get("distance", 0) <= max_meters]

    if limit:
        activities = activities[:limit]

    return activities
