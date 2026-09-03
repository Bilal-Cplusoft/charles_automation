import os
import datetime
import gspread
from config import (
    SPREADSHEET_ID,
    TEMPLATE_SHEET_ID,
    LEAGUE_LOGOS,
    BREAKING_FIRE_LOGO,
    hex_to_rgb,
    get_readable_text_color
)
from grid_builder import generate_spot_grid_requests

def get_gspread_client():
    cred_file = os.getenv("GCP_KEY")
    if not cred_file or not os.path.exists(cred_file):
        fallback_key = os.path.join(os.path.dirname(__file__), "cosmic-heaven-506712-e4-e652026d0682.json")
        if os.path.exists(fallback_key):
            cred_file = fallback_key
        else:
            raise FileNotFoundError("Missing GCP_KEY environment variable or credential file.")
    return gspread.service_account(filename=cred_file)

def create_game_tab(sh, grid_format, winners, cost, rake_pct, sport, game, game1=None, game2=None, game3=None):
    worksheets = sh.worksheets()
    target_index = len(worksheets)
    for idx, ws in enumerate(worksheets):
        if "daily contest" in ws.title.lower():
            target_index = idx + 1
            break

    game_date_str = game.get("game_date")
    if game_date_str:
        today_label = game_date_str
    else:
        today_label = datetime.date.today().strftime("%-m/%-d/%y")
    
    def clean_time(time_str):
        if not time_str: return ""
        import re
        t = re.sub(r'(?i)[a-z\s]+', '', time_str.strip()).strip()
        m = re.match(r'^(\d+):(\d{2})$', t)
        if m:
            hrs, mins = m.group(1), m.group(2)
            if mins == "00":
                val = hrs
            else:
                val = f"{hrs}{mins}"
        else:
            val = t.replace(":", "")
        if len(val) > 3:
            val = val[:3]
        return f"{val}MT"

    if grid_format.startswith("3n1_grid"):
        new_tab_title = f"{today_label} {sport.upper()} 3n1"
        try:
            source_ws = sh.worksheet("3n1")
            source_sheet_id = source_ws.id
        except Exception:
            source_sheet_id = TEMPLATE_SHEET_ID
    elif grid_format.startswith("2n1_grid"):
        new_tab_title = f"{today_label} {sport.upper()} 2n1"
        try:
            source_ws = sh.worksheet("2n1")
            source_sheet_id = source_ws.id
        except Exception:
            source_sheet_id = TEMPLATE_SHEET_ID
    else:
        new_tab_title = f"{today_label} ${cost} {sport.upper()} {game['away_abbrev'].lower()}/{game['home_abbrev'].lower()}"
        source_sheet_id = TEMPLATE_SHEET_ID

    for ws in sh.worksheets():
        if ws.title == new_tab_title or ws.title.startswith(f"{new_tab_title}_conflict"):
            try:
                sh.del_worksheet(ws)
            except Exception:
                pass

    dup_req = {
        "requests": [
            {
                "duplicateSheet": {
                    "sourceSheetId": source_sheet_id,
                    "insertSheetIndex": target_index,
                    "newSheetName": new_tab_title
                }
            }
        ]
    }
    res = sh.batch_update(dup_req)
    new_sheet_id = res["replies"][0]["duplicateSheet"]["properties"]["sheetId"]

    try:
        sh.batch_update({
            "requests": [{
                "updateSheetProperties": {
                    "properties": {"sheetId": new_sheet_id, "title": new_tab_title},
                    "fields": "title"
                }
            }]
        })
    except Exception:
        pass

    top_numbers = ["" for _ in range(10)]
    left_numbers = [[""] for _ in range(10)]
    top_numbers_5 = ["" for _ in range(5)]
    left_numbers_5 = [[""] for _ in range(5)]

    if grid_format in ["bankrupt_spot", "3n1_grid", "25_spot"]:
        grid_spots = 25
    else:
        try:
            grid_spots = int(grid_format.split('_')[0])
        except Exception:
            grid_spots = 100

    total_pot = grid_spots * cost
    net_payout_pool = int(total_pot * (1.0 - (rake_pct / 100.0)))

    league_logo = LEAGUE_LOGOS.get(sport, "")
    league_logo_formula = f'=IMAGE("{league_logo}")' if league_logo else ""
    away_logo_formula   = f'=IMAGE("{game["away_logo"]}")' if game and game.get("away_logo") else ""
    home_logo_formula   = f'=IMAGE("{game["home_logo"]}")' if game and game.get("home_logo") else ""
    community_logo_formula = f'=IMAGE("{BREAKING_FIRE_LOGO}")'

    payout_merge_reqs = []

    if grid_format.startswith("3n1_grid") or grid_format.startswith("2n1_grid"):
        g1_away_name = game1.get("away_name", game1.get("away_abbrev", "G1-A")) if game1 else "G1-A"
        g2_away_name = game2.get("away_name", game2.get("away_abbrev", "G2-A")) if game2 else "G2-A"
        g3_away_name = game3.get("away_name", game3.get("away_abbrev", "G3-A")) if game3 else "G3-A"

        g1_home_name = game1.get("home_name", game1.get("home_abbrev", "G1-H")) if game1 else "G1-H"
        g2_home_name = game2.get("home_name", game2.get("home_abbrev", "G2-H")) if game2 else "G2-H"
        g3_home_name = game3.get("home_name", game3.get("home_abbrev", "G3-H")) if game3 else "G3-H"

        g1_alogo = f'=IMAGE("{game1["away_logo"]}")' if game1 and game1.get("away_logo") else ""
        g1_hlogo = f'=IMAGE("{game1["home_logo"]}")' if game1 and game1.get("home_logo") else ""
        g2_alogo = f'=IMAGE("{game2["away_logo"]}")' if game2 and game2.get("away_logo") else ""
        g2_hlogo = f'=IMAGE("{game2["home_logo"]}")' if game2 and game2.get("home_logo") else ""
        g3_alogo = f'=IMAGE("{game3["away_logo"]}")' if game3 and game3.get("away_logo") else ""
        g3_hlogo = f'=IMAGE("{game3["home_logo"]}")' if game3 and game3.get("home_logo") else ""

        g1_time = clean_time(game1.get("game_time", "")) if game1 else ""
        g2_time = clean_time(game2.get("game_time", "")) if game2 else ""
        g3_time = clean_time(game3.get("game_time", "")) if game3 else ""

        def get_fmt(bg, txt):
            return {"userEnteredFormat": {"backgroundColor": bg, "textFormat": {"foregroundColor": txt}}}
        
        g1_a_bg = hex_to_rgb(game1["away_color"]) if game1 else hex_to_rgb("000000")
        g1_a_txt = get_readable_text_color(game1["away_color"], game1.get("away_alt_color")) if game1 else hex_to_rgb("FFFFFF")
        g1_h_bg = hex_to_rgb(game1["home_color"]) if game1 else hex_to_rgb("000000")
        g1_h_txt = get_readable_text_color(game1["home_color"], game1.get("home_alt_color")) if game1 else hex_to_rgb("FFFFFF")
        
        g2_a_bg = hex_to_rgb(game2["away_color"]) if game2 else hex_to_rgb("000000")
        g2_a_txt = get_readable_text_color(game2["away_color"], game2.get("away_alt_color")) if game2 else hex_to_rgb("FFFFFF")
        g2_h_bg = hex_to_rgb(game2["home_color"]) if game2 else hex_to_rgb("000000")
        g2_h_txt = get_readable_text_color(game2["home_color"], game2.get("home_alt_color")) if game2 else hex_to_rgb("FFFFFF")
        
        g3_a_bg = hex_to_rgb(game3["away_color"]) if game3 else hex_to_rgb("000000")
        g3_a_txt = get_readable_text_color(game3["away_color"], game3.get("away_alt_color")) if game3 else hex_to_rgb("FFFFFF")
        g3_h_bg = hex_to_rgb(game3["home_color"]) if game3 else hex_to_rgb("000000")
        g3_h_txt = get_readable_text_color(game3["home_color"], game3.get("home_alt_color")) if game3 else hex_to_rgb("FFFFFF")

        def req_bg(r1, r2, c1, c2, bg, txt):
            return {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2},
                    "cell": get_fmt(bg, txt),
                    "fields": "userEnteredFormat(backgroundColor,textFormat.foregroundColor)"
                }
            }

        def req_title_fmt(r1, r2, c1, c2, bg, txt, font_size=24):
            return {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": bg,
                            "textFormat": {"foregroundColor": txt, "bold": True, "fontSize": font_size},
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                }
            }

        if grid_format.startswith("2n1_grid"):
            per_game_pool = net_payout_pool // 2
            p1 = int(round((per_game_pool * 0.18) / 5.0) * 5)
            p2 = int(round((per_game_pool * 0.23) / 5.0) * 5)
            p3 = p1
            p_fs = per_game_pool - (p1 + p2 + p3)

            cost_val = int(cost) if int(cost) == float(cost) else cost
            cost_str = f"${cost_val}"

            updates = [
                # Left Grid Top Logos & Headers
                {"range": "A1", "values": [[league_logo_formula]]},
                {"range": "D1", "values": [[g1_alogo]]},
                {"range": "D2", "values": [[g2_alogo]]},
                {"range": "E1", "values": [[g1_away_name]]},
                {"range": "E2", "values": [[g2_away_name]]},
                {"range": "M1", "values": [[community_logo_formula]]},
                {"range": "A3", "values": [[g1_hlogo]]},
                {"range": "B3", "values": [[g2_hlogo]]},
                {"range": "A5", "values": [[g1_home_name]]},
                {"range": "B5", "values": [[g2_home_name]]},
                
                # C3:D4 Cost & Game Labels (G1 / G1 / G2)
                {"range": "C3", "values": [[cost_str]]},
                {"range": "D3", "values": [["G1"]]},
                {"range": "C4", "values": [["G1"]]},
                {"range": "D4", "values": [["G2"]]},

                # Left Grid Payouts & Game Times (Row 15 & 16)
                {"range": "C15", "values": [["G1"]]},
                {"range": "D15", "values": [[g1_time]]},
                {"range": "E15", "values": [["PAYOUTS"]]},
                {"range": "G15", "values": [[f"1st {p1}"]]},
                {"range": "I15", "values": [[f"2nd {p2}"]]},
                {"range": "K15", "values": [[f"3rd {p3}"]]},
                {"range": "M15", "values": [[f"FS: {p_fs}"]]},

                {"range": "C16", "values": [["G2"]]},
                {"range": "D16", "values": [[g2_time]]},
                {"range": "E16", "values": [["PAYOUTS"]]},
                {"range": "G16", "values": [[f"1st {p1}"]]},
                {"range": "I16", "values": [[f"2nd {p2}"]]},
                {"range": "K16", "values": [[f"3rd {p3}"]]},
                {"range": "M16", "values": [[f"FS: {p_fs}"]]},
            ]

            white_bg  = {"red": 1.0, "green": 1.0, "blue": 1.0}
            white_rgb = white_bg
            black_bg  = {"red": 0.0, "green": 0.0, "blue": 0.0}

            def req_bg_txt(r1, r2, c1, c2, bg, txt):
                return {
                    "repeatCell": {
                        "range": {"sheetId": new_sheet_id, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2},
                        "cell": {"userEnteredFormat": {"backgroundColor": bg, "textFormat": {"foregroundColor": txt}}},
                        "fields": "userEnteredFormat(backgroundColor,textFormat.foregroundColor)"
                    }
                }

            payout_merge_reqs.extend([
                # Unmerge Row 3 & Row 4 horizontal number cells (E3:N4)
                {"unmergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 2, "endRowIndex": 4, "startColumnIndex": 4, "endColumnIndex": 14}}},

                # A1:B2 Black Background for top left NFL logo margin
                req_bg_txt(0, 2, 0, 2, black_bg, white_rgb),

                # Away 1 Logo C1:D1 & Away 1 Name E1:L1 (Game 1 Away Color)
                req_bg_txt(0, 1, 2, 4, g1_a_bg, g1_a_txt),
                req_title_fmt(0, 1, 4, 12, g1_a_bg, g1_a_txt, font_size=28),

                # Away 2 Logo C2:D2 & Away 2 Name E2:L2 (Game 2 Away Color)
                req_bg_txt(1, 2, 2, 4, g2_a_bg, g2_a_txt),
                req_title_fmt(1, 2, 4, 12, g2_a_bg, g2_a_txt, font_size=28),

                # Top Right Breaking Fire Logo M1:N2 WHITE Background
                req_bg_txt(0, 2, 12, 14, white_bg, black_bg),

                # Horizontal Number Rows E3:N3 (Game 1 Away Color) & E4:N4 (Game 2 Away Color)
                req_bg_txt(2, 3, 4, 14, g1_a_bg, g1_a_txt),
                req_bg_txt(3, 4, 4, 14, g2_a_bg, g2_a_txt),
                
                # Home 1 Logo A3:A4 & Home 2 Logo B3:B4
                req_bg_txt(2, 4, 0, 1, g1_h_bg, g1_h_txt),
                req_bg_txt(2, 4, 1, 2, g2_h_bg, g2_h_txt),

                # Home 1 Name A5:A14 & Home 2 Name B5:B14
                req_bg_txt(4, 14, 0, 1, g1_h_bg, g1_h_txt),
                req_bg_txt(4, 14, 1, 2, g2_h_bg, g2_h_txt),

                # Vertical Number Columns C5:C14 (Game 1 Home Color) & D5:D14 (Game 2 Home Color)
                req_bg_txt(4, 14, 2, 3, g1_h_bg, g1_h_txt),
                req_bg_txt(4, 14, 3, 4, g2_h_bg, g2_h_txt),

                {"updateDimensionProperties": {
                    "range": {"sheetId": new_sheet_id, "dimension": "ROWS", "startIndex": 0, "endIndex": 2},
                    "properties": {"pixelSize": 50},
                    "fields": "pixelSize"
                }},
            ])

        else: # 3n1_grid
            if grid_format.startswith("3n1_grid") or cost == 36:
                p123, p_fs = 50, 100
            else:
                per_game_pool = net_payout_pool // 3
                raw_share = per_game_pool // 5
                share = int(round(raw_share / 5.0) * 5)
                p123 = share
                p_fs = share * 2
            
            updates = [
                {"range": "A1", "values": [[league_logo_formula]]},
                {"range": "D1", "values": [[g1_alogo]]},
                {"range": "D2", "values": [[g2_alogo]]},
                {"range": "D3", "values": [[g3_alogo]]},
                {"range": "G1", "values": [[g1_away_name]]},
                {"range": "G2", "values": [[g2_away_name]]},
                {"range": "G3", "values": [[g3_away_name]]},
                {"range": "A4", "values": [[g1_hlogo]]},
                {"range": "B4", "values": [[g2_hlogo]]},
                {"range": "C4", "values": [[g3_hlogo]]},
                {"range": "A7", "values": [[g1_home_name]]},
                {"range": "B7", "values": [[g2_home_name]]},
                {"range": "C7", "values": [[g3_home_name]]},
                
                {"range": "D4", "values": [[float(cost)]]},
                {"range": "T4", "values": [[float(cost)]]},
                
                {"range": "D17", "values": [["Game 1"]]},
                {"range": "F17", "values": [[g1_time]]},
                {"range": "I17", "values": [[f"1st {p123}"]]},
                {"range": "K17", "values": [[f"2nd {p123}"]]},
                {"range": "M17", "values": [[f"3rd {p123}"]]},
                {"range": "O17", "values": [[f"FS: {p_fs}"]]},

                {"range": "D18", "values": [["Game 2"]]},
                {"range": "F18", "values": [[g2_time]]},
                {"range": "I18", "values": [[f"1st {p123}"]]},
                {"range": "K18", "values": [[f"2nd {p123}"]]},
                {"range": "M18", "values": [[f"3rd {p123}"]]},
                {"range": "O18", "values": [[f"FS: {p_fs}"]]},

                {"range": "D19", "values": [["Game 3"]]},
                {"range": "F19", "values": [[g3_time]]},
                {"range": "I19", "values": [[f"1st {p123}"]]},
                {"range": "K19", "values": [[f"2nd {p123}"]]},
                {"range": "M19", "values": [[f"3rd {p123}"]]},
                {"range": "O19", "values": [[f"FS: {p_fs}"]]},
            ]

            spot = 1
            for rp in [7, 9, 11, 13, 15]:
                for cp in ["G", "I", "K", "M", "O"]:
                    updates.append({"range": f"{cp}{rp}", "values": [[str(spot)]]})
                    spot += 1

            spot = 1
            for rp in [7, 9, 11, 13, 15]:
                for cp in ["W", "Y", "AA", "AC", "AE"]:
                    updates.append({"range": f"{cp}{rp}", "values": [[str(spot)]]})
                    spot += 1

            updates.extend([
                {"range": "A17", "values": [[community_logo_formula]]},
            ])

            payout_merge_reqs.extend([
                {"unmergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 25, "startColumnIndex": 16, "endColumnIndex": 19}}},
                {
                    "repeatCell": {
                        "range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 25, "startColumnIndex": 16, "endColumnIndex": 19},
                        "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "borders": {"top": {"style": "NONE"}, "bottom": {"style": "NONE"}, "left": {"style": "NONE"}, "right": {"style": "NONE"}}}},
                        "fields": "userEnteredFormat(backgroundColor,borders)"
                    }
                },
                req_bg(0, 1, 3, 4, g1_a_bg, g1_a_txt), # D1 Away 1 logo bg
                req_bg(1, 2, 3, 4, g2_a_bg, g2_a_txt), # D2 Away 2 logo bg
                req_bg(2, 3, 3, 4, g3_a_bg, g3_a_txt), # D3 Away 3 logo bg
                
                req_bg(3, 4, 0, 1, g1_h_bg, g1_h_txt), # A4 Home 1 logo bg
                req_bg(3, 4, 1, 2, g2_h_bg, g2_h_txt), # B4 Home 2 logo bg
                req_bg(3, 4, 2, 3, g3_h_bg, g3_h_txt), # C4 Home 3 logo bg

                req_title_fmt(0, 1, 6, 16, g1_a_bg, g1_a_txt, font_size=24), # G1:P1 (Left Away 1)
                req_title_fmt(1, 2, 6, 16, g2_a_bg, g2_a_txt, font_size=24), # G2:P2 (Left Away 2)
                req_title_fmt(2, 3, 6, 16, g3_a_bg, g3_a_txt, font_size=24), # G3:P3 (Left Away 3)
                
                req_bg(3, 4, 6, 16, g1_a_bg, g1_a_txt), # G4:P4 (Left Away 1 strip)
                req_bg(4, 5, 6, 16, g2_a_bg, g2_a_txt), # G5:P5 (Left Away 2 strip)
                req_bg(5, 6, 6, 16, g3_a_bg, g3_a_txt), # G6:P6 (Left Away 3 strip)

                req_bg(6, 16, 0, 1, g1_h_bg, g1_h_txt), # A7:A16 (Left Home 1)
                req_bg(6, 16, 1, 2, g2_h_bg, g2_h_txt), # B7:B16 (Left Home 2)
                req_bg(6, 16, 2, 3, g3_h_bg, g3_h_txt), # C7:C16 (Left Home 3)

                req_bg(6, 16, 3, 4, g1_h_bg, g1_h_txt), # D7:D16 (Left Home 1 strip)
                req_bg(6, 16, 4, 5, g2_h_bg, g2_h_txt), # E7:E16 (Left Home 2 strip)
                req_bg(6, 16, 5, 6, g3_h_bg, g3_h_txt), # F7:F16 (Left Home 3 strip)
                
                {
                    "repeatCell": {
                        "range": {"sheetId": new_sheet_id, "startRowIndex": 16, "endRowIndex": 19, "startColumnIndex": 0, "endColumnIndex": 3},
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0}
                            }
                        },
                        "fields": "userEnteredFormat.backgroundColor"
                    }
                },
                {
                    "repeatCell": {
                        "range": {"sheetId": new_sheet_id, "startRowIndex": 16, "endRowIndex": 19, "startColumnIndex": 3, "endColumnIndex": 16},
                        "cell": {
                            "userEnteredFormat": {
                                "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True, "fontSize": 10},
                                "horizontalAlignment": "CENTER",
                                "verticalAlignment": "MIDDLE"
                            }
                        },
                        "fields": "userEnteredFormat(textFormat,horizontalAlignment,verticalAlignment)"
                    }
                },
                {
                    "repeatCell": {
                        "range": {"sheetId": new_sheet_id, "startRowIndex": 6, "endRowIndex": 16, "startColumnIndex": 6, "endColumnIndex": 16},
                        "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}},
                        "fields": "userEnteredFormat.backgroundColor"
                    }
                },
                {
                    "repeatCell": {
                        "range": {"sheetId": new_sheet_id, "startRowIndex": 6, "endRowIndex": 16, "startColumnIndex": 22, "endColumnIndex": 32},
                        "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}},
                        "fields": "userEnteredFormat.backgroundColor"
                    }
                },
                {"updateDimensionProperties": {
                    "range": {"sheetId": new_sheet_id, "dimension": "ROWS", "startIndex": 0, "endIndex": 3},
                    "properties": {"pixelSize": 50},
                    "fields": "pixelSize"
                }},
            ])
    else:
        updates = [
            {"range": "A1", "values": [[league_logo_formula]]},
            {"range": "B1", "values": [[away_logo_formula]]},
            {"range": "E1", "values": [[game.get("away_name", "")]]},
            {"range": "K1", "values": [[community_logo_formula]]},
            {"range": "A2", "values": [[home_logo_formula]]},
            {"range": "A3", "values": [[game.get("home_name", "")]]},
            {"range": "A13", "values": [[community_logo_formula]]},
            {"range": "B13", "values": [[clean_time(game.get("game_time", ""))]]},

            {"range": "Q1", "values": [[league_logo_formula]]},
            {"range": "R1", "values": [[away_logo_formula]]},
            {"range": "U1", "values": [[game.get("away_name", "")]]},
            {"range": "AA1", "values": [[community_logo_formula]]},
            {"range": "Q2", "values": [[home_logo_formula]]},
            {"range": "Q3", "values": [[game.get("home_name", "")]]},
            {"range": "Q13", "values": [[community_logo_formula]]},
            {"range": "R13", "values": [[clean_time(game.get("game_time", ""))]]},

            {"range": "B2", "values": [[f"${cost}"]]},
            {"range": "R2", "values": [[f"${cost}"]]},
            {"range": "C2:L2", "values": [top_numbers]},
            {"range": "S2:AB2", "values": [top_numbers]},
            {"range": "B3:B12", "values": left_numbers},
            {"range": "R3:R12", "values": left_numbers},
        ]

        payout_merge_reqs = [
            {"unmergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 14, "startColumnIndex": 2, "endColumnIndex": 28}}}
        ]

        if winners == 1:
            updates.extend([
                {"range": "C13", "values": [["PAYOUTS"]]},
                {"range": "E13", "values": [[f"FINAL: ${net_payout_pool}"]]},
                {"range": "S13", "values": [["PAYOUTS"]]},
                {"range": "U13", "values": [[f"FINAL: ${net_payout_pool}"]]},
            ])
            payout_merge_reqs.extend([
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 2, "endColumnIndex": 4}, "mergeType": "MERGE_ALL"}},
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 4, "endColumnIndex": 12}, "mergeType": "MERGE_ALL"}},
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 18, "endColumnIndex": 20}, "mergeType": "MERGE_ALL"}},
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 20, "endColumnIndex": 28}, "mergeType": "MERGE_ALL"}},
            ])
        elif winners == 2:
            if cost == 55:
                p2 = 100
            else:
                p2 = int(round((net_payout_pool // 2) / 5.0) * 5)

            if sport == "mlb":
                lbl1 = f"Score After 5 Inn: ${p2}"
                lbl2 = f"Final R+H+E: ${p2}"
            else:
                lbl1 = f"HALFTIME: ${p2}"
                lbl2 = f"FINAL: ${p2}"

            updates.extend([
                {"range": "C13", "values": [["PAYOUTS"]]},
                {"range": "E13", "values": [[lbl1]]},
                {"range": "I13", "values": [[lbl2]]},
                {"range": "S13", "values": [["PAYOUTS"]]},
                {"range": "U13", "values": [[lbl1]]},
                {"range": "Y13", "values": [[lbl2]]},
            ])
            payout_merge_reqs.extend([
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 2, "endColumnIndex": 4}, "mergeType": "MERGE_ALL"}},
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 4, "endColumnIndex": 8}, "mergeType": "MERGE_ALL"}},
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 8, "endColumnIndex": 12}, "mergeType": "MERGE_ALL"}},
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 18, "endColumnIndex": 20}, "mergeType": "MERGE_ALL"}},
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 20, "endColumnIndex": 24}, "mergeType": "MERGE_ALL"}},
                {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 24, "endColumnIndex": 28}, "mergeType": "MERGE_ALL"}},
            ])
        else:
            p_qtr = net_payout_pool // 5
            p_final = net_payout_pool - (p_qtr * 3)
            updates.extend([
                {"range": "C13", "values": [["PAYOUTS"]]},
                {"range": "E13", "values": [[f"1ST QTR: ${p_qtr}"]]},
                {"range": "G13", "values": [[f"HALFTIME: ${p_qtr}"]]},
                {"range": "I13", "values": [[f"3RD QTR: ${p_qtr}"]]},
                {"range": "K13", "values": [[f"FINAL: ${p_final}"]]},
                {"range": "S13", "values": [["PAYOUTS"]]},
                {"range": "U13", "values": [[f"1ST QTR: ${p_qtr}"]]},
                {"range": "W13", "values": [[f"HALFTIME: ${p_qtr}"]]},
                {"range": "Y13", "values": [[f"3RD QTR: ${p_qtr}"]]},
                {"range": "AA13", "values": [[f"FINAL: ${p_final}"]]},
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

    grid_reqs, grid_updates = generate_spot_grid_requests(grid_format, new_sheet_id)
    updates.extend(grid_updates)

    new_sheet = sh.get_worksheet_by_id(new_sheet_id)
    if grid_format.startswith("3n1_grid"):
        new_sheet.batch_clear(["Q1:S25"])
    elif grid_format.startswith("2n1_grid"):
        pass
    else:
        new_sheet.batch_clear(["C3:L12", "S3:AB12", "C13:L15", "S13:AB15"])

    away_rgb      = hex_to_rgb(game["away_color"])
    away_text_rgb = get_readable_text_color(game["away_color"], game.get("away_alt_color"))

    home_rgb      = hex_to_rgb(game["home_color"])
    home_text_rgb = get_readable_text_color(game["home_color"], game.get("home_alt_color"))

    yellow_rgb = {"red": 1.0, "green": 1.0, "blue": 0.0}
    black_rgb  = {"red": 0.0, "green": 0.0, "blue": 0.0}
    solid      = {"style": "SOLID", "color": black_rgb}

    payout_end_row = 15 if grid_format.startswith("3n1_grid") else 13

    payout_format_reqs = []
    if not grid_format.startswith("3n1_grid") and not grid_format.startswith("2n1_grid"):
        for col_start, col_end in [(2, 12), (18, 28)]:
            payout_format_reqs.append({
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": payout_end_row, "startColumnIndex": col_start, "endColumnIndex": col_end},
                    "cell": {"userEnteredFormat": {
                        "backgroundColor": yellow_rgb,
                        "textFormat": {"foregroundColor": black_rgb, "bold": True, "fontSize": 10},
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE",
                        "borders": {"top": solid, "bottom": solid, "left": solid, "right": solid}
                    }},
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,borders)"
                }
            })
        for col_idx in [1, 17]:
            payout_format_reqs.append({
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": col_idx, "endColumnIndex": col_idx + 1},
                    "cell": {"userEnteredFormat": {
                        "backgroundColor": hex_to_rgb("00B050"),
                        "textFormat": {"foregroundColor": hex_to_rgb("FFFFFF"), "bold": True, "fontSize": 9},
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE",
                        "borders": {"top": solid, "bottom": solid, "left": solid, "right": solid}
                    }},
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,borders)"
                }
            })

    white_rgb = hex_to_rgb("FFFFFF")

    header_reqs = []
    if not grid_format.startswith('3n1_grid') and not grid_format.startswith('2n1_grid'):
        header_reqs = [
            {"updateDimensionProperties": {"range": {"sheetId": new_sheet_id, "dimension": "ROWS", "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 80}, "fields": "pixelSize"}},
            {"updateDimensionProperties": {"range": {"sheetId": new_sheet_id, "dimension": "ROWS", "startIndex": 1, "endIndex": 2}, "properties": {"pixelSize": 50}, "fields": "pixelSize"}},
            {"updateDimensionProperties": {"range": {"sheetId": new_sheet_id, "dimension": "ROWS", "startIndex": 12, "endIndex": 14}, "properties": {"pixelSize": 35}, "fields": "pixelSize"}},
        ]
    
        header_reqs += [
            {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 4}, "mergeType": "MERGE_ALL"}},
            {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 4, "endColumnIndex": 10}, "mergeType": "MERGE_ALL"}},
            {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 10, "endColumnIndex": 12}, "mergeType": "MERGE_ALL"}},
            {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 2, "endRowIndex": 12, "startColumnIndex": 0, "endColumnIndex": 1}, "mergeType": "MERGE_ALL"}},

            {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 17, "endColumnIndex": 20}, "mergeType": "MERGE_ALL"}},
            {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 20, "endColumnIndex": 26}, "mergeType": "MERGE_ALL"}},
            {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 26, "endColumnIndex": 28}, "mergeType": "MERGE_ALL"}},
            {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 2, "endRowIndex": 12, "startColumnIndex": 16, "endColumnIndex": 17}, "mergeType": "MERGE_ALL"}},
            {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 14, "startColumnIndex": 0, "endColumnIndex": 1}, "mergeType": "MERGE_ALL"}},
            {"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 12, "endRowIndex": 14, "startColumnIndex": 16, "endColumnIndex": 17}, "mergeType": "MERGE_ALL"}},
        ]
    
        header_reqs.extend([
            {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 4},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": away_rgb,
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
                            "backgroundColor": away_rgb,
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
                            "backgroundColor": home_rgb,
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
                            "backgroundColor": home_rgb,
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment)"
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 17, "endColumnIndex": 20},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": away_rgb,
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
                            "backgroundColor": away_rgb,
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
                            "backgroundColor": home_rgb,
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
                            "backgroundColor": home_rgb,
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment)"
                }
            },
        ])
    
        header_reqs.extend([
            {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 4, "endColumnIndex": 10},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": away_rgb,
                            "textFormat": {"foregroundColor": away_text_rgb, "bold": True, "fontSize": 32},
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 20, "endColumnIndex": 26},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": away_rgb,
                            "textFormat": {"foregroundColor": away_text_rgb, "bold": True, "fontSize": 32},
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 2, "endRowIndex": 12, "startColumnIndex": 0, "endColumnIndex": 1},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": home_rgb,
                            "textFormat": {"foregroundColor": home_text_rgb, "bold": True, "fontSize": 28},
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE",
                            "textRotation": {"angle": 90}
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,textRotation)"
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": new_sheet_id, "startRowIndex": 2, "endRowIndex": 12, "startColumnIndex": 16, "endColumnIndex": 17},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": home_rgb,
                            "textFormat": {"foregroundColor": home_text_rgb, "bold": True, "fontSize": 28},
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE",
                            "textRotation": {"angle": 90}
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,textRotation)"
                }
            },
                {
                    "repeatCell": {
                        "range": {"sheetId": new_sheet_id, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 1, "endColumnIndex": 2},
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": away_rgb,
                                "textFormat": {"foregroundColor": away_text_rgb, "bold": True, "fontSize": 12},
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
                                "backgroundColor": away_rgb,
                                "textFormat": {"foregroundColor": away_text_rgb, "bold": True, "fontSize": 12},
                                "horizontalAlignment": "CENTER",
                                "verticalAlignment": "MIDDLE"
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                    }
                },
                {
                    "repeatCell": {
                        "range": {"sheetId": new_sheet_id, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 2, "endColumnIndex": 12},
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": away_rgb,
                                "textFormat": {"foregroundColor": away_text_rgb, "bold": True, "fontSize": 12},
                                "horizontalAlignment": "CENTER",
                                "verticalAlignment": "MIDDLE"
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                    }
                },
                {
                    "repeatCell": {
                        "range": {"sheetId": new_sheet_id, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 18, "endColumnIndex": 28},
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": away_rgb,
                                "textFormat": {"foregroundColor": away_text_rgb, "bold": True, "fontSize": 12},
                                "horizontalAlignment": "CENTER",
                                "verticalAlignment": "MIDDLE"
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                    }
                },
                {
                    "repeatCell": {
                        "range": {"sheetId": new_sheet_id, "startRowIndex": 2, "endRowIndex": 12, "startColumnIndex": 1, "endColumnIndex": 2},
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": home_rgb,
                                "textFormat": {"foregroundColor": home_text_rgb, "bold": True, "fontSize": 12},
                                "horizontalAlignment": "CENTER",
                                "verticalAlignment": "MIDDLE"
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                    }
                },
                {
                    "repeatCell": {
                        "range": {"sheetId": new_sheet_id, "startRowIndex": 2, "endRowIndex": 12, "startColumnIndex": 17, "endColumnIndex": 18},
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": home_rgb,
                                "textFormat": {"foregroundColor": home_text_rgb, "bold": True, "fontSize": 12},
                                "horizontalAlignment": "CENTER",
                                "verticalAlignment": "MIDDLE"
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                    }
                },
            ])
    
    

    body = {
        "requests": grid_reqs + payout_merge_reqs + payout_format_reqs + header_reqs
    }

    sh.batch_update(body)
    new_sheet.batch_update(updates, value_input_option="USER_ENTERED")

    return new_tab_title, new_sheet_id
