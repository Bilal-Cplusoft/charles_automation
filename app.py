import streamlit as st
import gspread
import requests
import os
import secrets
import datetime

SPREADSHEET_ID = "1PuKW9cDf9jzSsiSpzMUkJLwhbCtKWe0Y76yt_FGG4vc"

def fetch_espn_game(sport):
    sport_category = "basketball"
    api_sport = sport
    if sport == "mlb":
        sport_category = "baseball"
    elif sport == "nfl":
        sport_category = "football"
    elif sport == "wc":
        sport_category = "soccer"
        api_sport = "fifa.world"

    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_category}/{api_sport}/scoreboard"
    try:
        res = requests.get(url, timeout=5).json()
        events = res.get("events", [])
        if not events:
            return None

        event = events[0]
        competitions = event.get("competitions", [])
        if not competitions:
            return None
        comp = competitions[0]
        competitors = comp.get("competitors", [])
        if len(competitors) < 2:
            return None
        away_team = competitors[1].get("team", {})
        home_team = competitors[0].get("team", {})

        odds_data = comp.get("odds", [])
        ml_odds = odds_data[0].get("details", "") if odds_data else "Odds NA"

        return {
            "away_name": away_team.get("displayName", ""),
            "away_abbrev": away_team.get("abbreviation", ""),
            "away_color": "#" + away_team.get("color", "000000"),
            "away_logo": away_team.get("logo", ""),
            "home_name": home_team.get("displayName", ""),
            "home_abbrev": home_team.get("abbreviation", ""),
            "home_color": "#" + home_team.get("color", "000000"),
            "home_logo": home_team.get("logo", ""),
            "ml_odds": ml_odds
        }
    except Exception:
        return None

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip("#")
    if len(hex_str) != 6:
        return {"red": 0.1, "green": 0.1, "blue": 0.1}
    return {
        "red": int(hex_str[0:2], 16) / 255.0,
        "green": int(hex_str[2:4], 16) / 255.0,
        "blue": int(hex_str[4:6], 16) / 255.0
    }

LEAGUE_LOGOS = {
    "nfl":  "https://a.espncdn.com/i/teamlogos/leagues/500/nfl.png",
    "mlb":  "https://a.espncdn.com/i/teamlogos/leagues/500/mlb.png",
    "nba":  "https://a.espncdn.com/i/teamlogos/leagues/500/nba.png",
    "wnba": "https://a.espncdn.com/i/teamlogos/leagues/500/wnba.png",
    "wc":   "https://a.espncdn.com/i/teamlogos/leagues/500/fifa.png",
}

