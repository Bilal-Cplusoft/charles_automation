import streamlit as st
import gspread
import requests
import os
import secrets
import datetime

SPREADSHEET_ID = "1PuKW9cDf9jzSsiSpzMUkJLwhbCtKWe0Y76yt_FGG4vc"

LEAGUE_LOGOS = {
    "ncaaf": "https://a.espncdn.com/i/espn/misc_logos/500/ncaa.png",
    "nfl": "https://a.espncdn.com/i/teamlogos/leagues/500/nfl.png",
    "ncaab": "https://a.espncdn.com/i/espn/misc_logos/500/ncaa.png",
    "mlb": "https://a.espncdn.com/i/teamlogos/leagues/500/mlb.png",
    "nba": "https://a.espncdn.com/i/teamlogos/leagues/500/nba.png",
    "wnba": "https://a.espncdn.com/i/teamlogos/leagues/500/wnba.png",
    "wc": "https://a.espncdn.com/i/espn/misc_logos/500/fifa.png",
}

def get_short_team_name(team):
    if not team:
        return ""
    if team.get("name"):
        return team.get("name")
    disp = team.get("displayName", "")
    words = disp.split()
    return " ".join(words[1:]) if len(words) > 1 else disp

def get_high_contrast_logo(logo_url):
    return logo_url or ""

def fetch_espn_games(sport):
    sport_category = "football"
    api_sport = sport
    if sport == "ncaaf":
        sport_category = "football"
        api_sport = "college-football"
    elif sport == "nfl":
        sport_category = "football"
        api_sport = "nfl"
    elif sport == "ncaab":
        sport_category = "basketball"
        api_sport = "mens-college-basketball"
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

    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_category}/{api_sport}/scoreboard"
    try:
        res = requests.get(url, timeout=5).json()
        events = res.get("events", [])
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
            game_name = event.get("name") or f"{away_team.get('displayName', '')} at {home_team.get('displayName', '')}"
            display_label = f"{game_name} ({time_detail})" if time_detail else game_name

            raw_away_color = away_team.get("color", "000000").lstrip("#")
            raw_away_alt   = away_team.get("alternateColor", "FFFFFF").lstrip("#")
            raw_home_color = home_team.get("color", "000000").lstrip("#")
            raw_home_alt   = home_team.get("alternateColor", "FFFFFF").lstrip("#")

            away_logo_raw = away_team.get("logo", "") or (away_team.get("logos")[0].get("href", "") if away_team.get("logos") else "")
            home_logo_raw = home_team.get("logo", "") or (home_team.get("logos")[0].get("href", "") if home_team.get("logos") else "")

            games.append({
                "id": event.get("id"),
                "label": display_label,
                "game_time": time_detail,
                "away_name": get_short_team_name(away_team),
                "away_abbrev": away_team.get("abbreviation", ""),
                "away_color": "#" + (raw_away_color if len(raw_away_color) == 6 else "000000"),
                "away_alt_color": "#" + (raw_away_alt if len(raw_away_alt) == 6 else "FFFFFF"),
                "away_logo": get_high_contrast_logo(away_logo_raw),
                "home_name": get_short_team_name(home_team),
                "home_abbrev": home_team.get("abbreviation", ""),
                "home_color": "#" + (raw_home_color if len(raw_home_color) == 6 else "000000"),
                "home_alt_color": "#" + (raw_home_alt if len(raw_home_alt) == 6 else "FFFFFF"),
                "home_logo": get_high_contrast_logo(home_logo_raw),
            })
        return games
    except Exception:
        return []

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip("#")
    if len(hex_str) != 6:
        return {"red": 0.1, "green": 0.1, "blue": 0.1}
    return {
        "red": int(hex_str[0:2], 16) / 255.0,
        "green": int(hex_str[2:4], 16) / 255.0,
        "blue": int(hex_str[4:6], 16) / 255.0
    }

