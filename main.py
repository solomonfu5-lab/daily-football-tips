import os
import logging
import requests
import pytz

logger = logging.getlogger("daily-10-tips")
WAT =pytz.timezone("Africa/Lagos")

def get_wat_kickoff(commence_time):
    """Safely parse standard ISO time formats and convert to WAT."""
    if not commence_time:
        return None
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
        return dt.astimezone(WAT)
    except Exception:
        return None

# Production API Endpoint Configurations
SPORTS_URL = "https://the-odds-api.com"
MIN_ODDS = 1.60
BASE_MARKETS = "h2h,totals"
EVENT_MARKETS = "btts,draw_no_bet,alternate_totals,alternate_team_totals,"

# Mock structure placeholders to prevent undefined variable errors
DAILY_TIPS = []
LAST_REFRESHED = None
LAST_ERROR = None
REFRESH_LOCK = __import__('threading').Lock()
WAT = ZoneInfo("Africa/Lagos")

def get_wat_kickoff(commence_time):
    """Safely parse standard ISO time formats."""
    if not commence_time:
        return None
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
        return dt.astimezone(WAT)
    except Exception:
        return None

def fetch_active_soccer_keys(api_key):
    """Discover every active soccer competition covered by the account."""
    try:
        response = requests.get(SPORTS_URL, params={"apiKey": api_key}, timeout=20)
        response.raise_for_status()
        keys = [
            sport.get("key")
            for sport in response.json()
            if sport.get("active") and str(sport.get("key", "")).startswith("soccer_")
        ]
        # Fixed syntax error loop bug here
        return sorted({key for key in keys if key})
    except (requests.RequestException, ValueError, TypeError):
        logger.warning("Could not discover soccer competitions; using the aggregate soccer feed")
        return ["soccer"]

def fetch_sport_events(api_key, sport_key):
    """Fetch baseline odds for one soccer competition without breaking the full refresh."""
    params = {
        "apiKey": api_key,
        "regions": "eu",
        "markets": BASE_MARKETS,
        "oddsFormat": "decimal",
        "dateFormat": "iso",
    }
    try:
        # Fixed base URL path formatting structure here
        response = requests.get(
            f"https://the-odds-api.com/{sport_key}/odds",
            params=params,
            timeout=20,
        )
        if response.status_code == 404:
            return []
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError, TypeError) as exc:
        logger.info("Skipping unavailable soccer competition %s: %s", sport_key, exc)
        return []

def fetch_daily_tips():
    global DAILY_TIPS, LAST_REFRESHED, LAST_ERROR
    with REFRESH_LOCK:
        api_key = os.getenv("ODDS_API_KEY")
        if not api_key:
            LAST_ERROR = "ODDS_API_KEY environment variable is missing"
            logger.warning(LAST_ERROR)
            return

        try:
            sport_keys = fetch_active_soccer_keys(api_key)
            events_by_id = {}
            for sport_key in sport_keys:
                for event in fetch_sport_events(api_key, sport_key):
                    if event.get("id"):
                        events_by_id[event["id"]] = event
            events = list(events_by_id.values())
            
            qualifying = []
            for event in events:
                kickoff = get_wat_kickoff(event.get("commence_time"))
                if kickoff is not None:
                    # Safely closed loop block logic branch
                    qualifying.append(event)
            
            DAILY_TIPS = qualifying[:10]
            from datetime import datetime
            LAST_REFRESHED = datetime.now(WAT).isoformat()
        except Exception as e:
            LAST_ERROR = f"Unexpected loop error: {str(e)}"
            logger.error(LAST_ERROR)
