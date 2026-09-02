import gspread
from config import hex_to_rgb

def generate_spot_grid_requests(grid_format, new_sheet_id):
    if grid_format.startswith("3n1_grid"):
        return [], []
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

    reqs.append({"unmergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 100, "startColumnIndex": 0, "endColumnIndex": 100}}})
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

    def paint(r1, r2, c1_l, c2_l, c1_r, c2_r, bg, spot_num, txt=None, left_blank=False):
        if (r2 - r1 > 1) or (c2_l - c1_l > 1):
            reqs.append({"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1_l, "endColumnIndex": c2_l}, "mergeType": "MERGE_ALL"}})
            reqs.append({"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1_r, "endColumnIndex": c2_r}, "mergeType": "MERGE_ALL"}})
        reqs.append(fmt(r1, r2, c1_l, c2_l, bg, txt))
        reqs.append(spot_border(r1, r2, c1_l, c2_l))
        reqs.append(fmt(r1, r2, c1_r, c2_r, bg, txt))
        reqs.append(spot_border(r1, r2, c1_r, c2_r))
        left_val = "" if left_blank else str(spot_num)
        updates.append({"range": gspread.utils.rowcol_to_a1(r1 + 1, c1_l + 1), "values": [[left_val]]})
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

    elif grid_format == "3n1_grid":
        spot_idx = 0
        for r_i in range(5):
            for c_i in range(5):
                r1   = 6 + r_i
                c1_l = 3 + c_i
                c1_r = 19 + c_i
                paint(r1, r1 + 1, c1_l, c1_l + 1, c1_r, c1_r + 1, colors[spot_idx % 2], spot_idx + 1, left_blank=True)
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
