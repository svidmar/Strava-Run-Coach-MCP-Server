"""MCP server for Strava Run Coach."""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .storage import (
    add_goal,
    add_race,
    delete_goal,
    delete_race,
    get_goals,
    get_race,
    get_races,
    update_goal,
    update_race,
    save_activities_cache,
    get_activities_cache,
    query_cached_activities,
)
from .strava import StravaClient, format_activity_summary, format_distance, format_duration, format_pace

# Create the MCP server
server = Server("runcoach")

# Strava client instance
strava = StravaClient()


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        # Strava data tools
        Tool(
            name="get_athlete_profile",
            description="Get your Strava athlete profile including name, location, and basic stats",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_recent_activities",
            description="Get your recent running activities with pace, distance, heart rate, etc. For all historical data, use sync_all_activities first then search_activities.",
            inputSchema={
                "type": "object",
                "properties": {
                    "count": {
                        "type": "integer",
                        "description": "Number of activities to retrieve (default 10, max 100)",
                        "default": 10,
                    },
                    "runs_only": {
                        "type": "boolean",
                        "description": "Only include running activities (default true)",
                        "default": True,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="sync_all_activities",
            description="Sync ALL activities from Strava to local cache. Run this once to enable historical analysis. Returns a summary, not the full data.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="search_activities",
            description="Search through cached activities with filters. Run sync_all_activities first to populate the cache.",
            inputSchema={
                "type": "object",
                "properties": {
                    "activity_type": {
                        "type": "string",
                        "description": "Filter by type: 'Run', 'Ride', 'Swim', etc.",
                    },
                    "year": {
                        "type": "integer",
                        "description": "Filter by year (e.g., 2024)",
                    },
                    "min_distance_km": {
                        "type": "number",
                        "description": "Minimum distance in kilometers",
                    },
                    "max_distance_km": {
                        "type": "number",
                        "description": "Maximum distance in kilometers",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results to return (default 10, max 25)",
                        "default": 10,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_yearly_stats",
            description="Get aggregated running statistics by year from cached activities. Great for year-over-year comparisons.",
            inputSchema={
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "Specific year to analyze (omit for all years)",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_activity_details",
            description="Get detailed information about a specific activity including splits, laps, and heart rate zones",
            inputSchema={
                "type": "object",
                "properties": {
                    "activity_id": {
                        "type": "integer",
                        "description": "The Strava activity ID",
                    },
                },
                "required": ["activity_id"],
            },
        ),
        Tool(
            name="get_athlete_stats",
            description="Get your overall running statistics including all-time PRs, yearly totals, and recent totals",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_training_load",
            description="Analyze your training load with weekly and monthly mileage trends",
            inputSchema={
                "type": "object",
                "properties": {
                    "weeks": {
                        "type": "integer",
                        "description": "Number of weeks to analyze (default 8, max 16)",
                        "default": 8,
                    },
                },
                "required": [],
            },
        ),
        # Local data tools
        Tool(
            name="get_goals",
            description="Get your running goals",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="set_goal",
            description="Add or update a running goal",
            inputSchema={
                "type": "object",
                "properties": {
                    "goal_id": {
                        "type": "string",
                        "description": "Goal ID to update (omit to create new goal)",
                    },
                    "goal_type": {
                        "type": "string",
                        "description": "Type of goal: 'distance', 'pace', 'race', 'consistency'",
                    },
                    "target": {
                        "type": "string",
                        "description": "The target (e.g., 'sub-20 5K', '50km/week')",
                    },
                    "deadline": {
                        "type": "string",
                        "description": "Deadline date in YYYY-MM-DD format",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes about the goal",
                    },
                    "completed": {
                        "type": "boolean",
                        "description": "Mark goal as completed (for updates)",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="delete_goal",
            description="Delete a running goal",
            inputSchema={
                "type": "object",
                "properties": {
                    "goal_id": {
                        "type": "string",
                        "description": "The ID of the goal to delete",
                    },
                },
                "required": ["goal_id"],
            },
        ),
        Tool(
            name="get_races",
            description="Get your upcoming races",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="add_race",
            description="Add an upcoming race to your calendar",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Race name",
                    },
                    "date": {
                        "type": "string",
                        "description": "Race date in YYYY-MM-DD format",
                    },
                    "distance": {
                        "type": "string",
                        "description": "Race distance (e.g., '5K', '10K', 'Half Marathon', 'Marathon')",
                    },
                    "goal_time": {
                        "type": "string",
                        "description": "Your goal finish time",
                    },
                    "location": {
                        "type": "string",
                        "description": "Race location",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes",
                    },
                },
                "required": ["name", "date", "distance"],
            },
        ),
        Tool(
            name="update_race",
            description="Update an existing race",
            inputSchema={
                "type": "object",
                "properties": {
                    "race_id": {
                        "type": "string",
                        "description": "The ID of the race to update",
                    },
                    "name": {"type": "string"},
                    "date": {"type": "string"},
                    "distance": {"type": "string"},
                    "goal_time": {"type": "string"},
                    "location": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["race_id"],
            },
        ),
        Tool(
            name="delete_race",
            description="Delete a race from your calendar",
            inputSchema={
                "type": "object",
                "properties": {
                    "race_id": {
                        "type": "string",
                        "description": "The ID of the race to delete",
                    },
                },
                "required": ["race_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        result = await _handle_tool(name, arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        return [TextContent(type="text", text=error_msg)]


async def _handle_tool(name: str, arguments: dict[str, Any]) -> Any:
    """Route tool calls to appropriate handlers."""

    # Strava tools
    if name == "get_athlete_profile":
        return await _get_athlete_profile()
    elif name == "get_recent_activities":
        return await _get_recent_activities(arguments)
    elif name == "get_activity_details":
        return await _get_activity_details(arguments)
    elif name == "get_athlete_stats":
        return await _get_athlete_stats()
    elif name == "get_training_load":
        return await _get_training_load(arguments)
    elif name == "sync_all_activities":
        return await _sync_all_activities()
    elif name == "search_activities":
        return _search_activities(arguments)
    elif name == "get_yearly_stats":
        return _get_yearly_stats(arguments)

    # Goals tools
    elif name == "get_goals":
        return {"goals": get_goals()}
    elif name == "set_goal":
        return _set_goal(arguments)
    elif name == "delete_goal":
        goal_id = arguments.get("goal_id")
        if delete_goal(goal_id):
            return {"success": True, "message": f"Goal {goal_id} deleted"}
        return {"success": False, "message": f"Goal {goal_id} not found"}

    # Races tools
    elif name == "get_races":
        return {"races": get_races()}
    elif name == "add_race":
        return _add_race(arguments)
    elif name == "update_race":
        return _update_race(arguments)
    elif name == "delete_race":
        race_id = arguments.get("race_id")
        if delete_race(race_id):
            return {"success": True, "message": f"Race {race_id} deleted"}
        return {"success": False, "message": f"Race {race_id} not found"}

    else:
        raise ValueError(f"Unknown tool: {name}")


async def _get_athlete_profile() -> dict[str, Any]:
    """Get athlete profile."""
    athlete = await strava.get_athlete()
    return {
        "id": athlete.get("id"),
        "name": f"{athlete.get('firstname', '')} {athlete.get('lastname', '')}".strip(),
        "username": athlete.get("username"),
        "city": athlete.get("city"),
        "state": athlete.get("state"),
        "country": athlete.get("country"),
        "sex": athlete.get("sex"),
        "weight": athlete.get("weight"),  # kg
        "created_at": athlete.get("created_at"),
        "follower_count": athlete.get("follower_count"),
        "friend_count": athlete.get("friend_count"),
    }


async def _get_recent_activities(arguments: dict[str, Any]) -> dict[str, Any]:
    """Get recent activities."""
    count = min(arguments.get("count", 10), 100)
    runs_only = arguments.get("runs_only", True)

    # Fetch more if filtering to runs only
    fetch_count = count * 2 if runs_only else count
    activities = await strava.get_activities(per_page=min(fetch_count, 200))

    if runs_only:
        activities = [a for a in activities if a.get("type") == "Run"]

    activities = activities[:count]

    return {
        "count": len(activities),
        "activities": [format_activity_summary(a) for a in activities],
    }


async def _sync_all_activities() -> dict[str, Any]:
    """Sync all activities from Strava to local cache."""
    activities = await strava.get_all_activities()

    # Save to cache
    save_activities_cache(activities)

    # Calculate summary stats
    runs = [a for a in activities if a.get("type") == "Run"]
    total_run_distance = sum(a.get("distance", 0) for a in runs)
    total_run_time = sum(a.get("moving_time", 0) for a in runs)

    # Get date range
    if activities:
        dates = [a.get("start_date_local", "")[:10] for a in activities if a.get("start_date_local")]
        oldest = min(dates) if dates else "N/A"
        newest = max(dates) if dates else "N/A"
    else:
        oldest = newest = "N/A"

    # Count by year
    years = {}
    for a in runs:
        year = a.get("start_date_local", "")[:4]
        if year:
            years[year] = years.get(year, 0) + 1

    return {
        "success": True,
        "total_activities": len(activities),
        "total_runs": len(runs),
        "total_run_distance": format_distance(total_run_distance),
        "total_run_time": format_duration(total_run_time),
        "date_range": f"{oldest} to {newest}",
        "runs_by_year": dict(sorted(years.items())),
        "message": "Activities cached locally. Use search_activities to query them.",
    }


def _search_activities(arguments: dict[str, Any]) -> dict[str, Any]:
    """Search cached activities."""
    cache = get_activities_cache()
    if not cache:
        return {
            "error": "No cached activities. Run sync_all_activities first.",
            "activities": [],
        }

    limit = min(arguments.get("limit", 10), 25)  # Max 25 to avoid context issues

    activities = query_cached_activities(
        activity_type=arguments.get("activity_type"),
        year=arguments.get("year"),
        min_distance_km=arguments.get("min_distance_km"),
        max_distance_km=arguments.get("max_distance_km"),
        limit=limit,
    )

    return {
        "cache_updated": cache.get("updated_at"),
        "total_cached": cache.get("count"),
        "results_count": len(activities),
        "activities": [format_activity_summary(a, compact=True) for a in activities],
    }


def _get_yearly_stats(arguments: dict[str, Any]) -> dict[str, Any]:
    """Get aggregated stats by year."""
    cache = get_activities_cache()
    if not cache:
        return {"error": "No cached activities. Run sync_all_activities first."}

    activities = cache.get("activities", [])
    runs = [a for a in activities if a.get("type") == "Run"]

    # Group by year
    yearly = {}
    for run in runs:
        year = run.get("start_date_local", "")[:4]
        if not year:
            continue

        if year not in yearly:
            yearly[year] = {
                "runs": 0,
                "distance_m": 0,
                "time_s": 0,
                "elevation_m": 0,
            }

        yearly[year]["runs"] += 1
        yearly[year]["distance_m"] += run.get("distance", 0)
        yearly[year]["time_s"] += run.get("moving_time", 0)
        yearly[year]["elevation_m"] += run.get("total_elevation_gain", 0)

    # Filter to specific year if requested
    target_year = arguments.get("year")
    if target_year:
        yearly = {str(target_year): yearly.get(str(target_year), {})}

    # Format output
    result = {}
    for year, stats in sorted(yearly.items()):
        if not stats:
            continue
        avg_pace = stats["distance_m"] / stats["time_s"] if stats["time_s"] > 0 else 0
        result[year] = {
            "total_runs": stats["runs"],
            "total_distance": format_distance(stats["distance_m"]),
            "total_distance_km": round(stats["distance_m"] / 1000, 1),
            "total_time": format_duration(stats["time_s"]),
            "total_elevation": f"{stats['elevation_m']:.0f}m",
            "average_run_distance": format_distance(stats["distance_m"] / stats["runs"]) if stats["runs"] > 0 else "N/A",
            "average_pace": format_pace(avg_pace) if avg_pace > 0 else "N/A",
        }

    return {
        "cache_updated": cache.get("updated_at"),
        "yearly_stats": result,
    }


async def _get_activity_details(arguments: dict[str, Any]) -> dict[str, Any]:
    """Get detailed activity information."""
    activity_id = arguments.get("activity_id")
    if not activity_id:
        raise ValueError("activity_id is required")

    # Get activity details and laps
    activity = await strava.get_activity(activity_id, include_all_efforts=True)
    laps = await strava.get_activity_laps(activity_id)

    # Format the response
    result = format_activity_summary(activity)

    # Add detailed fields
    result["description"] = activity.get("description")
    result["workout_type"] = _workout_type_name(activity.get("workout_type"))
    result["perceived_exertion"] = activity.get("perceived_exertion")

    # Splits (per km/mile)
    splits = activity.get("splits_metric", [])
    result["splits"] = [
        {
            "split": s.get("split"),
            "distance": format_distance(s.get("distance", 0)),
            "time": format_duration(s.get("moving_time", 0)),
            "pace": format_pace(s.get("average_speed", 0)),
            "elevation_diff": f"{s.get('elevation_difference', 0):.0f}m",
            "average_heartrate": s.get("average_heartrate"),
        }
        for s in splits
    ]

    # Laps
    result["laps"] = [
        {
            "name": lap.get("name"),
            "distance": format_distance(lap.get("distance", 0)),
            "time": format_duration(lap.get("moving_time", 0)),
            "pace": format_pace(lap.get("average_speed", 0)),
            "average_heartrate": lap.get("average_heartrate"),
            "max_heartrate": lap.get("max_heartrate"),
        }
        for lap in laps
    ]

    # Best efforts (PRs on this run)
    best_efforts = activity.get("best_efforts", [])
    result["best_efforts"] = [
        {
            "name": e.get("name"),
            "distance": format_distance(e.get("distance", 0)),
            "time": format_duration(e.get("elapsed_time", 0)),
            "pr_rank": e.get("pr_rank"),  # 1 = PR, 2 = 2nd best, etc.
        }
        for e in best_efforts
    ]

    # Segment efforts
    segment_efforts = activity.get("segment_efforts", [])[:5]  # Limit to 5
    result["segment_efforts"] = [
        {
            "name": s.get("name"),
            "distance": format_distance(s.get("distance", 0)),
            "time": format_duration(s.get("elapsed_time", 0)),
            "pr_rank": s.get("pr_rank"),
        }
        for s in segment_efforts
    ]

    return result


def _workout_type_name(workout_type: int | None) -> str:
    """Convert workout type ID to name."""
    types = {
        0: "Default",
        1: "Race",
        2: "Long Run",
        3: "Workout",
    }
    return types.get(workout_type, "Unknown") if workout_type is not None else None


async def _get_athlete_stats() -> dict[str, Any]:
    """Get athlete statistics including PRs."""
    athlete = await strava.get_athlete()
    athlete_id = athlete.get("id")
    stats = await strava.get_athlete_stats(athlete_id)

    def format_totals(totals: dict) -> dict:
        if not totals:
            return {}
        return {
            "count": totals.get("count", 0),
            "distance": format_distance(totals.get("distance", 0)),
            "moving_time": format_duration(totals.get("moving_time", 0)),
            "elevation_gain": f"{totals.get('elevation_gain', 0):.0f}m",
        }

    def format_pr(pr: dict) -> dict | None:
        if not pr or not pr.get("distance"):
            return None
        return {
            "distance": format_distance(pr.get("distance", 0)),
            "time": format_duration(pr.get("elapsed_time", 0)),
            "pace": format_pace(pr.get("distance", 0) / pr.get("elapsed_time", 1)),
            "activity_id": pr.get("activity_id"),
        }

    # Extract best efforts (PRs)
    all_run_totals = stats.get("all_run_totals", {})

    return {
        "all_time_runs": format_totals(all_run_totals),
        "ytd_runs": format_totals(stats.get("ytd_run_totals", {})),
        "recent_runs": format_totals(stats.get("recent_run_totals", {})),
        "biggest_ride_distance": format_distance(stats.get("biggest_ride_distance", 0)),
        "biggest_climb_elevation_gain": f"{stats.get('biggest_climb_elevation_gain', 0):.0f}m",
    }


async def _get_training_load(arguments: dict[str, Any]) -> dict[str, Any]:
    """Analyze training load over recent weeks."""
    weeks = min(arguments.get("weeks", 8), 16)

    # Calculate date range
    now = datetime.now()
    start_of_week = now - timedelta(days=now.weekday())  # Monday
    start_date = start_of_week - timedelta(weeks=weeks - 1)

    # Fetch activities
    after_timestamp = int(start_date.timestamp())
    activities = await strava.get_activities(per_page=200, after=after_timestamp)

    # Filter to runs only
    runs = [a for a in activities if a.get("type") == "Run"]

    # Group by week
    weekly_data = {}
    for run in runs:
        run_date = datetime.fromisoformat(run["start_date_local"].replace("Z", ""))
        # Get Monday of that week
        week_start = run_date - timedelta(days=run_date.weekday())
        week_key = week_start.strftime("%Y-%m-%d")

        if week_key not in weekly_data:
            weekly_data[week_key] = {
                "week_of": week_key,
                "runs": 0,
                "distance_meters": 0,
                "time_seconds": 0,
                "elevation_meters": 0,
            }

        weekly_data[week_key]["runs"] += 1
        weekly_data[week_key]["distance_meters"] += run.get("distance", 0)
        weekly_data[week_key]["time_seconds"] += run.get("moving_time", 0)
        weekly_data[week_key]["elevation_meters"] += run.get("total_elevation_gain", 0)

    # Sort weeks and format
    sorted_weeks = sorted(weekly_data.values(), key=lambda x: x["week_of"])

    formatted_weeks = []
    for week in sorted_weeks:
        formatted_weeks.append({
            "week_of": week["week_of"],
            "runs": week["runs"],
            "distance": format_distance(week["distance_meters"]),
            "distance_km": round(week["distance_meters"] / 1000, 1),
            "time": format_duration(week["time_seconds"]),
            "elevation": f"{week['elevation_meters']:.0f}m",
        })

    # Calculate averages
    if formatted_weeks:
        avg_distance = sum(w["distance_km"] for w in formatted_weeks) / len(formatted_weeks)
        avg_runs = sum(w["runs"] for w in formatted_weeks) / len(formatted_weeks)
    else:
        avg_distance = 0
        avg_runs = 0

    return {
        "weeks_analyzed": len(formatted_weeks),
        "weekly_breakdown": formatted_weeks,
        "average_weekly_distance_km": round(avg_distance, 1),
        "average_runs_per_week": round(avg_runs, 1),
        "total_distance": format_distance(sum(w["distance_meters"] for w in sorted_weeks)),
        "total_runs": sum(w["runs"] for w in sorted_weeks),
    }


def _set_goal(arguments: dict[str, Any]) -> dict[str, Any]:
    """Add or update a goal."""
    goal_id = arguments.get("goal_id")

    if goal_id:
        # Update existing goal
        updates = {}
        for key in ["goal_type", "target", "deadline", "notes", "completed"]:
            if key in arguments:
                # Map goal_type to type for storage
                storage_key = "type" if key == "goal_type" else key
                updates[storage_key] = arguments[key]

        result = update_goal(goal_id, **updates)
        if result:
            return {"success": True, "goal": result}
        return {"success": False, "message": f"Goal {goal_id} not found"}
    else:
        # Create new goal
        goal_type = arguments.get("goal_type")
        target = arguments.get("target")

        if not goal_type or not target:
            raise ValueError("goal_type and target are required for new goals")

        goal = add_goal(
            goal_type=goal_type,
            target=target,
            deadline=arguments.get("deadline"),
            notes=arguments.get("notes"),
        )
        return {"success": True, "goal": goal}


def _add_race(arguments: dict[str, Any]) -> dict[str, Any]:
    """Add a new race."""
    name = arguments.get("name")
    date = arguments.get("date")
    distance = arguments.get("distance")

    if not all([name, date, distance]):
        raise ValueError("name, date, and distance are required")

    race = add_race(
        name=name,
        date=date,
        distance=distance,
        goal_time=arguments.get("goal_time"),
        location=arguments.get("location"),
        notes=arguments.get("notes"),
    )
    return {"success": True, "race": race}


def _update_race(arguments: dict[str, Any]) -> dict[str, Any]:
    """Update an existing race."""
    race_id = arguments.get("race_id")
    if not race_id:
        raise ValueError("race_id is required")

    updates = {}
    for key in ["name", "date", "distance", "goal_time", "location", "notes"]:
        if key in arguments:
            updates[key] = arguments[key]

    result = update_race(race_id, **updates)
    if result:
        return {"success": True, "race": result}
    return {"success": False, "message": f"Race {race_id} not found"}


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
