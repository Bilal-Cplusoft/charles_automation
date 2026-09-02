import re

with open("grid_builder.py", "r") as f:
    text = f.read()

text = re.sub(
    r'def generate_spot_grid_requests\(grid_format, new_sheet_id\):',
    'def generate_spot_grid_requests(grid_format, new_sheet_id):\n    if grid_format.startswith("3n1_grid"):\n        return [], []',
    text
)

with open("grid_builder.py", "w") as f:
    f.write(text)

with open("sheets_client.py", "r") as f:
    text = f.read()

# 1. Update dup_req
dup_code = """
    if grid_format.startswith("3n1_grid"):
        try:
            source_ws = sh.worksheet("3n1")
            source_sheet_id = source_ws.id
        except Exception:
            source_sheet_id = TEMPLATE_SHEET_ID
    else:
        source_sheet_id = TEMPLATE_SHEET_ID

    dup_req = {
        "requests": [
            {
                "duplicateSheet": {
                    "sourceSheetId": source_sheet_id,
"""
# Replace from `dup_req = {` to `"sourceSheetId": TEMPLATE_SHEET_ID,`
text = re.sub(
    r'    dup_req = \{\n        "requests": \[\n            \{\n                "duplicateSheet": \{\n                    "sourceSheetId": TEMPLATE_SHEET_ID,',
    dup_code[1:],
    text
)

# 2. Re-write the entire `if grid_format.startswith("3n1_grid"):` branch.
new_3n1_branch = """    if grid_format.startswith("3n1_grid"):
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

        g1_time = game1.get("game_time", "") if game1 else ""
        g2_time = game2.get("game_time", "") if game2 else ""
        g3_time = game3.get("game_time", "") if game3 else ""

        per_game_pool = net_payout_pool // 3
        share = per_game_pool // 5
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
            
        payout_merge_reqs.extend([
            req_bg(0, 1, 3, 19, g1_a_bg, g1_a_txt),
            req_bg(1, 2, 3, 19, g2_a_bg, g2_a_txt),
            req_bg(2, 3, 3, 19, g3_a_bg, g3_a_txt),
            req_bg(3, 22, 0, 1, g1_h_bg, g1_h_txt),
            req_bg(3, 22, 1, 2, g2_h_bg, g2_h_txt),
            req_bg(3, 22, 2, 3, g3_h_bg, g3_h_txt),
            
            req_bg(3, 4, 19, 35, g1_a_bg, g1_a_txt),
            req_bg(4, 5, 19, 35, g2_a_bg, g2_a_txt),
            req_bg(5, 6, 19, 35, g3_a_bg, g3_a_txt),
            req_bg(6, 22, 19, 20, g1_h_bg, g1_h_txt),
            req_bg(6, 22, 20, 21, g2_h_bg, g2_h_txt),
            req_bg(6, 22, 21, 22, g3_h_bg, g3_h_txt),
        ])
"""
start_idx = text.find('    if grid_format.startswith("3n1_grid"):')
end_idx = text.find('    else:\n        updates = [', start_idx)
text = text[:start_idx] + new_3n1_branch + text[end_idx:]

# 3. Patch the 'clear()' and 'payout_format_reqs' logic
# find new_sheet.clear()
clear_start = text.find('    new_sheet = sh.get_worksheet_by_id(new_sheet_id)\n    new_sheet.clear()')
clear_end = clear_start + len('    new_sheet = sh.get_worksheet_by_id(new_sheet_id)\n    new_sheet.clear()')
clear_replacement = '    new_sheet = sh.get_worksheet_by_id(new_sheet_id)\n    if not grid_format.startswith("3n1_grid"):\n        new_sheet.batch_clear(["C3:L12", "S3:AB12", "C13:L15", "S13:AB15"])'
if clear_start != -1:
    text = text[:clear_start] + clear_replacement + text[clear_end:]


# Next, the payout format logic
pf_start = text.find('    if grid_format.startswith("3n1_grid") and game1 and game2 and game3:\n        game_rows = [')
if pf_start != -1:
    pf_end = text.find('    white_rgb = hex_to_rgb("FFFFFF")')
    if pf_end != -1:
        # Just replace the entire chunk with the 'else' block logic only for not 3n1_grid
        pf_replacement = """    if not grid_format.startswith("3n1_grid"):
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

"""
        text = text[:pf_start] + pf_replacement + text[pf_end:]

# 4. Patch header resizing
hr_start = text.find('    header_reqs = [\n        {"updateDimensionProperties"')
hr_end = text.find('    body = {\n        "requests": grid_reqs')
if hr_start != -1 and hr_end != -1:
    # replace that giant chunk of headers
    # basically, keep it, but put it all under `if not grid_format.startswith("3n1_grid"):`
    old_hr = text[hr_start:hr_end]
    new_hr = "    header_reqs = []\n    if not grid_format.startswith('3n1_grid'):\n" + "\n".join("    " + line for line in old_hr.split("\n")) + "\n\n"
    text = text[:hr_start] + new_hr + text[hr_end:]

with open("sheets_client.py", "w") as f:
    f.write(text)

