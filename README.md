# Strava Run Coach MCP Server

A local MCP server that connects Claude Desktop to your Strava data, enabling a personalized running coach experience.

## Features

- **Strava Integration**: Access your training data, activities, and PRs
- **Training Analysis**: Weekly/monthly mileage trends and training load
- **Shoe Tracking**: Monitor shoe mileage, wear, and usage patterns
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
cd /Users/.../runcoach
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

### Shoe Tracking

| Tool | Description |
|------|-------------|
| `get_shoes` | List all shoes with mileage, wear status, and replacement recommendations |
| `get_shoe_usage` | Analyze which shoes you use for different run types, distances, and paces |

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

### Basic Activity Queries
- "What were my recent runs?"
- "How did my 10K on Saturday go? Show me the splits."
- "What's my training load been like the past month?"
- "Show me all runs over 20km from this year"

### Training Analysis
- "What's my average pace at different heart rate zones?"
- "Has my pace improved at the same heart rate over the past 6 months?"
- "Compare my January and February training volume"
- "How much elevation have I gained in my runs this year?"
- "Am I running more consistently this year compared to last year?"

### Performance Insights
- "Based on my 10K PR, what marathon time should I target?"
- "How has my heart rate changed at marathon pace over the past year?"
- "What's my average pace on hilly vs flat routes?"
- "Show me my progression on my usual 10km route"
- "Are my long runs getting faster or am I maintaining better consistency?"

### Goal Setting & Race Prep
- "Add a goal to run a sub-50 minute 10K by March"
- "I'm racing the Chicago Marathon on October 13th, goal time 3:30"
- "Based on my recent training, am I ready for my upcoming half marathon?"
- "Create a 12-week marathon training plan based on my current fitness"

### Historical Analysis
First sync your data with "Sync all my Strava activities", then:
- "Show my yearly running stats"
- "Find my longest runs from 2024"
- "Compare my 2023 and 2024 training volume"
- "What were my peak training weeks before my last marathon?"
- "How many runs did I do per week during my last marathon build-up?"

### Shoe Management
- "What shoes do I have and how worn are they?"
- "Which shoes should I retire?"
- "Which shoes do I use for fast workouts vs easy runs?"
- "How many km are on my Pegasus?"
- "Recommend which shoe I should wear for my long run this weekend"

### Advanced Coaching
- "I want to run a sub-3:15 marathon in June. Based on my PRs and training history, is this realistic?"
- "Analyze my heart rate data - am I improving my aerobic efficiency?"
- "What's the optimal weekly mileage for me based on what I've done before?"
- "I have a half marathon in 4 weeks. Should I taper and how much?"


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

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions welcome!

## Acknowledgments

- Built with [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- Powered by [Strava API](https://developers.strava.com/)
