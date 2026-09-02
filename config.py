import os

SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "1PuKW9cDf9jzSsiSpzMUkJLwhbCtKWe0Y76yt_FGG4vc")
TEMPLATE_SHEET_ID = 1594614647

LEAGUE_LOGOS = {
    "ncaaf": "https://a.espncdn.com/i/espn/misc_logos/500/ncaa.png",
    "nfl": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/leagues/500/nfl.png",
    "ncaab": "https://a.espncdn.com/i/espn/misc_logos/500/ncaa.png",
    "nba": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/leagues/500/nba.png",
    "wnba": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/leagues/500/wnba.png",
    "mlb": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/leagues/500/mlb.png",
    "wc": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/leagues/500/fifa.png"
}

BREAKING_FIRE_LOGO = "https://files.catbox.moe/rg2p8e.png"

SPORT_CHOICES = {
    "NFL": "nfl",
    "NCAA Football": "ncaaf",
    "NCAA Basketball": "ncaab",
    "NBA": "nba",
    "WNBA": "wnba",
    "MLB": "mlb",
    "World Cup": "wc"
}

GRID_FORMAT_CHOICES = {
    "100_spot": "100_spot",
    "50_spot": "50_spot",
    "25_spot": "25_spot",
    "10_spot": "10_spot",
    "5_spot": "5_spot",
    "4_spot": "4_spot",
    "bankrupt_spot": "bankrupt_spot",
    "3n1_grid": "3n1_grid",
    "2n1_grid": "2n1_grid"
}

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip("#")
    if len(hex_str) != 6:
        return {"red": 0.0, "green": 0.0, "blue": 0.0}
    r = int(hex_str[0:2], 16) / 255.0
    g = int(hex_str[2:4], 16) / 255.0
    b = int(hex_str[4:6], 16) / 255.0
    return {"red": r, "green": g, "blue": b}

def get_readable_text_color(bg_hex, alt_hex="FFFFFF"):
    hex_str = bg_hex.lstrip("#")
    if len(hex_str) != 6:
        return {"red": 1.0, "green": 1.0, "blue": 1.0}
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    if luminance > 0.6:
        return {"red": 0.0, "green": 0.0, "blue": 0.0}
    else:
        alt_str = alt_hex.lstrip("#")
        if len(alt_str) == 6:
            ar = int(alt_str[0:2], 16) / 255.0
            ag = int(alt_str[2:4], 16) / 255.0
            ab = int(alt_str[4:6], 16) / 255.0
            if (0.299 * ar*255 + 0.587 * ag*255 + 0.114 * ab*255) / 255.0 > 0.4:
                return {"red": ar, "green": ag, "blue": ab}
        return {"red": 1.0, "green": 1.0, "blue": 1.0}

def get_short_team_name(team_dict):
    name = team_dict.get("shortDisplayName") or team_dict.get("name") or team_dict.get("displayName") or ""
    return name