def generate_spot_grid_requests(grid_format, new_sheet_id):
    reqs = []
    white_rgb = {"red": 1.0, "green": 1.0, "blue": 1.0}
    black_rgb = {"red": 0.0, "green": 0.0, "blue": 0.0}

    reqs.append({
        "unmergeCells": {
            "range": {
                "sheetId": new_sheet_id,
                "startRowIndex": 1,
                "endRowIndex": 13,
                "startColumnIndex": 2,
                "endColumnIndex": 12
            }
        }
    })
    reqs.append({
        "unmergeCells": {
            "range": {
                "sheetId": new_sheet_id,
                "startRowIndex": 1,
                "endRowIndex": 13,
                "startColumnIndex": 18,
                "endColumnIndex": 28
            }
        }
    })

    reqs.append({
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
                        "bold": True,
                        "fontSize": 12
                    },
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "MIDDLE"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
        }
    })
    reqs.append({
        "repeatCell": {
            "range": {
                "sheetId": new_sheet_id,
                "startRowIndex": 2,
                "endRowIndex": 12,
                "startColumnIndex": 18,
                "endColumnIndex": 28
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": white_rgb,
                    "textFormat": {
                        "foregroundColor": black_rgb,
                        "bold": True,
                        "fontSize": 12
                    },
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "MIDDLE"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
        }
    })

    updates = []

    if grid_format == "10_spot":
        for i in range(10):
            r1 = 2 + i
            r2 = r1 + 1
            reqs.append({
                "mergeCells": {
                    "range": {
                        "sheetId": new_sheet_id,
                        "startRowIndex": r1,
                        "endRowIndex": r2,
                        "startColumnIndex": 2,
                        "endColumnIndex": 12
                    },
                    "mergeType": "MERGE_ALL"
                }
            })
            reqs.append({
                "mergeCells": {
                    "range": {
                        "sheetId": new_sheet_id,
                        "startRowIndex": r1,
                        "endRowIndex": r2,
                        "startColumnIndex": 18,
                        "endColumnIndex": 28
                    },
                    "mergeType": "MERGE_ALL"
                }
            })

    elif grid_format == "5_spot":
        for i in range(5):
            r1 = 2 + i * 2
            r2 = r1 + 2
            reqs.append({
                "mergeCells": {
                    "range": {
                        "sheetId": new_sheet_id,
                        "startRowIndex": r1,
                        "endRowIndex": r2,
                        "startColumnIndex": 2,
                        "endColumnIndex": 12
                    },
                    "mergeType": "MERGE_ALL"
                }
            })
            reqs.append({
                "mergeCells": {
                    "range": {
                        "sheetId": new_sheet_id,
                        "startRowIndex": r1,
                        "endRowIndex": r2,
                        "startColumnIndex": 18,
                        "endColumnIndex": 28
                    },
                    "mergeType": "MERGE_ALL"
                }
            })

    elif grid_format == "50_spot":
        for r_i in range(10):
            for c_i in range(5):
                r1 = 2 + r_i
                r2 = r1 + 1
                c1 = 2 + c_i * 2
                c2 = c1 + 2
                reqs.append({
                    "mergeCells": {
                        "range": {
                            "sheetId": new_sheet_id,
                            "startRowIndex": r1,
                            "endRowIndex": r2,
                            "startColumnIndex": c1,
                            "endColumnIndex": c2
                        },
                        "mergeType": "MERGE_ALL"
                    }
                })
                c1_r = 18 + c_i * 2
                c2_r = c1_r + 2
                reqs.append({
                    "mergeCells": {
                        "range": {
                            "sheetId": new_sheet_id,
                            "startRowIndex": r1,
                            "endRowIndex": r2,
                            "startColumnIndex": c1_r,
                            "endColumnIndex": c2_r
                        },
                        "mergeType": "MERGE_ALL"
                    }
                })

    elif grid_format == "25_spot":
        for r_i in range(5):
            for c_i in range(5):
                r1 = 2 + r_i * 2
                r2 = r1 + 2
                c1 = 2 + c_i * 2
                c2 = c1 + 2
                reqs.append({
                    "mergeCells": {
                        "range": {
                            "sheetId": new_sheet_id,
                            "startRowIndex": r1,
                            "endRowIndex": r2,
                            "startColumnIndex": c1,
                            "endColumnIndex": c2
                        },
                        "mergeType": "MERGE_ALL"
                    }
                })
                c1_r = 18 + c_i * 2
                c2_r = c1_r + 2
                reqs.append({
                    "mergeCells": {
                        "range": {
                            "sheetId": new_sheet_id,
                            "startRowIndex": r1,
                            "endRowIndex": r2,
                            "startColumnIndex": c1_r,
                            "endColumnIndex": c2_r
                        },
                        "mergeType": "MERGE_ALL"
                    }
                })

    elif grid_format == "4_spot":
        quads = [(2, 7, 2, 7), (2, 7, 7, 12), (7, 12, 2, 7), (7, 12, 7, 12)]
        quads_right = [(2, 7, 18, 23), (2, 7, 23, 28), (7, 12, 18, 23), (7, 12, 23, 28)]
        for r1, r2, c1, c2 in quads:
            reqs.append({
                "mergeCells": {
                    "range": {
                        "sheetId": new_sheet_id,
                        "startRowIndex": r1,
                        "endRowIndex": r2,
                        "startColumnIndex": c1,
                        "endColumnIndex": c2
                    },
                    "mergeType": "MERGE_ALL"
                }
            })
        for r1, r2, c1, c2 in quads_right:
            reqs.append({
                "mergeCells": {
                    "range": {
                        "sheetId": new_sheet_id,
                        "startRowIndex": r1,
                        "endRowIndex": r2,
                        "startColumnIndex": c1,
                        "endColumnIndex": c2
                    },
                    "mergeType": "MERGE_ALL"
                }
            })

    thin_border = {"style": "SOLID", "color": {"red": 0.0, "green": 0.0, "blue": 0.0}}
    for c1, c2 in [(2, 12), (18, 28)]:
        reqs.append({
            "updateBorders": {
                "range": {
                    "sheetId": new_sheet_id,
                    "startRowIndex": 1,
                    "endRowIndex": 2,
                    "startColumnIndex": c1,
                    "endColumnIndex": c2
                },
                "top": thin_border,
                "bottom": thin_border,
                "left": thin_border,
                "right": thin_border,
                "innerVertical": thin_border
            }
        })

    for c1, c2 in [(2, 12), (18, 28)]:
        reqs.append({
            "updateBorders": {
                "range": {
                    "sheetId": new_sheet_id,
                    "startRowIndex": 2,
                    "endRowIndex": 12,
                    "startColumnIndex": c1,
                    "endColumnIndex": c2
                },
                "top": thin_border,
                "bottom": thin_border,
                "left": thin_border,
                "right": thin_border,
                "innerHorizontal": thin_border,
                "innerVertical": thin_border
            }
        })

    for c1, c2 in [(2, 12), (18, 28)]:
        reqs.append({
            "updateBorders": {
                "range": {
                    "sheetId": new_sheet_id,
                    "startRowIndex": 12,
                    "endRowIndex": 13,
                    "startColumnIndex": c1,
                    "endColumnIndex": c2
                },
                "top": thin_border,
                "bottom": thin_border,
                "left": thin_border,
                "right": thin_border,
                "innerVertical": thin_border
            }
        })

    return reqs, updates

st.set_page_config(page_title="Bet Creation Dashboard", layout="centered")
st.title("Automated Bet Creation")

with st.form("bet_form"):
    st.markdown("### Square Board Logic Algorithms")
    sport = st.selectbox("Sport Type", ["nfl", "mlb", "nba", "wnba", "wc"])
    grid_format = st.selectbox("Grid Size (Spots)", ["100_spot", "bankrupt_spot", "50_spot", "25_spot", "10_spot", "5_spot", "4_spot"])
    winners = st.number_input("Number of Winners", min_value=1, value=4)
    cost = st.number_input("Cost Per Square ($)", min_value=1, value=55)
    submit = st.form_submit_button("Create Bet")

if submit:
    with st.spinner("Generating board..."):
        cred_file = os.getenv("GCP_KEY")
        if not cred_file or not os.path.exists(cred_file):
            fallback_key = os.path.join(os.path.dirname(__file__), "cosmic-heaven-506712-e4-e652026d0682.json")
            if os.path.exists(fallback_key):
                cred_file = fallback_key
            else:
                st.error("Missing GCP_KEY environment variable or credential file.")
                st.stop()

        game = fetch_espn_game(sport)
        if not game:
            st.error(f"No active {sport.upper()} games found via ESPN API.")
            st.stop()

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

        crypto_rng = secrets.SystemRandom()
        top_numbers = list(range(10))
        crypto_rng.shuffle(top_numbers)
        left_numbers = list(range(10))
        crypto_rng.shuffle(left_numbers)

        if grid_format == "bankrupt_spot":
            grid_spots = 25
        else:
            try:
                grid_spots = int(grid_format.split('_')[0])
            except Exception:
                grid_spots = 100

        total_pot   = grid_spots * cost
        payout_q1   = int(total_pot * 0.175)
        payout_half = int(total_pot * 0.45455)
        payout_final = int(total_pot * 0.45455)
        payout_rev  = int(total_pot * 0.05)

        league_logo = LEAGUE_LOGOS.get(sport, "")
        updates = [
            {"range": "A1", "values": [[f'=IMAGE("{league_logo}")']]},
            {"range": "C1", "values": [[f'=IMAGE("{game.get("away_logo", "")}")']]},
            {"range": "E1", "values": [[game.get("away_name", "")]]},
            {"range": "K1", "values": [[""]]},
            {"range": "A2", "values": [[f'=IMAGE("{game.get("home_logo", "")}")']]},
            {"range": "A5", "values": [[game.get("home_name", "")]]},
            {"range": "A11", "values": [[""]]},
            {"range": "B2", "values": [[f"${cost}"]]},
            {"range": "C2:L2", "values": [[str(n) for n in top_numbers]]},
            {"range": "B3:B12", "values": [[str(n)] for n in left_numbers]},
        ]

        payout_merge_reqs = []

        if sport == "mlb":
            if grid_format in ["4_spot", "5_spot", "10_spot"]:
                mlb_5inn = payout_half
                mlb_final = payout_final
            else:
                mlb_5inn = int(total_pot * 0.20)
                mlb_final = int(total_pot * 0.40)

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
        elif grid_format in ["4_spot", "5_spot", "10_spot"] or sport in ["nba", "wnba"]:
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
            updates.extend([
                {"range": "C13", "values": [["PAYOUTS"]]},
                {"range": "E13", "values": [[f"Q1 ${payout_q1}"]]},
                {"range": "G13", "values": [[f"HT ${payout_q1}"]]},
                {"range": "I13", "values": [[f"Q3 ${payout_q1}"]]},
                {"range": "K13", "values": [[f"FINAL ${int(total_pot * 0.40)}"]]},
                {"range": "E14", "values": [[f"Rev ${payout_rev}"]]},
                {"range": "G14", "values": [[f"Rev ${payout_rev}"]]},
                {"range": "I14", "values": [[f"Rev ${payout_rev}"]]},
                {"range": "K14", "values": [[f"Rev ${int(payout_rev * 1.5)}"]]},
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

        away_rgb  = hex_to_rgb(game["away_color"])
        home_rgb  = hex_to_rgb(game["home_color"])
        white_rgb = {"red": 1.0, "green": 1.0, "blue": 1.0}
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

        header_reqs = [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": new_sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1,
                        "startColumnIndex": 1,
                        "endColumnIndex": 12
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
                        "startRowIndex": 1,
                        "endRowIndex": 2,
                        "startColumnIndex": 2,
                        "endColumnIndex": 12
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
                        "startRowIndex": 1,
                        "endRowIndex": 12,
                        "startColumnIndex": 0,
                        "endColumnIndex": 1
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
                        "startColumnIndex": 1,
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
            }
        ]

        body = {
            "requests": payout_merge_reqs + grid_reqs + payout_format_reqs + header_reqs
        }
        sh.batch_update(body)

        new_sheet.batch_update(updates, value_input_option="USER_ENTERED")

        st.success(f"Successfully generated: {new_tab_title}")
        st.markdown(f"**[Click here to view your Google Sheet](https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit)**")
