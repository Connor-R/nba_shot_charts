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

url = 'http://stats.nba.com/stats/commonallplayers?IsOnlyCurrentSeason=0&LeagueID=00&Season=2016-17'

print "scraper_players.py"
print "-------------------------"

json = getter.get_url_data(url, "json")

resultSets = json["resultSets"]

players = resultSets[0]["rowSet"]

player_entries = []
for dbplayer in players:
    entry = {}
    entry["player_id"] = dbplayer[0]
    if dbplayer[1] == "Nene":
        entry["lname"] = "Hilario"
        entry["fname"] = "Nene"
    elif dbplayer[1] == "Yao Ming":
        entry["lname"] = "Ming"
        entry["fname"] = "Yao"
    elif dbplayer[1] == "Yi Jianlian":
        entry["lname"] = "Jianlian"
        entry["fname"] = "Yi"
    elif dbplayer[1] == "Jones, Jr., Derrick":
        entry["lname"] = "Jones Jr."
        entry["fname"] = "Derrick"
    else:
        entry["lname"] = dbplayer[1].split(', ')[0]
        entry["fname"] = dbplayer[1].split(', ')[1]
    entry["from_year"] = dbplayer[4]
    entry["to_year"] = int(dbplayer[5])+1
    if dbplayer[12] == "Y":
        entry["games_played_FLAG"] = 1
    else:
        entry["games_played_FLAG"] = 0

    player_entries.append(entry)


if player_entries != []:
    for i in range(0, len(player_entries), 1000):
        db.insertRowDict(player_entries[i: i + 1000], "players", insertMany=True, replace=True, rid=0,debug=1)
        db.conn.commit()


end_time = time()
elapsed_time = float(end_time - start_time)
print "time elapsed (in seconds): " + str(elapsed_time)
print "time elapsed (in minutes): " + str(elapsed_time/60.0)
print "scraper_players.py"
print "-------------------------"
