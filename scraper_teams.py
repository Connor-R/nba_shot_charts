import requests
import urllib
import csv
import os
import sys
from time import time


sys.path.append('/Users/connordog/Dropbox/Desktop_Files/Work_Things/CodeBase/Python_Scripts/Python_Projects/packages')

from py_data_getter import data_getter
from py_db import db

db = db('nba_shots')

start_time = time()

getter = data_getter()

team_url = 'http://stats.nba.com/stats/franchisehistory?LeagueID=00'

json = getter.get_url_data(team_url, "json")

resultSets = json["resultSets"]

teams = resultSets[0]["rowSet"]

teams_entries = []

for team in teams:
    entry = {}
    entry["team_id"] = team[1]
    entry["city"] = team[2]
    entry["name"] = team[3]
    entry["start_year"] = team[4]
    entry["end_year"] = int(team[5])+1

    teams_entries.append(entry)


if teams_entries != []:
    for i in range(0, len(teams_entries), 1000):
        db.insertRowDict(teams_entries[i: i + 1000], "teams", insertMany=True, replace=True, rid=0,debug=1)
        db.conn.commit()


end_time = time()
elapsed_time = float(end_time - start_time)
print "scraper_teams.py"
print "time elapsed (in seconds): " + str(elapsed_time)
print "time elapsed (in minutes): " + str(elapsed_time/60.0)

