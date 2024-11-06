import streamlit as st
import pandas as pd
import sleeper_app_functions as saf

st.set_page_config(page_title=None, 
                   page_icon=None, 
                   layout="wide", 
                   initial_sidebar_state="auto", 
                   menu_items=None)

# current_league_id = st.text_input("Please input your league ID:")
current_league_id = 1073659471932538880

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
    season_matchups = saf.get_matchups_season(id, season, playoff_start, all_rosters) # I think we're dropping some rows here!
    all_matchups = pd.concat([all_matchups, season_matchups]) 

exclude_playoffs = st.checkbox("Exclude Playoffs/Toilet Bowl?")

users = sorted(current_rosters.display_name.tolist(), key = str.lower)
users.insert(0, "None")

# st.dataframe(all_matchups)

display_names = sorted(current_rosters.display_name.tolist(), key = str.lower)
display_names.insert(0, "Please select a team.")



col1, col2 = st.columns(2)
with col1:
    team1 = st.selectbox("Team 1:", display_names)
    # try:
    #     team1_image = current_rosters[current_rosters["display_name"] == team1].at[0, "image_link"]
    #     st.image(team1_image)
    # except:
    #     print("Error getting image")

with col2:
    display_names_remain = [name for name in display_names if name != team1 if name != "Please select a team."]
    display_names_remain.insert(0, "Please select another team.")

    team2 = st.selectbox("Team 2:", display_names_remain)

    # team2_image = current_rosters[current_rosters["display_name"] == team2].at[0, "image_link"]
    # st.image(team2_image)

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

st.dataframe(pair_df[["season", "week", "match_type", "display_name_1", "points_1", "display_name_2", "points_2", "Winner"]], use_container_width=True)

emoji_dict = {-20: ":face_vomiting:",
              -10: ":thumbsdown:",
              0: ":scales:",
              10: ":ok_hand:",
              20: ":fire:"}

def get_emoji(diff):
    if diff <= -15:
        return emoji_dict[-20]
    elif -15 < diff <= -5:
        return emoji_dict[-10]
    elif -5 < diff <= 5:
        return emoji_dict[0]
    elif 5 < diff <= 15:
        return emoji_dict[10]
    elif diff > 15:
        return emoji_dict[20]

if team1 in sorted(current_rosters.display_name.tolist(), key = str.lower):
    if team2 in sorted(current_rosters.display_name.tolist(), key = str.lower):
        matchup_ppg = pair_df["points_1"].mean()
        total_points = all_matchups[all_matchups['display_name_1'] == team1]['points_1'].sum() + all_matchups[all_matchups['display_name_2'] == team1]['points_2'].sum()
        total_games = all_matchups[all_matchups['display_name_1'] == team1]['points_1'].shape[0] + all_matchups[all_matchups['display_name_2'] == team1]['points_2'].shape[0]
        ppg = total_points / total_games
        diff = matchup_ppg - ppg

        emoji = get_emoji(diff)

        if matchup_ppg < ppg:
            word_use = "underperforming"
            diff *= -1
        else:
            word_use = "overperforming"
        
        st.caption(f'{team1} scores {round(matchup_ppg, 2)} points per game when facing {team2}. Against the league, {team1} averages {round(ppg, 2)} points per game, {word_use} by {round(diff, 2)} points. {emoji}')

        matchup_ppg = pair_df["points_2"].mean()
        total_points = all_matchups[all_matchups['display_name_1'] == team2]['points_1'].sum() + all_matchups[all_matchups['display_name_2'] == team2]['points_2'].sum()
        total_games = all_matchups[all_matchups['display_name_1'] == team2]['points_1'].shape[0] + all_matchups[all_matchups['display_name_2'] == team2]['points_2'].shape[0]
        ppg = total_points / total_games
        diff = matchup_ppg - ppg

        emoji = get_emoji(diff)

        if matchup_ppg < ppg:
            word_use = "underperforming"
            diff *= -1
        else:
            word_use = "overperforming"

        st.caption(f'{team2} scores {round(matchup_ppg, 2)} points per game when facing {team1}. Against the league, {team2} averages {round(ppg, 2)} points per game, {word_use} by {round(diff, 2)} points. {emoji}')


# highlight_user = st.selectbox("Select a team to highlight:", users)

head_to_head_matrix = saf.generate_matrix(all_matchups, current_rosters, exclude_playoffs)

st.header("League Head-to-Head Records", divider = True)

st.dataframe(head_to_head_matrix.style.apply(
    lambda row: ['background-color: blue' if row.name == team1 else '' for _ in row], axis=1
    ).apply(
        lambda col: ['background-color: blue' if col.name == team2 else '' for _ in col], axis = 0
    ), 
    use_container_width=True)