def get_readable_text_color(bg_hex, alt_hex):
    def hex_to_rgb_tuple(h):
        h = h.lstrip("#")
        if len(h) != 6:
            return (0, 0, 0)
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    def relative_luminance(rgb):
        r, g, b = [c / 255.0 for c in rgb]
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def contrast_ratio(rgb1, rgb2):
        l1 = relative_luminance(rgb1)
        l2 = relative_luminance(rgb2)
        lighter = max(l1, l2)
        darker = min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)

    bg_rgb = hex_to_rgb_tuple(bg_hex)
    alt_rgb = hex_to_rgb_tuple(alt_hex) if alt_hex else (255, 255, 255)
    white_rgb = (255, 255, 255)
    black_rgb = (0, 0, 0)

    cr_alt = contrast_ratio(bg_rgb, alt_rgb)
    if cr_alt >= 3.0:
        return hex_to_rgb(alt_hex)

    cr_white = contrast_ratio(bg_rgb, white_rgb)
    cr_black = contrast_ratio(bg_rgb, black_rgb)
    return hex_to_rgb("ffffff") if cr_white >= cr_black else hex_to_rgb("000000")

LEAGUE_LOGOS = {
    "ncaaf": "https://a.espncdn.com/i/espn/misc_logos/500/ncaa.png",
    "nfl":  "https://a.espncdn.com/i/teamlogos/leagues/500/nfl.png",
    "ncaab": "https://a.espncdn.com/i/espn/misc_logos/500/ncaa.png",
    "mlb":  "https://a.espncdn.com/i/teamlogos/leagues/500/mlb.png",
    "nba":  "https://a.espncdn.com/i/teamlogos/leagues/500/nba.png",
    "wnba": "https://a.espncdn.com/i/teamlogos/leagues/500/wnba.png",
    "wc":   "https://a.espncdn.com/i/teamlogos/leagues/500/fifa.png",
}

