import requests
import urllib
import csv
import os
import sys
from time import time, sleep
from datetime import date, datetime
import argparse
import json as jsnn

from py_data_getter import data_getter
from py_db import db

db = db('nba_shots')

start_time = time()

getter = data_getter()

type_dict = {'Pre':'Pre Season','Post':'Playoffs', 'AS':'All Star', 'Reg':'Regular Season'}

base_url = "https://stats.nba.com/stats/shotchartdetail"

print "-------------------------"
print "scraper_shots.py"

def initiate(start_year, end_year, lastNgames, short_type):

    season_type = type_dict.get(short_type)

    for year in range(start_year,end_year+1):
        print year, short_type, type(short_type), season_type
        season_start = year

        # takes a season (e.g. 2008) and returns the nba ID (e.g. 2008-09)
        season_id = str(season_start)+'-'+str(season_start%100+1).zfill(2)[-2:]

        db_season_id = str(season_start)+str(season_start%100+1).zfill(2)[-2:]

        season_url = base_url
        parameters = {
            'ContextMeasure': 'FGA',
            'LastNGames': lastNgames,
            'LeagueID': '00',
            'Month': 0,
            'OpponentTeamID': 0,
            'Period': 0,
            'PlayerID': 0,
            'SeasonType': season_type,
            'TeamID': 0,
            'VsDivision': '',
            'VsConference': '',
            'SeasonSegment': '',
            'Season': season_id,
            'RookieYear': '',
            'PlayerPosition': '',
            'Outcome': '',
            'Location': '',
            'GameSegment': '',
            'GameId': '',
            'DateTo': '',
            'DateFrom': ''
        }
        # print season_url


        json = getter.get_url_data(season_url, "json", nba=True, params=parameters)
        if json is None:
            sys.exit('\n\n\nNo data acquired')
        else:
            print "acquired data"

        sleep(5)
        resultSets = json["resultSets"]

        shots = resultSets[0]["rowSet"]

        shot_entries = []

        for shot in shots:
            # print shot
            entry = {}
            entry["season_id"] = db_season_id
            entry["game_id"] = shot[1]
            entry["game_event_id"] = shot[2]
            entry["player_id"] = shot[3]
            entry["team_id"] = shot[5]
            entry["period"] = shot[7]
            entry["minutes_remaining"] = shot[8]
            entry["seconds_remaining"] = shot[9]
            entry["event_type"] = shot[10]
            entry["action_type"] = shot[11]
            entry["shot_type"] = shot[12]
            if shot[13] in ('Left Corner 3', 'Right Corner 3'):
                entry["shot_zone_basic"] = 'Corner 3'
            else:
                entry["shot_zone_basic"] = shot[13]
            entry["shot_zone_area"] = shot[14]
            entry["shot_zone_range"] = shot[15]
            entry["shot_distance"] = shot[16]
            entry["LOC_X"] = shot[17]
            entry["LOC_Y"] = shot[18]

            text_date = str(shot[21])
            year = int(text_date[:4]) 
            month = int(text_date[4:6])
            day = int(text_date[6:])
            _date = date(year, month, day)
            entry["game_date"] = _date

            entry["home_team"] = shot[22]
            entry["away_team"] = shot[23]
            entry["season_type"] = short_type

            shot_entries.append(entry)


        if shot_entries != []:
            for i in range(0, len(shot_entries), 1000):
                db.insertRowDict(shot_entries[i: i + 1000], "shots", insertMany=True, replace=True, rid=0,debug=1)
                db.conn.commit()

    end_time = time()
    elapsed_time = float(end_time - start_time)
    print "time elapsed (in seconds): " + str(elapsed_time)
    print "time elapsed (in minutes): " + str(elapsed_time/60.0)
    print "scraper_shots.py"
    print "-------------------------"


if __name__ == "__main__":     
    parser = argparse.ArgumentParser()
    parser.add_argument('--start_year',type=int,default=2018)
    parser.add_argument('--end_year',type=int,default=2018)
    parser.add_argument('--lastNgames',type=int,default=1)
    parser.add_argument('--short_type',type=str,default='Reg')


    args = parser.parse_args()
    
    initiate(args.start_year, args.end_year, args.lastNgames, args.short_type)
