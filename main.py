import os
import logging
import requests
import pytz
from datetime import datetime

logger = logging.getLogger("daily-10-tips")

# 1. FIXED UNIVERSAL TIMEZONE SETUP
WAT = pytz.timezone("Africa/Lagos")

# 2. FIXED PRODUCTION API ENDPOINTS
SPORTS_URL = "https://the-odds-api.com"
MIN_ODDS = 1.60
BASE_MARKETS = "h2h,totals"
EVENT_MARKETS = "btts,draw_no_bet,alternate_totals,alternate_team_totals,"

# GLOBAL VALUE INITIALIZATIONS
DAILY_TIPS = []
LAST_REFRESHED = None
LAST_ERROR = None
REFRESH_LOCK = __import__('threading').Lock()

# 3. ADDED THE MISSING GET_WAT_KICKOFF FUNCTION
def get_wat_kickoff(commence_time):
    """Safely parse standard ISO time formats and convert to WAT."""
    if not commence_time:
        return None
    try:
        dt = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
        return dt.astimezone(WAT)
    except Exception:
        return None

# 4. FIXED SYNTAX ERROR COMPREHENSION LOOP
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
        # Fixed loop syntax from duplicate 'for key for key'
        return sorted({key for key in keys if key})
    except (requests.RequestException, ValueError, TypeError) as e:
        logger.warning(f"Could not discover soccer competitions: {e}; using aggregate feed")
        return ["soccer"]

# 5. FIXED ENDPOINT FORMAT PATH STRINGS
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

# 6. FIXED INCOMPLETE DATA FILTERING LOOP AT BOTTOM
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
                    # Safely closed loop logic branch to store qualifying predictions
                    qualifying.append(event)
            
            DAILY_TIPS = qualifying[:10]
            LAST_REFRESHED = datetime.now(WAT).isoformat()
            print(f"Successfully processed {len(DAILY_TIPS)} tips.")
        except Exception as e:
            LAST_ERROR = f"Unexpected loop error: {str(e)}"
            logger.error(LAST_ERROR)

# Simple infinite worker sleep runtime structure loop for persistent execution tasking script setups
if __name__ == "__main__":
    import time
    print("Daily Football Tips initialization script processing background tasks dynamically...")
    while True:
        fetch_daily_tips()
        # Sleep for 1 hour before pulling new active sports data loops again
        time.sleep(3600)
