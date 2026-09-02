import requests
import datetime
import zoneinfo
import streamlit as st
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
from config import get_short_team_name

def get_retry_session(retries=5, backoff_factor=1.0):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

@st.cache_data(ttl=300, show_spinner="Fetching games from ESPN (retrying if connection is slow)...")
def fetch_espn_games(sport):
    sport_category = "football"
    api_sport = sport
    extra_params = "?limit=300"
    if sport == "ncaaf":
        sport_category = "football"
        api_sport = "college-football"
        extra_params = "?groups=80&limit=300"
    elif sport == "nfl":
        sport_category = "football"
        api_sport = "nfl"
    elif sport == "ncaab":
        sport_category = "basketball"
        api_sport = "mens-college-basketball"
        extra_params = "?groups=50&limit=300"
    elif sport == "nba":
        sport_category = "basketball"
        api_sport = "nba"
    elif sport == "wnba":
        sport_category = "basketball"
        api_sport = "wnba"
    elif sport == "mlb":
        sport_category = "baseball"
        api_sport = "mlb"
    elif sport == "wc":
        sport_category = "soccer"
        api_sport = "fifa.world"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    }

    session = get_retry_session()
    url = f"https://site.web.api.espn.com/apis/site/v2/sports/{sport_category}/{api_sport}/scoreboard{extra_params}"
    events = []
    
    try:
        res = session.get(url, headers=headers, timeout=15).json()
        events = res.get("events", [])
    except Exception as err:
        st.warning(f"ESPN primary API request timed out or encountered slow network: {err}")
        events = []

    if not events:
        try:
            now_mt = datetime.datetime.now(zoneinfo.ZoneInfo("America/Denver"))
            d_start = (now_mt - datetime.timedelta(days=7)).strftime("%Y%m%d")
            d_end = (now_mt + datetime.timedelta(days=21)).strftime("%Y%m%d")
            dates_arg = f"&dates={d_start}-{d_end}" if "?" in extra_params else f"?dates={d_start}-{d_end}"
            url_range = f"https://site.web.api.espn.com/apis/site/v2/sports/{sport_category}/{api_sport}/scoreboard{extra_params}{dates_arg}"
            res_range = session.get(url_range, headers=headers, timeout=15).json()
            events = res_range.get("events", [])
        except Exception:
            pass

    if not events:
        try:
            url_simple = f"https://site.web.api.espn.com/apis/site/v2/sports/{sport_category}/{api_sport}/scoreboard"
            res_simple = session.get(url_simple, headers=headers, timeout=15).json()
            events = res_simple.get("events", [])
        except Exception:
            pass

    games = []
    for event in events:
        competitions = event.get("competitions", [])
        if not competitions:
            continue
        comp = competitions[0]
        competitors = comp.get("competitors", [])
        if len(competitors) < 2:
            continue

        comp_home = competitors[0]
        comp_away = competitors[1]
        for c in competitors:
            if c.get("homeAway") == "home":
                comp_home = c
            elif c.get("homeAway") == "away":
                comp_away = c

        away_team = comp_away.get("team", {})
        home_team = comp_home.get("team", {})

        status_info = comp.get("status", {}).get("type", {})
        time_detail = status_info.get("shortDetail") or status_info.get("detail") or ""
        
        raw_date = event.get("date")
        game_date = ""
        game_time = ""
        day_time_str = ""
        if raw_date:
            try:
                clean_date = raw_date.replace("Z", "+0000")
                try:
                    dt_utc = datetime.datetime.strptime(clean_date, "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    dt_utc = datetime.datetime.strptime(clean_date, "%Y-%m-%dT%H:%M%z")
                dt_mt = dt_utc.astimezone(zoneinfo.ZoneInfo("America/Denver"))
                game_date = dt_mt.strftime("%-m/%-d/%y")
                
                day_name = dt_mt.strftime("%a %-m/%-d")
                if dt_mt.minute == 0:
                    time_fmt = dt_mt.strftime("%-I %p MT")
                    full_time_fmt = dt_mt.strftime("%-I %p MT")
                else:
                    time_fmt = dt_mt.strftime("%-I:%M %p MT")
                    full_time_fmt = dt_mt.strftime("%-I:%M %p MT")
                
                game_time = time_fmt
                day_time_str = f"{day_name} {full_time_fmt}"
            except Exception:
                pass
        if not game_time:
            game_time = time_detail
            day_time_str = time_detail

        game_name = event.get("name") or f"{away_team.get('displayName', '')} at {home_team.get('displayName', '')}"
        display_label = f"{game_name} ({day_time_str})" if day_time_str else game_name

        raw_away_color = away_team.get("color", "000000").lstrip("#")
        raw_away_alt   = away_team.get("alternateColor", "FFFFFF").lstrip("#")
        raw_home_color = home_team.get("color", "000000").lstrip("#")
        raw_home_alt   = home_team.get("alternateColor", "FFFFFF").lstrip("#")

        away_logo_raw = away_team.get("logo", "") or (away_team.get("logos")[0].get("href", "") if away_team.get("logos") else "")
        home_logo_raw = home_team.get("logo", "") or (home_team.get("logos")[0].get("href", "") if home_team.get("logos") else "")

        games.append({
            "id": event.get("id"),
            "label": display_label,
            "game_time": game_time,
            "game_date": game_date,
            "away_name": get_short_team_name(away_team),
            "away_abbrev": away_team.get("abbreviation", ""),
            "away_color": "#" + (raw_away_color if len(raw_away_color) == 6 else "000000"),
            "away_alt_color": "#" + (raw_away_alt if len(raw_away_alt) == 6 else "FFFFFF"),
            "away_logo": away_logo_raw,
            "home_name": get_short_team_name(home_team),
            "home_abbrev": home_team.get("abbreviation", ""),
            "home_color": "#" + (raw_home_color if len(raw_home_color) == 6 else "000000"),
            "home_alt_color": "#" + (raw_home_alt if len(raw_home_alt) == 6 else "FFFFFF"),
            "home_logo": home_logo_raw,
        })
    return games
