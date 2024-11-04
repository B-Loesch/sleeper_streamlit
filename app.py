import streamlit as st
import pandas as pd
import sleeper_app_functions as saf

current_league_id = st.text_input("Please input your league ID:")

league_info = saf.get_all_league_info(current_league_id) # dataframe with league_id, season, playoff_week_start

# st.dataframe(league_info)

all_rosters = pd.DataFrame()

for season_id, year in zip(league_info.league_id, league_info.season):
    year_roster = saf.get_roster_id(season_id, year)

    all_rosters = pd.concat([all_rosters, year_roster])

current_rosters = all_rosters[all_rosters["Season"] == league_info["season"].max()]

# st.dataframe(current_rosters)

all_matchups = pd.DataFrame()

for id, season, playoff_start in zip(league_info.league_id, league_info.season, league_info.playoff_week_start):
    season_matchups = saf.get_matchups_season(id, season, playoff_start, all_rosters)

    all_matchups = pd.concat([all_matchups, season_matchups])

st.dataframe(all_matchups)

display_names = sorted(current_rosters.display_name.tolist())
display_names.insert(0, "Please select a team.")

col1, col2 = st.columns(2)
with col1:
    team1 = st.selectbox("Team 1:", display_names)

with col2:
    display_names_remain = [name for name in display_names if name != team1]
    team2 = st.selectbox("Team 2:", display_names_remain)

exclude_playoffs = st.checkbox("Exclude Playoffs?")

user_pair_view = (team1, team2)

# resetting the index here helps with swapping the values
pair_df = all_matchups[all_matchups["user_pair"] == user_pair_view].reset_index()

if pair_df.shape[0] == 0:
    user_pair_view = (team2, team1)
    pair_df = all_matchups[all_matchups["user_pair"] == user_pair_view].reset_index()

if exclude_playoffs:
    pair_df = pair_df[pair_df["match_type"] == "Regular Season"]

for idx, row in pair_df.iterrows():
    if row['display_name_1'] != team1:
        #swap display name
        pair_df.at[idx, 'display_name_1'] = row['display_name_2']
        pair_df.at[idx, 'display_name_2'] = row['display_name_1']
        # Swap points columns
        pair_df.at[idx, 'points_1'] = row['points_2']
        pair_df.at[idx, 'points_2'] = row['points_1']
        
st.dataframe(pair_df[["season", "week", "match_type", "display_name_1", "points_1", "display_name_2", "points_2", "Winner"]])

team_1_record = f'{pair_df[pair_df["Winner"] == team1].shape[0]}-{pair_df[pair_df["Loser"] == team1].shape[0]}'
team_1_pts = pair_df["points_1"].sum()

team_2_record = f'{pair_df[pair_df["Winner"] == team2].shape[0]}-{pair_df[pair_df["Loser"] == team2].shape[0]}'
team_2_pts = pair_df["points_2"].sum()

team_1_delta = round(team_1_pts - team_2_pts, 2)
team_2_delta = round(team_2_pts - team_1_pts, 2)

team_1_display = f"{team_1_delta} ({round(team_1_pts, 2)})"
team_2_display = f"{team_2_delta} ({round(team_2_pts, 2)})"

col1, col2 = st.columns(2)
col1.metric(team1, team_1_record, team_1_display)
col2.metric(team2, team_2_record, team_2_display)