# Strava Run Coach MCP Server

A local MCP server that connects Claude Desktop to your Strava data, enabling a personalized running coach experience.

## Features

- **Strava Integration**: Access your training data, activities, and PRs
- **Training Analysis**: Weekly/monthly mileage trends and training load
- **Goal Tracking**: Set and track your running goals
- **Race Calendar**: Manage upcoming races with goal times

## Setup

### 1. Create a Strava API Application

1. Go to [Strava API Settings](https://www.strava.com/settings/api)
2. Create a new application:
   - **Application Name**: Run Coach (or any name)
   - **Category**: Training
   - **Website**: http://localhost
   - **Authorization Callback Domain**: localhost
3. Note your **Client ID** and **Client Secret**

### 2. Install Dependencies

```bash
cd /Users/sv/Documents/Python/runcoach
pip install -e .
```

Or install dependencies directly:

```bash
pip install mcp httpx
```

### 3. Authenticate with Strava

Run the authentication flow:

```bash
python -m runcoach.auth
```

This will:
1. Ask for your Client ID and Client Secret
2. Open a browser for Strava authorization
3. Save your tokens to `data/tokens.json`

### 4. Add to Claude Desktop

Add the MCP server to your Claude Desktop configuration:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "runcoach": {
      "command": "/path/to/python",
      "args": ["-m", "runcoach.server"],
      "cwd": "/path/to/runcoach"
    }
  }
}
```

**Note:** Use the full path to your Python executable (find it with `which python` or `python -c "import sys; print(sys.executable)"`) and the full path to the runcoach directory.

Then restart Claude Desktop.

## Available Tools

### Strava Data

| Tool | Description |
|------|-------------|
| `get_athlete_profile` | Your Strava profile (name, location, stats) |
| `get_recent_activities` | Last N runs with pace, distance, HR |
| `get_activity_details` | Deep dive on a specific run (splits, laps) |
| `get_athlete_stats` | Overall stats including all-time totals |
| `get_training_load` | Weekly/monthly mileage trends |
| `sync_all_activities` | Sync all activities to local cache for historical analysis |
| `search_activities` | Search cached activities by year, distance, type |
| `get_yearly_stats` | Aggregated running stats by year |

### Goals & Races

| Tool | Description |
|------|-------------|
| `get_goals` | List your running goals |
| `set_goal` | Add or update a goal |
| `delete_goal` | Remove a goal |
| `get_races` | List upcoming races |
| `add_race` | Add an upcoming race |
| `update_race` | Update race details |
| `delete_race` | Remove a race |

## Example Prompts

Once set up, you can ask Claude things like:

- "What were my recent runs?"
- "How did my 10K on Saturday go? Show me the splits."
- "What's my training load been like the past month?"
- "Add a goal to run a sub-50 minute 10K by June"
- "I'm racing the Chicago Marathon on October 13th, goal time 3:30"
- "Based on my recent training, am I ready for my upcoming race?"

For historical analysis, first sync your data:
- "Sync all my Strava activities"
- "Show my yearly running stats"
- "Find my longest runs from 2024"
- "Compare my 2023 and 2024 training volume"

## File Structure

```
runcoach/
├── pyproject.toml          # Project config
├── src/runcoach/
│   ├── __init__.py
│   ├── server.py           # MCP server
│   ├── strava.py           # Strava API client
│   ├── auth.py             # OAuth management
│   └── storage.py          # Local JSON storage
├── data/
│   ├── tokens.json         # OAuth tokens (gitignored)
│   ├── goals.json          # Your goals
│   └── races.json          # Upcoming races
└── README.md
```

## Troubleshooting

### "No tokens found" error

Run the authentication flow:
```bash
python -m runcoach.auth
```

### Token refresh fails

Delete `data/tokens.json` and re-authenticate.

### Server not showing in Claude Desktop

1. Check the config file path is correct
2. Ensure Python can find the module (try `python -m runcoach.server` manually)
3. Restart Claude Desktop completely

## Security Notes

- `data/tokens.json` contains sensitive OAuth tokens and is gitignored
- Tokens auto-refresh when expired (Strava tokens expire after 6 hours)
- Only you can access your Strava data through this local server
