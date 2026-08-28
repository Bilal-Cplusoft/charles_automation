import sys, os
sys.path.insert(0, "/app")
import gspread, json

cred_file = "/app/cosmic-heaven-506712-e4-e652026d0682.json"
gc = gspread.service_account(filename=cred_file)
sh = gc.open_by_key("1PuKW9cDf9jzSsiSpzMUkJLwhbCtKWe0Y76yt_FGG4vc")

sheet_name = "Test_4_Spot_Correct"
try:
    sh.del_worksheet(sh.worksheet(sheet_name))
except Exception:
    pass

dup_req = {
    "requests": [
        {
            "duplicateSheet": {
                "sourceSheetId": 1594614647,
                "insertSheetIndex": 0,
                "newSheetName": sheet_name
            }
        }
    ]
}
res = sh.batch_update(dup_req)
new_sheet_id = res["replies"][0]["duplicateSheet"]["properties"]["sheetId"]

white_rgb = {"red": 1.0, "green": 1.0, "blue": 1.0}
black_rgb = {"red": 0.0, "green": 0.0, "blue": 0.0}
thin_border = {"style": "SOLID", "color": {"red": 0.0, "green": 0.0, "blue": 0.0}}

reqs = [
    {"unmergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 2, "endRowIndex": 12, "startColumnIndex": 2, "endColumnIndex": 12}}},
    {"unmergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": 2, "endRowIndex": 12, "startColumnIndex": 18, "endColumnIndex": 28}}},
]

for c1, c2 in [(2, 12), (18, 28)]:
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": new_sheet_id, "startRowIndex": 2, "endRowIndex": 12, "startColumnIndex": c1, "endColumnIndex": c2},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": white_rgb,
                    "textFormat": {"foregroundColor": black_rgb, "bold": True, "fontSize": 12},
                    "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
        }
    })

# 4_spot merge
quads = [(2, 7, 2, 7), (2, 7, 7, 12), (7, 12, 2, 7), (7, 12, 7, 12)]
quads_right = [(2, 7, 18, 23), (2, 7, 23, 28), (7, 12, 18, 23), (7, 12, 23, 28)]
for r1, r2, c1, c2 in quads + quads_right:
    reqs.append({"mergeCells": {"range": {"sheetId": new_sheet_id, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}, "mergeType": "MERGE_ALL"}})

for c1, c2 in [(2, 12), (18, 28)]:
    reqs.append({
        "updateBorders": {
            "range": {"sheetId": new_sheet_id, "startRowIndex": 2, "endRowIndex": 12, "startColumnIndex": c1, "endColumnIndex": c2},
            "top": thin_border, "bottom": thin_border, "left": thin_border, "right": thin_border,
            "innerHorizontal": thin_border, "innerVertical": thin_border
        }
    })

sh.batch_update({"requests": reqs})

# Fetch merges count
sheet_data = sh.client.request(
    "get",
    f"https://sheets.googleapis.com/v4/spreadsheets/{sh.id}?includeGridData=false&ranges='{sheet_name}'"
).json()

merges = sheet_data["sheets"][0].get("merges", [])
grid_merges = [m for m in merges if m["startRowIndex"] >= 2 and m["endRowIndex"] <= 12 and m["startColumnIndex"] >= 2 and m["endColumnIndex"] <= 12]
print("4_spot left grid merges count (should be 4):", len(grid_merges))
for m in grid_merges:
    print(" ", m)

sh.del_worksheet(sh.worksheet(sheet_name))