def generate_spot_grid_requests(grid_format, new_sheet_id):
    reqs = []
    updates = []

    white_rgb  = {"red": 1.0,  "green": 1.0,  "blue": 1.0}
    gray_rgb   = {"red": 0.85, "green": 0.85, "blue": 0.85}
    black_rgb  = {"red": 0.0,  "green": 0.0,  "blue": 0.0}
    bk_rgb     = {"red": 0.0,  "green": 0.0,  "blue": 0.0}
    bk_txt_rgb = {"red": 1.0,  "green": 1.0,  "blue": 1.0}

    solid  = {"style": "SOLID", "color": black_rgb}
    none_b = {"style": "NONE"}
    colors = [white_rgb, gray_rgb]

    reqs.append({"unmergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 30, "startColumnIndex": 0, "endColumnIndex": 30}}})
    for lc, rc in [(2, 12), (18, 28)]:
        reqs.append({"repeatCell": {"range": {"sheetId": new_sheet_id, "startRowIndex": 1, "endRowIndex": 13, "startColumnIndex": lc, "endColumnIndex": rc}, "cell": {"userEnteredFormat": {"borders": {"top": none_b, "bottom": none_b, "left": none_b, "right": none_b}}}, "fields": "userEnteredFormat.borders"}})

    def fmt(r1, r2, c1, c2, bg, txt=None):
        return {"repeatCell": {
            "range": {"sheetId": new_sheet_id, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2},
            "cell": {"userEnteredFormat": {"backgroundColor": bg, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "textFormat": {"foregroundColor": txt if txt else black_rgb, "bold": True, "fontSize": 12}}},
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
        }}

    def spot_border(r1, r2, c1, c2):
        return {"updateBorders": {"range": {"sheetId": new_sheet_id, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}, "top": solid, "bottom": solid, "left": solid, "right": solid}}

    def grid_border(r1, r2, c1, c2):
        return {"updateBorders": {"range": {"sheetId": new_sheet_id, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}, "top": solid, "bottom": solid, "left": solid, "right": solid, "innerHorizontal": solid, "innerVertical": solid}}

    def paint(r1, r2, c1_l, c2_l, c1_r, c2_r, bg, spot_num, txt=None):
        reqs.append(fmt(r1, r2, c1_l, c2_l, bg, txt))
        reqs.append(spot_border(r1, r2, c1_l, c2_l))
        reqs.append(fmt(r1, r2, c1_r, c2_r, bg, txt))
        reqs.append(spot_border(r1, r2, c1_r, c2_r))
        updates.append({"range": gspread.utils.rowcol_to_a1(r1 + 1, c1_l + 1), "values": [[str(spot_num)]]})
        updates.append({"range": gspread.utils.rowcol_to_a1(r1 + 1, c1_r + 1), "values": [[str(spot_num)]]})

    if grid_format == "10_spot":
        for i in range(10):
            r1 = 2 + i
            paint(r1, r1 + 1, 2, 12, 18, 28, colors[i % 2], i + 1)

    elif grid_format == "5_spot":
        for i in range(5):
            r1 = 2 + i * 2
            paint(r1, r1 + 2, 2, 12, 18, 28, colors[i % 2], i + 1)

    elif grid_format == "50_spot":
        spot_idx = 0
        for r_i in range(10):
            for c_i in range(5):
                r1   = 2 + r_i
                c1_l = 2  + c_i * 2
                c1_r = 18 + c_i * 2
                paint(r1, r1 + 1, c1_l, c1_l + 2, c1_r, c1_r + 2, colors[spot_idx % 2], spot_idx + 1)
                spot_idx += 1

    elif grid_format == "25_spot":
        spot_idx = 0
        for r_i in range(5):
            for c_i in range(5):
                r1   = 2 + r_i * 2
                c1_l = 2  + c_i * 2
                c1_r = 18 + c_i * 2
                paint(r1, r1 + 2, c1_l, c1_l + 2, c1_r, c1_r + 2, colors[spot_idx % 2], spot_idx + 1)
                spot_idx += 1

    elif grid_format == "4_spot":
        quads_l = [(2, 7, 2, 7),   (2, 7, 7, 12),   (7, 12, 2, 7),   (7, 12, 7, 12)]
        quads_r = [(2, 7, 18, 23), (2, 7, 23, 28), (7, 12, 18, 23), (7, 12, 23, 28)]
        quad_bg = [white_rgb, gray_rgb, gray_rgb, white_rgb]
        for idx in range(4):
            r1, r2, c1_l, c2_l = quads_l[idx]
            _,  _,  c1_r, c2_r = quads_r[idx]
            paint(r1, r2, c1_l, c2_l, c1_r, c2_r, quad_bg[idx], idx + 1)

    elif grid_format == "bankrupt_spot":
        spot_idx = 0
        for r_i in range(5):
            for c_i in range(5):
                r1   = 2 + r_i * 2
                c1_l = 2  + c_i * 2
                c1_r = 18 + c_i * 2
                if r_i == 2 and c_i == 2:
                    paint(r1, r1 + 2, c1_l, c1_l + 2, c1_r, c1_r + 2, bk_rgb, "Bankrupt", bk_txt_rgb)
                else:
                    paint(r1, r1 + 2, c1_l, c1_l + 2, c1_r, c1_r + 2, colors[spot_idx % 2], spot_idx + 1)
                spot_idx += 1

    else:
        spot_idx = 0
        for r_i in range(10):
            for c_i in range(10):
                r1   = 2 + r_i
                c1_l = 2  + c_i
                c1_r = 18 + c_i
                reqs.append(fmt(r1, r1 + 1, c1_l, c1_l + 1, white_rgb))
                reqs.append(fmt(r1, r1 + 1, c1_r, c1_r + 1, white_rgb))
                updates.append({"range": gspread.utils.rowcol_to_a1(r1 + 1, c1_l + 1), "values": [[str(spot_idx + 1)]]})
                updates.append({"range": gspread.utils.rowcol_to_a1(r1 + 1, c1_r + 1), "values": [[str(spot_idx + 1)]]})
                spot_idx += 1
        reqs.append(grid_border(2, 12, 2, 12))
        reqs.append(grid_border(2, 12, 18, 28))

    for lc, rc in [(2, 12), (18, 28)]:
        reqs.append(grid_border(1, 2,   lc, rc))
        reqs.append(grid_border(12, 13, lc, rc))

    return reqs, updates


st.set_page_config(page_title="Bet Creation Dashboard", layout="centered")
st.title("Automated Bet Creation")

st.markdown("### Game Selection")
sport = st.selectbox("Sport Type", ["ncaaf", "nfl", "ncaab", "mlb", "nba", "wnba", "wc"], format_func=lambda x: x.upper())

fetched_games = fetch_espn_games(sport)

if fetched_games:
    selected_game_label = st.selectbox(
        "Select Game",
        options=[g["label"] for g in fetched_games],
        help="Select any available game for this sport."
    )
    selected_game = next((g for g in fetched_games if g["label"] == selected_game_label), fetched_games[0])
else:
    st.warning(f"No games found for {sport.upper()} via ESPN API.")
    selected_game = None

with st.form("bet_form"):
    st.markdown("### Square Board Options")
    grid_format = st.selectbox(
        "Grid Size (Spots)", 
        ["3n1_grid", "100_spot", "bankrupt_spot", "50_spot", "25_spot", "10_spot", "5_spot", "4_spot"],
        format_func=lambda x: "3n1 Grid" if x == "3n1_grid" else x
    )
    winners = st.number_input("Number of Winners", min_value=1, value=4)
    cost = st.number_input("Cost Per Square ($)", min_value=1, value=36)
    rake_pct = st.number_input("House Rake (%)", min_value=0.0, max_value=50.0, value=13.33, step=0.5, help="Percentage of total pot kept by house (default 13.33%)")
    submit = st.form_submit_button("Create Bet")

if submit:
    if not selected_game:
        st.error("No game selected. Please select a valid game to proceed.")
        st.stop()

    with st.spinner("Generating board..."):
        cred_file = os.getenv("GCP_KEY")
        if not cred_file or not os.path.exists(cred_file):
            fallback_key = os.path.join(os.path.dirname(__file__), "cosmic-heaven-506712-e4-e652026d0682.json")
            if os.path.exists(fallback_key):
                cred_file = fallback_key
            else:
                st.error("Missing GCP_KEY environment variable or credential file.")
                st.stop()

        game = selected_game

        gc = gspread.service_account(filename=cred_file)
        sh = gc.open_by_key(SPREADSHEET_ID)

        template_id = 1594614647

        target_index = 7
        today = datetime.date.today().strftime("%-m/%-d/%y")
        new_tab_title = f"{today} ${cost} {sport.upper()} {game['away_abbrev'].lower()}/{game['home_abbrev'].lower()}"

        try:
            old_tab = sh.worksheet(new_tab_title)
            sh.del_worksheet(old_tab)
        except Exception:
            pass

        dup_req = {
            "requests": [
                {
                    "duplicateSheet": {
                        "sourceSheetId": template_id,
                        "insertSheetIndex": target_index,
                        "newSheetName": new_tab_title
                    }
                }
            ]
        }
        res = sh.batch_update(dup_req)
        new_sheet_id = res["replies"][0]["duplicateSheet"]["properties"]["sheetId"]

        top_numbers = list(range(10))
        left_numbers = list(range(10))

        if grid_format == "bankrupt_spot":
            grid_spots = 25
        elif grid_format.startswith("3n1_grid"):
            grid_spots = 100
        else:
            try:
                grid_spots = int(grid_format.split('_')[0])
            except Exception:
                grid_spots = 100

        total_pot = grid_spots * cost
        net_payout_pool = int(total_pot * (1.0 - (rake_pct / 100.0)))

        payout_half  = int(net_payout_pool * 0.50)
        payout_final = int(net_payout_pool * 0.50)

        league_logo = LEAGUE_LOGOS.get(sport, "")
        league_logo_formula = f'=IMAGE("{league_logo}")' if league_logo else ""
        away_logo_formula   = f'=IMAGE("{game["away_logo"]}")' if game.get("away_logo") else ""
        home_logo_formula   = f'=IMAGE("{game["home_logo"]}")' if game.get("home_logo") else ""
        # Upload local logo if available, or fall back to public image URL
        breaking_fire_logo = "https://files.catbox.moe/rg2p8e.png"
        community_logo_formula = f'=IMAGE("{breaking_fire_logo}")'

        updates = [
            # Grid 1 Top Header (Row 1) & Side Header (Col A)
            {"range": "A1", "values": [[league_logo_formula]]},
            {"range": "B1", "values": [[away_logo_formula]]},
            {"range": "E1", "values": [[game.get("away_name", "")]]},
            {"range": "K1", "values": [[community_logo_formula]]},
            {"range": "A2", "values": [[home_logo_formula]]},
            {"range": "A3", "values": [[game.get("home_name", "")]]},
            {"range": "A13", "values": [[community_logo_formula]]},

            # Grid 2 Top Header (Row 1) & Side Header (Col Q)
            {"range": "Q1", "values": [[league_logo_formula]]},
            {"range": "R1", "values": [[away_logo_formula]]},
            {"range": "U1", "values": [[game.get("away_name", "")]]},
            {"range": "AA1", "values": [[community_logo_formula]]},
            {"range": "Q2", "values": [[home_logo_formula]]},
            {"range": "Q3", "values": [[game.get("home_name", "")]]},
            {"range": "Q13", "values": [[community_logo_formula]]},

            # Numbers & Cost (Numbers are blank for manual entry via Random.org)
            {"range": "B2", "values": [[f"${cost}"]]},
            {"range": "R2", "values": [[f"${cost}"]]},
            {"range": "C2:L2", "values": [top_numbers]},
            {"range": "S2:AB2", "values": [top_numbers]},
            {"range": "B3:B12", "values": [[n] for n in left_numbers]},
            {"range": "R3:R12", "values": [[n] for n in left_numbers]},
        ]

        payout_merge_reqs = []

        if grid_format.startswith("3n1_grid"):
            g1_payout = net_payout_pool // 3
            g2_payout = net_payout_pool // 3
            g3_payout = net_payout_pool - (g1_payout + g2_payout)

            updates.extend([
                {"range": "C13", "values": [["3n1 PAYOUTS"]]},
                {"range": "E13", "values": [[f"Game 1: ${g1_payout}"]]},
                {"range": "H13", "values": [[f"Game 2: ${g2_payout}"]]},
                {"range": "K13", "values": [[f"Game 3: ${g3_payout}"]]},
                {"range": "S13", "values": [["3n1 PAYOUTS"]]},
                {"range": "U13", "values": [[f"Game 1: ${g1_payout}"]]},
                {"range": "X13", "values": [[f"Game 2: ${g2_payout}"]]},
                {"range": "AA13", "values": [[f"Game 3: ${g3_payout}"]]},
            ])
            payout_merge_reqs.extend([
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 2, "endColumnIndex": 4}, "mergeType": "MERGE_ALL"}},
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 4, "endColumnIndex": 7}, "mergeType": "MERGE_ALL"}},
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 7, "endColumnIndex": 10}, "mergeType": "MERGE_ALL"}},
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 10, "endColumnIndex": 12}, "mergeType": "MERGE_ALL"}},
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 18, "endColumnIndex": 20}, "mergeType": "MERGE_ALL"}},
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 20, "endColumnIndex": 23}, "mergeType": "MERGE_ALL"}},
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 23, "endColumnIndex": 26}, "mergeType": "MERGE_ALL"}},
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 26, "endColumnIndex": 28}, "mergeType": "MERGE_ALL"}},
            ])
        elif sport == "mlb":
            mlb_5inn  = int(net_payout_pool * 0.40)
            mlb_final = int(net_payout_pool * 0.60)

            updates.extend([
                {"range": "C13", "values": [["PAYOUTS"]]},
                {"range": "E13", "values": [[f"Score After 5 Inn: ${mlb_5inn}"]]},
                {"range": "I13", "values": [[f"Final R+H+E: ${mlb_final}"]]},
                {"range": "S13", "values": [["PAYOUTS"]]},
                {"range": "U13", "values": [[f"Score After 5 Inn: ${mlb_5inn}"]]},
                {"range": "Y13", "values": [[f"Final R+H+E: ${mlb_final}"]]},
            ])
            payout_merge_reqs.extend([
                {
                    "mergeCells": {
                        "range": {
                            "sheetId": new_sheet_id,
                            "startRowIndex": 12,
                            "endRowIndex": 13,
                            "startColumnIndex": 4,
                            "endColumnIndex": 8
                        },
                        "mergeType": "MERGE_ALL"
                    }
                },
                {
                    "mergeCells": {
                        "range": {
                            "sheetId": new_sheet_id,
                            "startRowIndex": 12,
                            "endRowIndex": 13,
                            "startColumnIndex": 8,
                            "endColumnIndex": 12
                        },
                        "mergeType": "MERGE_ALL"
                    }
                },
                {
                    "mergeCells": {
                        "range": {
                            "sheetId": new_sheet_id,
                            "startRowIndex": 12,
                            "endRowIndex": 13,
                            "startColumnIndex": 20,
                            "endColumnIndex": 24
                        },
                        "mergeType": "MERGE_ALL"
                    }
                },
                {
                    "mergeCells": {
                        "range": {
                            "sheetId": new_sheet_id,
                            "startRowIndex": 12,
                            "endRowIndex": 13,
                            "startColumnIndex": 24,
                            "endColumnIndex": 28
                        },
                        "mergeType": "MERGE_ALL"
                    }
                }
            ])
        elif grid_format in ["4_spot", "5_spot", "10_spot", "25_spot", "bankrupt_spot"] or sport in ["nba", "wnba"]:
            updates.extend([
                {"range": "C13", "values": [["PAYOUTS"]]},
                {"range": "E13", "values": [["HALFTIME"]]},
                {"range": "G13", "values": [[f"${payout_half}"]]},
                {"range": "I13", "values": [["FINAL"]]},
                {"range": "K13", "values": [[f"${payout_final}"]]},
                {"range": "S13", "values": [["PAYOUTS"]]},
                {"range": "U13", "values": [["HALFTIME"]]},
                {"range": "W13", "values": [[f"${payout_half}"]]},
                {"range": "Y13", "values": [["FINAL"]]},
                {"range": "AA13", "values": [[f"${payout_final}"]]},
            ])
            payout_merge_reqs.extend([
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 2, "endColumnIndex": 4}, "mergeType": "MERGE_ALL"}},
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 4, "endColumnIndex": 6}, "mergeType": "MERGE_ALL"}},
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 6, "endColumnIndex": 8}, "mergeType": "MERGE_ALL"}},
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 8, "endColumnIndex": 10}, "mergeType": "MERGE_ALL"}},
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 10, "endColumnIndex": 12}, "mergeType": "MERGE_ALL"}},
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 18, "endColumnIndex": 20}, "mergeType": "MERGE_ALL"}},
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 20, "endColumnIndex": 22}, "mergeType": "MERGE_ALL"}},
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 22, "endColumnIndex": 24}, "mergeType": "MERGE_ALL"}},
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 24, "endColumnIndex": 26}, "mergeType": "MERGE_ALL"}},
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 26, "endColumnIndex": 28}, "mergeType": "MERGE_ALL"}},
            ])
        elif sport == "nfl":
            nfl_q1    = int(net_payout_pool * 0.175)
            nfl_ht    = int(net_payout_pool * 0.175)
            nfl_q3    = int(net_payout_pool * 0.175)
            nfl_final = int(net_payout_pool * 0.40)
            nfl_rev   = int(net_payout_pool * 0.01875)

            updates.extend([
                {"range": "C13", "values": [["PAYOUTS"]]},
                {"range": "E13", "values": [[f"Q1 ${nfl_q1}"]]},
                {"range": "G13", "values": [[f"HT ${nfl_ht}"]]},
                {"range": "I13", "values": [[f"Q3 ${nfl_q3}"]]},
                {"range": "K13", "values": [[f"FINAL ${nfl_final}"]]},
                {"range": "E14", "values": [[f"Rev ${nfl_rev}"]]},
                {"range": "G14", "values": [[f"Rev ${nfl_rev}"]]},
                {"range": "I14", "values": [[f"Rev ${nfl_rev}"]]},
                {"range": "K14", "values": [[f"Rev ${nfl_rev}"]]},
                {"range": "S13", "values": [["PAYOUTS"]]},
                {"range": "U13", "values": [[f"Q1 ${payout_q1}"]]},
                {"range": "W13", "values": [[f"HT ${payout_q1}"]]},
                {"range": "Y13", "values": [[f"Q3 ${payout_q1}"]]},
                {"range": "AA13", "values": [[f"FINAL ${int(total_pot * 0.40)}"]]},
                {"range": "U14", "values": [[f"Rev ${payout_rev}"]]},
                {"range": "W14", "values": [[f"Rev ${payout_rev}"]]},
                {"range": "Y14", "values": [[f"Rev ${payout_rev}"]]},
                {"range": "AA14", "values": [[f"Rev ${int(payout_rev * 1.5)}"]]},
            ])
        elif sport == "wc":
            updates.extend([
                {"range": "C13", "values": [["PAYOUTS"]]},
                {"range": "E13", "values": [[f"Halftime score: ${payout_half}"]]},
                {"range": "I13", "values": [[f"Final Score: ${payout_final}"]]},
                {"range": "E14", "values": [[f"Final SOG : ${payout_q1}"]]},
                {"range": "R13", "values": [["PAYOUTS"]]},
                {"range": "T13", "values": [[f"HT ${int(payout_half/2)}"]]},
                {"range": "V13", "values": [["FINAL"]]},
                {"range": "R14", "values": [["REVERSE"]]},
                {"range": "T14", "values": [[f"HT ${int(payout_q1)}"]]},
                {"range": "V14", "values": [["FINAL"]]},
            ])

        grid_reqs, grid_updates = generate_spot_grid_requests(grid_format, new_sheet_id)
        updates.extend(grid_updates)

        new_sheet = sh.get_worksheet_by_id(new_sheet_id)
        new_sheet.batch_clear(["C3:L12", "S3:AB12", "C13:L14", "S13:AB14"])

        away_rgb      = hex_to_rgb(game["away_color"])
        away_text_rgb = get_readable_text_color(game["away_color"], game.get("away_alt_color"))

        home_rgb      = hex_to_rgb(game["home_color"])
        home_text_rgb = get_readable_text_color(game["home_color"], game.get("home_alt_color"))

        yellow_rgb = {"red": 1.0, "green": 1.0, "blue": 0.0}
        black_rgb  = {"red": 0.0, "green": 0.0, "blue": 0.0}

        payout_format_reqs = [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": new_sheet_id,
                        "startRowIndex": 12,
                        "endRowIndex": 13,
                        "startColumnIndex": 2,
                        "endColumnIndex": 12
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": yellow_rgb,
                            "textFormat": {
                                "foregroundColor": black_rgb,
                                "bold": True,
                                "fontSize": 11
                            },
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                }
            },
            {
                "repeatCell": {
                    "range": {
                        "sheetId": new_sheet_id,
                        "startRowIndex": 12,
                        "endRowIndex": 13,
                        "startColumnIndex": 18,
                        "endColumnIndex": 28
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": yellow_rgb,
                            "textFormat": {
                                "foregroundColor": black_rgb,
                                "bold": True,
                                "fontSize": 11
                            },
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                }
            }
        ]

        green_rgb = hex_to_rgb("00B050")
        white_rgb = hex_to_rgb("FFFFFF")

        header_reqs = [
            # Row height adjustments for logo proportion (Row 1 & 2 set to 50px height)
            {"updateDimensionProperties": {"range": {"sheetId": new_sheet_id, "dimension": "ROWS", "startIndex": 0, "endIndex": 2}, "properties": {"pixelSize": 50}, "fields": "pixelSize"}},

            # Top Header Merges (Grid 1)
            {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 4}, "mergeType": "MERGE_ALL"}},
            {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 4, "endColumnIndex": 10}, "mergeType": "MERGE_ALL"}},
            {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 10, "endColumnIndex": 12}, "mergeType": "MERGE_ALL"}},
            # Side Header Merge (Grid 1)
            {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 2, "endRowIndex": 12, "startColumnIndex": 0, "endColumnIndex": 1}, "mergeType": "MERGE_ALL"}},
            # Bottom Left Logo Merge (Grid 1: A13:A14)
            {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 14, "startColumnIndex": 0, "endColumnIndex": 1}, "mergeType": "MERGE_ALL"}},

            # Top Header Merges (Grid 2)
            {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 17, "endColumnIndex": 20}, "mergeType": "MERGE_ALL"}},
            {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 20, "endColumnIndex": 26}, "mergeType": "MERGE_ALL"}},
            {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 26, "endColumnIndex": 28}, "mergeType": "MERGE_ALL"}},
            # Side Header Merge (Grid 2)
            {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 2, "endRowIndex": 12, "startColumnIndex": 16, "endColumnIndex": 17}, "mergeType": "MERGE_ALL"}},
            # Bottom Left Logo Merge (Grid 2: Q13:Q14)
            {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 14, "startColumnIndex": 16, "endColumnIndex": 17}, "mergeType": "MERGE_ALL"}},

            # Logo Cells Styling (Grid 1 & Grid 2) - Enforce White Fill (#FFFFFF) for 100% Logo Visibility
            {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 4},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": white_rgb,
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment)"
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 10, "endColumnIndex": 12},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": white_rgb,
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment)"
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 0, "endColumnIndex": 1},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": white_rgb,
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment)"
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 14, "startColumnIndex": 0, "endColumnIndex": 1},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": white_rgb,
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment)"
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 16, "endColumnIndex": 20},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": white_rgb,
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment)"
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 26, "endColumnIndex": 28},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": white_rgb,
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment)"
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 16, "endColumnIndex": 17},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": white_rgb,
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment)"
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 14, "startColumnIndex": 16, "endColumnIndex": 17},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": white_rgb,
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment)"
                }
            },

            # Away Header Name Styling (Row 1) - Grid 1 (E1..J1)
            {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 4, "endColumnIndex": 10},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": away_rgb,
                            "textFormat": {"foregroundColor": away_text_rgb, "bold": True, "fontSize": 16},
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                }
            },
            # Away Numbers Header Styling (Row 2) - Grid 1 (C2..L2)
            {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 2, "endColumnIndex": 12},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": away_rgb,
                            "textFormat": {"foregroundColor": away_text_rgb, "bold": True, "fontSize": 14},
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                }
            },

            # Away Header Name Styling (Row 1) - Grid 2 (U1..Z1)
            {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 20, "endColumnIndex": 26},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": away_rgb,
                            "textFormat": {"foregroundColor": away_text_rgb, "bold": True, "fontSize": 16},
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                }
            },
            # Away Numbers Header Styling (Row 2) - Grid 2 (S2..AB2)
            {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 18, "endColumnIndex": 28},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": away_rgb,
                            "textFormat": {"foregroundColor": away_text_rgb, "bold": True, "fontSize": 14},
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                }
            },

            # Home Header Side Styling (A3:A12 Name vertical) - Grid 1
            {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 2, "endRowIndex": 12, "startColumnIndex": 0, "endColumnIndex": 1},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": home_rgb,
                            "textFormat": {"foregroundColor": home_text_rgb, "bold": True, "fontSize": 16},
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE",
                            "textRotation": {"angle": 90}
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,textRotation)"
                }
            },
            # Home Numbers Header Styling (Col B: B3..B12) - Grid 1
            {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 2, "endRowIndex": 12, "startColumnIndex": 1, "endColumnIndex": 2},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": home_rgb,
                            "textFormat": {"foregroundColor": home_text_rgb, "bold": True, "fontSize": 14},
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                }
            },

            # Home Header Side Styling (Q3:Q12 Name vertical) - Grid 2
            {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 2, "endRowIndex": 12, "startColumnIndex": 16, "endColumnIndex": 17},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": home_rgb,
                            "textFormat": {"foregroundColor": home_text_rgb, "bold": True, "fontSize": 16},
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE",
                            "textRotation": {"angle": 90}
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,textRotation)"
                }
            },
            # Home Numbers Header Styling (Col R: R3..R12) - Grid 2
            {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 2, "endRowIndex": 12, "startColumnIndex": 17, "endColumnIndex": 18},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": home_rgb,
                            "textFormat": {"foregroundColor": home_text_rgb, "bold": True, "fontSize": 14},
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                }
            },

            # Cost Cells (B2 & R2) - Green background
            {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 1, "endColumnIndex": 2},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": green_rgb,
                            "textFormat": {"foregroundColor": white_rgb, "bold": True, "fontSize": 14},
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 17, "endColumnIndex": 18},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": green_rgb,
                            "textFormat": {"foregroundColor": white_rgb, "bold": True, "fontSize": 14},
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                }
            }
        ]

        body = {
            "requests": grid_reqs + payout_merge_reqs + payout_format_reqs + header_reqs
        }
        sh.batch_update(body)

        new_sheet.batch_update(updates, value_input_option="USER_ENTERED")

        st.success(f"Successfully generated: {new_tab_title}")
        st.markdown(f"**[Click here to view your Google Sheet](https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit)**")
