import streamlit as st
from config import SPREADSHEET_ID, SPORT_CHOICES, GRID_FORMAT_CHOICES
from espn_api import fetch_espn_games
from sheets_client import get_gspread_client, create_game_tab

st.set_page_config(page_title="Automated Bet Creation", layout="centered")
st.title("Automated Bet Creation")

st.markdown("### Square Board Options")
grid_format = st.selectbox(
    "Grid Size (Spots)",
    list(GRID_FORMAT_CHOICES.keys()),
    format_func=lambda x: "3n1 Grid" if x == "3n1_grid" else ("2n1 Grid" if x == "2n1_grid" else x)
)

if grid_format == "3n1_grid":
    winners = 12
    st.info("3n1 Grid automatically configures 12 winners across 3 selected games (4 quarter winners per game).")
elif grid_format == "2n1_grid":
    winners = 8
    st.info("2n1 Grid automatically configures 8 winners across 2 selected games (4 quarter winners per game).")
else:
    winners = st.number_input("Number of Winners", min_value=1, value=4)

cost = st.number_input("Cost Per Square ($)", min_value=1, value=36)
rake_pct = st.number_input(
    "House Rake (%)",
    min_value=0.0,
    max_value=50.0,
    value=13.33,
    step=0.5,
    help="Percentage of total pot kept by house (default 13.33%)"
)

col_sport, col_ref = st.columns([4, 1])
with col_sport:
    sport_label = st.selectbox("Sport Type", list(SPORT_CHOICES.keys()))
with col_ref:
    st.write("")
    st.write("")
    if st.button("Refresh"):
        st.cache_data.clear()
        st.rerun()

sport = SPORT_CHOICES[sport_label]

fetched_games = fetch_espn_games(sport)
selected_game = None
game1, game2, game3 = None, None, None

if grid_format == "3n1_grid":
    if fetched_games:
        game_labels = [g["label"] for g in fetched_games]
        g1_label = st.selectbox("Game 1", game_labels, index=0, key="g1_select")
        game1 = next((g for g in fetched_games if g["label"] == g1_label), fetched_games[0])

        g2_label = st.selectbox("Game 2", game_labels, index=min(1, len(game_labels) - 1), key="g2_select")
        game2 = next((g for g in fetched_games if g["label"] == g2_label), fetched_games[1] if len(fetched_games) > 1 else fetched_games[0])

        g3_label = st.selectbox("Game 3", game_labels, index=min(2, len(game_labels) - 1), key="g3_select")
        game3 = next((g for g in fetched_games if g["label"] == g3_label), fetched_games[2] if len(fetched_games) > 2 else fetched_games[0])
        selected_game = game1
    else:
        st.warning(f"No games found for {sport_label} via ESPN API.")
elif grid_format == "2n1_grid":
    if fetched_games:
        game_labels = [g["label"] for g in fetched_games]
        g1_label = st.selectbox("Game 1", game_labels, index=0, key="g1_select")
        game1 = next((g for g in fetched_games if g["label"] == g1_label), fetched_games[0])

        g2_label = st.selectbox("Game 2", game_labels, index=min(1, len(game_labels) - 1), key="g2_select")
        game2 = next((g for g in fetched_games if g["label"] == g2_label), fetched_games[1] if len(fetched_games) > 1 else fetched_games[0])
        selected_game = game1
    else:
        st.warning(f"No games found for {sport_label} via ESPN API.")
else:
    if fetched_games:
        selected_game_label = st.selectbox(
            "Select Game",
            options=[g["label"] for g in fetched_games],
            help="Select any available game for this sport."
        )
        selected_game = next((g for g in fetched_games if g["label"] == selected_game_label), fetched_games[0])
    else:
        st.warning(f"No games found for {sport_label} via ESPN API.")

submit = st.button("Create Bet")

if submit:
    if not selected_game:
        st.error("No game selected. Please select a valid game to proceed.")
        st.stop()

    with st.spinner("Connecting to Google Sheets & generating board..."):
        try:
            gc = get_gspread_client()
            sh = gc.open_by_key(SPREADSHEET_ID)

            new_tab_title = create_game_tab(
                sh=sh,
                grid_format=grid_format,
                winners=winners,
                cost=cost,
                rake_pct=rake_pct,
                sport=sport,
                game=selected_game,
                game1=game1,
                game2=game2,
                game3=game3
            )

            st.success(f"Successfully generated: {new_tab_title}")
            st.markdown(f"**[Click here to view your Google Sheet](https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit)**")
        except Exception as e:
            st.error(f"Error generating board: {e}")