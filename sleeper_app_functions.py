import requests
import pandas as pd
import numpy as np
import streamlit as st

def get_league_info(current_id):
    """Returns the league information from the sleeper api.

    Args:
        current_id (string or integer): A string/integer containing the most recent league id.

    Returns:
        dict: The league's current information.
    """

    league_url = f"https://api.sleeper.app/v1/league/{current_id}"
    response = requests.get(league_url)
    if response.status_code == 200:
        data = response.json()
    else:
        print(f"Error: {response.status_code}")

    return(data)

def get_all_league_info(league_id):
    """Generates a list of all league information from the sleeper api, calls the get_league_id function.

    Args:
        league_id (string or integer): A string/integer containing the most recent league id.

    Returns:
        dict: A dictionary containing all previous league info: id, season, playoff_week_start
    """

    while league_id != None:
        league_data = get_league_info(league_id)
        try:
            league_info["league_id"].append(league_id)
            league_info["season"].append(league_data["season"])
            league_info["playoff_week_start"].append(league_data["settings"]["playoff_week_start"])

            league_id = league_data["previous_league_id"]

        except NameError:
            # create league dictionary if it doesn't exist
            league_info = {"league_id": [],
                           "season": [],
                           "playoff_week_start":[]}
            
            

            league_info["league_id"].append(league_id)
            league_info["season"].append(league_data["season"])
            league_info["playoff_week_start"].append(league_data["settings"]["playoff_week_start"])

            league_id = league_data["previous_league_id"]


    
    return(pd.DataFrame(league_info))

def get_matchups(league_id, week_number):
    api_url = f"https://api.sleeper.app/v1/league/{league_id}/matchups/{week_number}"
    # Make the API request
    response = requests.get(api_url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON response
        matchups = response.json()
        return(matchups)
    else:
        print(f"Error: {response.status_code}")

@st.cache_data(persist = "disk")
def get_matchups_season(league_id, season, play_off_week_start, all_rosters):
    users_df = all_rosters[all_rosters["Season"] == str(season)]
    season_matchups = pd.DataFrame()
    for i in range(18):
        week = i+1
        matchups_response = get_matchups(league_id, week_number = week)
        
        if matchups_response != []:
            matchups = {"points": [],
                        "roster_id": [],
                        "matchup_id": []}
            
            for matchup in matchups_response:
                matchups["points"].append(matchup["points"])
                matchups["roster_id"].append(matchup["roster_id"])
                matchups["matchup_id"].append(matchup["matchup_id"])

            
            matchups_df = pd.DataFrame(matchups)
            matchups_df = matchups_df.sort_values(by=['matchup_id', 'points']).reset_index(drop=True)
            matchups_df['pair'] = matchups_df.groupby('matchup_id').cumcount() + 1
            matchups_df = matchups_df.merge(users_df, on = 'roster_id')
            matchups_df = matchups_df[matchups_df["matchup_id"].notnull()] # if it's playoffs, teams that aren't included still return a matchup but shouldn't be kept

            matchups_df_wide = matchups_df.pivot(index='matchup_id', columns='pair', values=['roster_id', 'points', 'display_name', 'user_id'])
            matchups_df_wide.columns = [f"{col[0]}_{col[1]}" for col in matchups_df_wide.columns]
            matchups_df_wide["season"] = season
            matchups_df_wide["week"] = week
            matchups_df_wide["match_type"] = matchups_df_wide['week'].apply(lambda x: 'Regular Season' if x < int(play_off_week_start) else 'Playoffs')

            season_matchups = pd.concat([season_matchups, matchups_df_wide])  

    season_matchups = season_matchups[(season_matchups["points_1"] > 0) & (season_matchups["points_2"] > 0)]
    season_matchups['user_pair'] = season_matchups.apply(lambda row: tuple(sorted([row['display_name_1'], row['display_name_2']])), axis=1)
    season_matchups["Winner"] = season_matchups.apply(lambda row: row['display_name_1'] if row['points_1'] > row['points_2'] else row['display_name_2'], axis=1)
    season_matchups["Loser"] = season_matchups.apply(lambda row: row['display_name_2'] if row['points_1'] > row['points_2'] else row['display_name_1'], axis=1)

    return(season_matchups)

def get_roster_id(league_id, year):
    users_dict = {}
    rosters_dict = {}

    users_url = f"https://api.sleeper.app/v1/league/{league_id}/users"
    rosters_url = f"https://api.sleeper.app/v1/league/{league_id}/rosters"

    # Make the API request
    users_response = requests.get(users_url)
    # Check if the request was successful (status code 200)
    if users_response.status_code == 200:
        # Parse the JSON response
        users = users_response.json()
    else:
        print(f"Error: {users_response.status_code}")

    # Make the API request
    rosters_response = requests.get(rosters_url)
    # Check if the request was successful (status code 200)
    if rosters_response.status_code == 200:
        # Parse the JSON response
        rosters = rosters_response.json()
    else:
        print(f"Error: {rosters_response.status_code}")

    for i, (user, roster) in enumerate(zip(users, rosters)):
        users_dict[i+1] = [user["display_name"], user["user_id"], roster["roster_id"], year]

    users_df = pd.DataFrame.from_dict(users_dict, orient = 'index', columns=['display_name', 'user_id', 'roster_id', "Season"])

    return(users_df)