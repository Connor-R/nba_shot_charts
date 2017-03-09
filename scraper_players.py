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


path = os.getcwd()
csv_file = open(path+'/player_list.csv', 'wb')
append_csv = csv.writer(csv_file)
header = ['_player_name', '_player_id', '_start_season', '_end_season']
append_csv.writerow(header)


no_shots_list = ['Marqus Blakely', 'Jerrelle Benimon', 'Michael McDonald', 'Trevor Winter', 'Alex Scales', 'Andy Panko', 'JamesOn Curry', 'Magnum Rolle', 'Anthony Bonner', 'Curtis Jerrells', 'Deng Gai', 'Gani Lawal', 'Herbert Hill', 'Kenny Hasbrouck', 'Terrico White', 'Guy Rucker', 'Brian Butch', 'Lionel Simmons', 'Chris Smith', 'Tony Gaffney']


player_names = []

player_q = """SELECT player_id, CONCAT(fname, ' ', lname) AS p_name, from_year, to_year
FROM players
WHERE games_played_FLAG = 1
AND to_year >= 1997
ORDER BY lname ASC, fname ASC, player_id ASC
"""

players = db.query(player_q)

for player in players:
    player_id, p_name, from_year, to_year = player

    if p_name not in no_shots_list:

        if p_name.split(' ')[0][1].isupper():
            temp_name = p_name
            p_name = ''
            for i in range(0, len(temp_name.split(' ')[0])):
                p_name += temp_name.split(' ')[0][i] + '.'
            for i in range(1, len(temp_name.split(' '))):
                p_name += ' ' + temp_name.split(' ')[i]
        if p_name not in player_names:
            player_names.append(p_name)
        else:
            i = 2
            op = False
            while op is False:
                p_name = p_name + '(' + str(i) + ')'
                if p_name not in player_names:
                    player_names.append(p_name)
                    op = True
                else:
                    i += 1

        row = [p_name, player_id, from_year, to_year]
        append_csv.writerow(row)


end_time = time()
elapsed_time = float(end_time - start_time)
print "scraper_players.py"
print "time elapsed (in seconds): " + str(elapsed_time)
print "time elapsed (in minutes): " + str(elapsed_time/60.0)
