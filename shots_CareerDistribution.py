import requests
import urllib
import csv
import os
import sys
from time import time


sys.path.append('/Users/connordog/Dropbox/Desktop_Files/Work_Things/CodeBase/Python_Scripts/Python_Projects/packages')
sys.path.append('/Users/connordog/Dropbox/Desktop_Files/Work_Things/maxdalury/sports/general')

from py_data_getter import data_getter
from py_db import db

db = db('nba_shots')


def initiate():
    start_time = time()

    process_players()
    process_teams()
    process_league()

    end_time = time()
    elapsed_time = float(end_time - start_time)
    print "shots_YearDistribution.py"
    print "time elapsed (in seconds): " + str(elapsed_time)
    print "time elapsed (in minutes): " + str(elapsed_time/60.0)


def process_players():
    print '\tplayers'
    query = """SELECT
player_id, CONCAT(GREATEST(1996, from_year),to_year) AS career, shot_zone_basic, shot_zone_area,
SUM(attempts) AS attempts, 
SUM(attempts)/all_atts AS zone_pct,
SUM(points)/SUM(attempts)/2 AS efg
FROM shots_Player_Breakdown
JOIN players USING (player_id)
JOIN(
    SELECT player_id, SUM(attempts) AS all_atts
    FROM shots_Player_Breakdown
    GROUP BY player_id  
) allatts USING (player_id)
GROUP BY player_id, shot_zone_basic, shot_zone_area
"""
    
    res = db.query(query)

    player_entries = []
    for row in res:
        player_id, career, shot_zone_basic, shot_zone_area, attempts, zone_pct, efg = row
        entry = {"player_id":player_id, "season_id":career, "shot_zone_basic":shot_zone_basic, "shot_zone_area":shot_zone_area, "attempts":attempts, "zone_pct":zone_pct, "efg":efg}   
        player_entries.append(entry)

    if player_entries != []:
        for i in range(0, len(player_entries), 1000):
            db.insertRowDict(player_entries[i: i + 1000], "shots_Player_CareerDistribution", insertMany=True, replace=True, rid=0,debug=1)
            db.conn.commit()

def process_teams():
    print '\tteams'
    query = """SELECT
team_id, '1' AS career, shot_zone_basic, shot_zone_area,
SUM(attempts) as attempts,
SUM(attempts)/all_atts AS zone_pct,
SUM(points)/SUM(attempts)/2 AS efg
FROM shots_Team_Breakdown
JOIN teams USING (team_id)
JOIN(
    SELECT team_id, SUM(attempts) AS all_atts
    FROM shots_Team_Breakdown
    GROUP BY team_id  
) allatts USING (team_id)
GROUP BY team_id, shot_zone_basic, shot_zone_area
"""
    
    res = db.query(query)

    player_entries = []
    for row in res:
        team_id, career, shot_zone_basic, shot_zone_area, attempts, zone_pct, efg = row
        entry = {"team_id":team_id, "season_id":career, "shot_zone_basic":shot_zone_basic, "shot_zone_area":shot_zone_area, "attempts":attempts, "zone_pct":zone_pct, "efg":efg}   
        player_entries.append(entry)

    if player_entries != []:
        for i in range(0, len(player_entries), 1000):
            db.insertRowDict(player_entries[i: i + 1000], "shots_Team_CareerDistribution", insertMany=True, replace=True, rid=0,debug=1)
            db.conn.commit()


def process_league():
    print '\tleague'
    query = """SELECT
'00' AS league_id, '1' AS career, shot_zone_basic, shot_zone_area,
SUM(attempts) as attempts,
SUM(attempts)/all_atts AS zone_pct,
SUM(points)/SUM(attempts)/2 AS efg
FROM shots_League_Breakdown
JOIN(
    SELECT '00' AS league_id, SUM(attempts) AS all_atts
    FROM shots_League_Breakdown
    GROUP BY league_id  
) allatts USING (league_id)
GROUP BY league_id, shot_zone_basic, shot_zone_area
"""
    
    res = db.query(query)

    player_entries = []
    for row in res:
        league_id, career, shot_zone_basic, shot_zone_area, attempts, zone_pct, efg = row
        entry = {"league_id":league_id, "season_id":career, "shot_zone_basic":shot_zone_basic, "shot_zone_area":shot_zone_area, "attempts":attempts, "zone_pct":zone_pct, "efg":efg}   
        player_entries.append(entry)

    if player_entries != []:
        for i in range(0, len(player_entries), 1000):
            db.insertRowDict(player_entries[i: i + 1000], "shots_League_CareerDistribution", insertMany=True, replace=True, rid=0,debug=1)
            db.conn.commit()



if __name__ == "__main__":     
    initiate()



    