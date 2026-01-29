# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-28

### Added
- Initial release
- Strava API integration with OAuth authentication
- MCP server for Claude Desktop integration
- Activity data retrieval (recent activities, detailed activity info)
- Athlete profile and statistics
- Training load analysis (weekly/monthly trends)
- Activity caching for historical analysis
- Search functionality for cached activities
- Yearly statistics aggregation
- Goal tracking system (create, update, delete goals)
- Race calendar management (add, update, delete races)
- Heart rate, pace, distance, and elevation data analysis
- Split and lap data for individual activities

### Tools Available
- `get_athlete_profile` - Strava profile information
- `get_recent_activities` - Last N runs with metrics
- `get_activity_details` - Detailed activity with splits/laps
- `get_athlete_stats` - Overall running statistics
- `get_training_load` - Weekly/monthly mileage trends
- `sync_all_activities` - Sync all activities to local cache
- `search_activities` - Search cached activities
- `get_yearly_stats` - Yearly aggregated statistics
- `get_goals` / `set_goal` / `delete_goal` - Goal management
- `get_races` / `add_race` / `update_race` / `delete_race` - Race calendar

### Security
- OAuth tokens stored locally and gitignored
- Automatic token refresh handling
- Local-only data access

## [Unreleased]

### Planned Features
- Training plan generation based on historical data
- Race predictor based on recent PRs
- Recovery metrics and recommendations
- Weather-adjusted pace predictions
- Training intensity distribution analysis
- Injury risk indicators based on load changes
