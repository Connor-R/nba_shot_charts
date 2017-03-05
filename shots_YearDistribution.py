import requests
import urllib
import csv
import os
import sys

sys.path.append('/Users/connordog/Dropbox/Desktop_Files/Work_Things/CodeBase/Python_Scripts/Python_Projects/packages')
sys.path.append('/Users/connordog/Dropbox/Desktop_Files/Work_Things/maxdalury/sports/general')

from py_data_getter import data_getter
from py_db import db

db = db('nba_shots')


def initiate():
    process_players()
    process_teams()
    process_league()

def process_players():
    print '\tplayers'
    query = """SELECT
player_id, season_id, shot_zone_basic, shot_zone_area,
SUM(attempts) as attempts,
SUM(attempts)/all_atts AS zone_pct,
SUM(points)/SUM(attempts)/2 AS efg
FROM shots_Player_Breakdown
JOIN players USING (player_id)
JOIN(
    SELECT player_id, season_id, SUM(attempts) AS all_atts
    FROM shots_Player_Breakdown
    GROUP BY player_id, season_id
) allatts USING (player_id, season_id)
GROUP BY player_id, season_id, shot_zone_basic, shot_zone_area
"""
    res = db.query(query)

    player_entries = []
    for row in res:
        player_id, season_id, shot_zone_basic, shot_zone_area, attempts, zone_pct, efg = row
        entry = {"player_id":player_id, "season_id":season_id, "shot_zone_basic":shot_zone_basic, "shot_zone_area":shot_zone_area, "attempts":attempts, "zone_pct":zone_pct, "efg":efg}   
        player_entries.append(entry)

    if player_entries != []:
        for i in range(0, len(player_entries), 1000):
            db.insertRowDict(player_entries[i: i + 1000], "shots_Player_YearDistribution", insertMany=True, replace=True, rid=0,debug=1)
            db.conn.commit()


def process_teams():
    print '\tteams'
    query = """SELECT
team_id, season_id, shot_zone_basic, shot_zone_area,
SUM(attempts) as attempts,
SUM(attempts)/all_atts AS zone_pct,
SUM(points)/SUM(attempts)/2 AS efg
FROM shots_Team_Breakdown
JOIN teams USING (team_id)
JOIN(
    SELECT team_id, season_id, SUM(attempts) AS all_atts
    FROM shots_Team_Breakdown
    GROUP BY team_id, season_id 
) allatts USING (team_id, season_id)
GROUP BY team_id, season_id, shot_zone_basic, shot_zone_area
"""
    
    res = db.query(query)

    player_entries = []
    for row in res:
        team_id, season_id, shot_zone_basic, shot_zone_area, attempts, zone_pct, efg = row
        entry = {"team_id":team_id, "season_id":season_id, "shot_zone_basic":shot_zone_basic, "shot_zone_area":shot_zone_area, "attempts":attempts, "zone_pct":zone_pct, "efg":efg}   
        player_entries.append(entry)

    if player_entries != []:
        for i in range(0, len(player_entries), 1000):
            db.insertRowDict(player_entries[i: i + 1000], "shots_Team_YearDistribution", insertMany=True, replace=True, rid=0,debug=1)
            db.conn.commit()


def process_league():
    print '\tleague'
    query = """SELECT
'00' AS league_id, season_id, shot_zone_basic, shot_zone_area,
SUM(attempts) as attempts,
SUM(attempts)/all_atts AS zone_pct,
SUM(points)/SUM(attempts)/2 AS efg
FROM shots_League_Breakdown
JOIN(
    SELECT '00' AS league_id, season_id, SUM(attempts) AS all_atts
    FROM shots_League_Breakdown
    GROUP BY league_id, season_id
) allatts USING (league_id, season_id)
GROUP BY league_id, season_id, shot_zone_basic, shot_zone_area
"""
    
    res = db.query(query)

    player_entries = []
    for row in res:
        league_id, season_id, shot_zone_basic, shot_zone_area, attempts, zone_pct, efg = row
        entry = {"league_id":league_id, "season_id":season_id, "shot_zone_basic":shot_zone_basic, "shot_zone_area":shot_zone_area, "attempts":attempts, "zone_pct":zone_pct, "efg":efg}   
        player_entries.append(entry)

    if player_entries != []:
        for i in range(0, len(player_entries), 1000):
            db.insertRowDict(player_entries[i: i + 1000], "shots_League_YearDistribution", insertMany=True, replace=True, rid=0,debug=1)
            db.conn.commit()



if __name__ == "__main__":     
    initiate()



