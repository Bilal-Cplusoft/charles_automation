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
    "nhl": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/leagues/500/nhl.png",
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
    "NHL": "nhl",
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

def get_relative_luminance(r, g, b):
    def adjust(c):
        c_s = c / 255.0
        return c_s / 12.92 if c_s <= 0.03928 else ((c_s + 0.055) / 1.055) ** 2.4
    return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)

def get_contrast_ratio(rgb1, rgb2):
    l1 = get_relative_luminance(*rgb1)
    l2 = get_relative_luminance(*rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

def get_readable_text_color(bg_hex, alt_hex="FFFFFF"):
    bg = bg_hex.lstrip("#")
    if len(bg) != 6:
        return {"red": 1.0, "green": 1.0, "blue": 1.0}
    r, g, b = int(bg[0:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)
    
    black_contrast = get_contrast_ratio((r, g, b), (0, 0, 0))
    
    alt = alt_hex.lstrip("#")
    if len(alt) == 6:
        ar, ag, ab = int(alt[0:2], 16), int(alt[2:4], 16), int(alt[4:6], 16)
        alt_contrast = get_contrast_ratio((r, g, b), (ar, ag, ab))
        if alt_contrast >= 4.5:
            return {"red": ar / 255.0, "green": ag / 255.0, "blue": ab / 255.0}

    white_contrast = get_contrast_ratio((r, g, b), (255, 255, 255))
    if white_contrast >= black_contrast:
        return {"red": 1.0, "green": 1.0, "blue": 1.0}
    else:
        return {"red": 0.0, "green": 0.0, "blue": 0.0}

def get_short_team_name(team_dict):
    name = team_dict.get("shortDisplayName") or team_dict.get("name") or team_dict.get("displayName") or ""
    return name
