import streamlit as st
import gspread
import requests
import os

SPREADSHEET_ID = "1PuKW9cDf9jzSsiSpzMUkJLwhbCtKWe0Y76yt_FGG4vc"

def fetch_espn_game(sport):
    sport_category = "basketball"
    if sport == "mlb": sport_category = "baseball"
    elif sport == "nfl": sport_category = "football"
    
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_category}/{sport}/scoreboard"
    try:
        res = requests.get(url, timeout=5).json()
        events = res.get("events", [])
        if not events: return None
        
        event = events[0]
        comp = event["competitions"][0]
        competitors = comp["competitors"]
        away_team = competitors[1]["team"]
        home_team = competitors[0]["team"]
        
        return {
            "away_name": away_team.get("displayName", ""),
            "away_abbrev": away_team.get("abbreviation", ""),
            "away_color": "#" + away_team.get("color", "000000"),
            "away_logo": away_team.get("logo", ""),
            "home_name": home_team.get("displayName", ""),
            "home_abbrev": home_team.get("abbreviation", ""),
            "home_color": "#" + home_team.get("color", "000000"),
            "home_logo": home_team.get("logo", "")
        }
    except Exception:
        return None

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip("#")
    if len(hex_str) != 6: return {"red": 0.1, "green": 0.1, "blue": 0.1}
    return {
        "red": int(hex_str[0:2], 16) / 255.0,
        "green": int(hex_str[2:4], 16) / 255.0,
        "blue": int(hex_str[4:6], 16) / 255.0
    }

st.set_page_config(page_title="Bet Creation Dashboard", layout="centered")
st.title("Automated Bet Creation")

with st.form("bet_form"):
    sport = st.selectbox("Sport Type", ["nfl", "mlb", "nba", "wnba"])
    grid_format = st.selectbox("Grid Size", ["100_spot", "25_spot"])
    winners = st.number_input("Number of Winners", min_value=1, value=4)
    cost = st.number_input("Cost Per Square ($)", min_value=1, value=55)
    submit = st.form_submit_button("Create Bet")

if submit:
    with st.spinner("Generating board..."):
        cred_file = os.getenv("GCP_KEY")
        if not cred_file or not os.path.exists(cred_file):
            st.error("Missing GCP_KEY environment variable or credential file.")
            st.stop()
            
        game = fetch_espn_game(sport)
        if not game:
            st.error(f"No active {sport.upper()} games found via ESPN API.")
            st.stop()
            
        gc = gspread.service_account(filename=cred_file)
        sh = gc.open_by_key(SPREADSHEET_ID)

        template_id = 1594614647 if grid_format == "100_spot" else None
        if not template_id:
            st.error("Template ID for this grid size is not configured.")
            st.stop()

        target_index = 7
        new_tab_title = f"8/26/26 ${cost} {sport.upper()} {game['away_abbrev'].lower()}/{game['home_abbrev'].lower()}"

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
        
        blank_grid = [["" for _ in range(10)] for _ in range(10)]
        blank_side = [["" for _ in range(5)] for _ in range(10)]
        
        updates = [
            {"range": "C1", "values": [[f'=IMAGE("{game["away_logo"]}")']]}, 
            {"range": "E1", "values": [[game["away_name"]]]},             
            {"range": "A3", "values": [[f'=IMAGE("{game["home_logo"]}")']]}, 
            {"range": "A5", "values": [[game["home_name"]]]},             
            {"range": "B2", "values": [[f"${cost}"]]},       
            {"range": "C3:L12", "values": blank_grid},                 
            {"range": "Q3:U12", "values": blank_side},               
        ]
        
        new_sheet = sh.get_worksheet_by_id(new_sheet_id)
        new_sheet.batch_update(updates, value_input_option="USER_ENTERED")

        away_rgb = hex_to_rgb(game["away_color"])
        home_rgb = hex_to_rgb(game["home_color"])
        white_rgb = {"red": 1.0, "green": 1.0, "blue": 1.0}
        black_rgb = {"red": 0.0, "green": 0.0, "blue": 0.0}
        
        body = {
            "requests": [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": new_sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                            "startColumnIndex": 2,
                            "endColumnIndex": 10
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": away_rgb,
                                "textFormat": {
                                    "foregroundColor": white_rgb,
                                    "bold": True,
                                    "fontSize": 16
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
                            "startRowIndex": 4,
                            "endRowIndex": 12,
                            "startColumnIndex": 0,
                            "endColumnIndex": 2
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": home_rgb,
                                "textFormat": {
                                    "foregroundColor": white_rgb,
                                    "bold": True,
                                    "fontSize": 16
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
                            "startRowIndex": 2,
                            "endRowIndex": 12,
                            "startColumnIndex": 2,
                            "endColumnIndex": 12
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": white_rgb,
                                "textFormat": {
                                    "foregroundColor": black_rgb,
                                    "bold": False,
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
        }
        sh.batch_update(body)

        st.success(f"Successfully generated: {new_tab_title}")
        st.markdown(f"**[Click here to view your Google Sheet](https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit)**")
