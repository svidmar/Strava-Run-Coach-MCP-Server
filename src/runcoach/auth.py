"""OAuth token management for Strava API."""

import json
import os
import time
import webbrowser
from pathlib import Path
from urllib.parse import urlencode

import httpx

# Strava OAuth endpoints
STRAVA_AUTH_URL = "https://www.strava.com/oauth/authorize"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"

# Default paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
TOKENS_FILE = DATA_DIR / "tokens.json"


def get_data_dir() -> Path:
    """Get the data directory path."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def load_tokens() -> dict | None:
    """Load tokens from disk."""
    tokens_file = get_data_dir() / "tokens.json"
    if tokens_file.exists():
        with open(tokens_file) as f:
            return json.load(f)
    return None


def save_tokens(tokens: dict) -> None:
    """Save tokens to disk."""
    tokens_file = get_data_dir() / "tokens.json"
    with open(tokens_file, "w") as f:
        json.dump(tokens, f, indent=2)


def is_token_expired(tokens: dict) -> bool:
    """Check if the access token is expired."""
    expires_at = tokens.get("expires_at", 0)
    # Add 60 second buffer
    return time.time() > (expires_at - 60)


def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> dict:
    """Refresh the access token using the refresh token."""
    with httpx.Client() as client:
        response = client.post(
            STRAVA_TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        )
        response.raise_for_status()
        return response.json()


def exchange_code_for_tokens(client_id: str, client_secret: str, code: str) -> dict:
    """Exchange authorization code for access and refresh tokens."""
    with httpx.Client() as client:
        response = client.post(
            STRAVA_TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
            },
        )
        response.raise_for_status()
        return response.json()


def get_authorization_url(client_id: str, redirect_uri: str = "http://localhost") -> str:
    """Generate the Strava authorization URL."""
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "read,activity:read_all,profile:read_all",
    }
    return f"{STRAVA_AUTH_URL}?{urlencode(params)}"


def get_valid_token(client_id: str, client_secret: str) -> str | None:
    """Get a valid access token, refreshing if necessary."""
    tokens = load_tokens()
    if not tokens:
        return None

    if is_token_expired(tokens):
        # Refresh the token
        new_tokens = refresh_access_token(
            client_id, client_secret, tokens["refresh_token"]
        )
        # Preserve athlete info if present
        if "athlete" in tokens and "athlete" not in new_tokens:
            new_tokens["athlete"] = tokens["athlete"]
        save_tokens(new_tokens)
        return new_tokens["access_token"]

    return tokens["access_token"]


def run_auth_flow() -> None:
    """Interactive CLI flow for initial OAuth setup."""
    print("=" * 60)
    print("Strava Run Coach - OAuth Setup")
    print("=" * 60)
    print()
    print("You need to create a Strava API application first:")
    print("1. Go to https://www.strava.com/settings/api")
    print("2. Create an application (use 'http://localhost' as callback)")
    print("3. Note your Client ID and Client Secret")
    print()

    client_id = input("Enter your Strava Client ID: ").strip()
    client_secret = input("Enter your Strava Client Secret: ").strip()

    if not client_id or not client_secret:
        print("Error: Client ID and Secret are required")
        return

    # Generate auth URL
    auth_url = get_authorization_url(client_id)
    print()
    print("Opening browser for authorization...")
    print(f"If browser doesn't open, visit: {auth_url}")
    print()

    webbrowser.open(auth_url)

    print("After authorizing, you'll be redirected to a URL like:")
    print("http://localhost/?state=&code=XXXXXXXXXXXX&scope=read,activity:read_all,profile:read_all")
    print()
    code = input("Paste the 'code' value from the URL: ").strip()

    if not code:
        print("Error: Authorization code is required")
        return

    print()
    print("Exchanging code for tokens...")

    try:
        tokens = exchange_code_for_tokens(client_id, client_secret, code)
        # Store client credentials with tokens for refresh
        tokens["client_id"] = client_id
        tokens["client_secret"] = client_secret
        save_tokens(tokens)

        athlete = tokens.get("athlete", {})
        name = f"{athlete.get('firstname', '')} {athlete.get('lastname', '')}".strip()
        print()
        print("Success! Authenticated as:", name or "Unknown")
        print(f"Tokens saved to: {get_data_dir() / 'tokens.json'}")
        print()
        print("You can now add the MCP server to Claude Desktop.")

    except httpx.HTTPStatusError as e:
        print(f"Error exchanging code: {e.response.status_code}")
        print(e.response.text)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    run_auth_flow()
