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

    for year in range(2016,2017):
        season_start = year
        season_id = str(season_start)+str(season_start%100+1).zfill(2)[-2:]
        print season_id
        
        process_players(season_id)
        process_teams(season_id)
        process_league(season_id)

    end_time = time()
    elapsed_time = float(end_time - start_time)
    print "shots_Breakdown.py"
    print "time elapsed (in seconds): " + str(elapsed_time)
    print "time elapsed (in minutes): " + str(elapsed_time/60.0)

def process_players(season_id):
    print '\tplayers'
    query = """SELECT player_id, season_id, shot_zone_basic, shot_zone_area,
COUNT(*) AS attempts,
SUM(CASE WHEN event_type = "Made Shot" THEN 1 ELSE 0 END) AS makes,
SUM(CASE WHEN event_type = "Made Shot" AND shot_type = '2PT Field Goal' THEN 2 
    WHEN event_type = "Made Shot" AND shot_type = '3PT Field Goal' THEN 3
    ELSE 0 END) AS points
FROM shots
WHERE season_id = %s
GROUP BY player_id, season_id, shot_zone_basic, shot_zone_area
"""
    
    res = db.query(query % (season_id))

    player_entries = []
    for row in res:
        player_id, season_id, shot_zone_basic, shot_zone_area, attempts, makes, points = row
        entry = {"player_id":player_id, "season_id":season_id, "shot_zone_basic":shot_zone_basic, "shot_zone_area":shot_zone_area, "attempts":attempts, "makes":makes, "points":points}   
        player_entries.append(entry)

    if player_entries != []:
        for i in range(0, len(player_entries), 1000):
            db.insertRowDict(player_entries[i: i + 1000], "shots_Player_Breakdown", insertMany=True, replace=True, rid=0,debug=1)
            db.conn.commit()

def process_teams(season_id):
    print '\tteams'
    query = """SELECT team_id, season_id, shot_zone_basic, shot_zone_area,
COUNT(*) AS attempts,
SUM(CASE WHEN event_type = "Made Shot" THEN 1 ELSE 0 END) AS makes,
SUM(CASE WHEN event_type = "Made Shot" AND shot_type = '2PT Field Goal' THEN 2 
    WHEN event_type = "Made Shot" AND shot_type = '3PT Field Goal' THEN 3
    ELSE 0 END) AS points
FROM shots
WHERE season_id = %s
GROUP BY team_id, season_id, shot_zone_basic, shot_zone_area
"""
    
    res = db.query(query % (season_id))

    team_entries = []
    for row in res:
        team_id, season_id, shot_zone_basic, shot_zone_area, attempts, makes, points = row
        entry = {"team_id":team_id, "season_id":season_id, "shot_zone_basic":shot_zone_basic, "shot_zone_area":shot_zone_area, "attempts":attempts, "makes":makes, "points":points}   
        team_entries.append(entry)

    if team_entries != []:
        for i in range(0, len(team_entries), 1000):
            db.insertRowDict(team_entries[i: i + 1000], "shots_Team_Breakdown", insertMany=True, replace=True, rid=0,debug=1)
            db.conn.commit()

def process_league(season_id):
    print '\tleague'
    query = """SELECT 00 as league_id, season_id, shot_zone_basic, shot_zone_area,
COUNT(*) AS attempts,
SUM(CASE WHEN event_type = "Made Shot" THEN 1 ELSE 0 END) AS makes,
SUM(CASE WHEN event_type = "Made Shot" AND shot_type = '2PT Field Goal' THEN 2 
    WHEN event_type = "Made Shot" AND shot_type = '3PT Field Goal' THEN 3
    ELSE 0 END) AS points
FROM shots
WHERE season_id = %s
GROUP BY season_id, shot_zone_basic, shot_zone_area
"""
    
    res = db.query(query % (season_id))

    league_entries = []
    for row in res:
        league_id, season_id, shot_zone_basic, shot_zone_area, attempts, makes, points = row
        entry = {"league_id":league_id, "season_id":season_id, "shot_zone_basic":shot_zone_basic, "shot_zone_area":shot_zone_area, "attempts":attempts, "makes":makes, "points":points}   
        league_entries.append(entry)

    if league_entries != []:
        for i in range(0, len(league_entries), 1000):
            db.insertRowDict(league_entries[i: i + 1000], "shots_League_Breakdown", insertMany=True, replace=True, rid=0,debug=1)
            db.conn.commit()


if __name__ == "__main__":     
    initiate()



