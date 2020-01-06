import requests
import urllib
import csv
import os
import sys
from time import time, sleep


from py_data_getter import data_getter
from py_db import db

db = db('nba_shots')

start_time = time()

getter = data_getter()

team_url = 'http://stats.nba.com/stats/franchisehistory?LeagueID=00'

print "-------------------------"
print "scraper_teams.py"

json = getter.get_url_data(team_url, "json", nba=True)
sleep(5)

resultSets = json["resultSets"]

teams = resultSets[0]["rowSet"]

teams_entries = []

for team in teams:
    entry = {}
    entry["team_id"] = team[1]
    entry["city"] = team[2]
    entry["tname"] = team[3]
    entry["start_year"] = team[4]
    entry["end_year"] = int(team[5])+1

    teams_entries.append(entry)


if teams_entries != []:
    for i in range(0, len(teams_entries), 1000):
        db.insertRowDict(teams_entries[i: i + 1000], "teams", insertMany=True, replace=True, rid=0,debug=1)
        db.conn.commit()

#delete duplicate entries
list_query = """SELECT t1.*
FROM teams t1
JOIN teams t2 USING (team_id, end_year)
WHERE t1.start_year < t2.start_year
GROUP BY team_id"""
del_list = db.query(list_query)

for team in del_list:
    team_id, city, tname, start_year, end_year = team
    del_temp = """DELETE FROM teams
    WHERE team_id = %s
    AND city = '%s'
    AND tname = '%s'
    AND start_year = %s
    AND end_year = %s
    """
    del_qry = del_temp % (team_id, city, tname, start_year, end_year)

    db.query(del_qry)
    db.conn.commit()

db.query("DELETE FROM teams WHERE city = 'New Orleans/Oklahoma City'")
db.conn.commit()

end_time = time()
elapsed_time = float(end_time - start_time)
print "time elapsed (in seconds): " + str(elapsed_time)
print "time elapsed (in minutes): " + str(elapsed_time/60.0)
print "scraper_teams.py"
print "-------------------------"
