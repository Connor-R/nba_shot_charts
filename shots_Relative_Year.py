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


def initiate():
    start_time = time()

    for year in range(2016,2017):
        season_start = year
        season_id = str(season_start)+str(season_start%100+1).zfill(2)[-2:]
        print season_id
        
        process(season_id)

    end_time = time()
    elapsed_time = float(end_time - start_time)
    print "shots_Relative_Year.py"
    print "time elapsed (in seconds): " + str(elapsed_time)
    print "time elapsed (in minutes): " + str(elapsed_time/60.0)


def process(season_id):
    for _type in ('Player', 'Team'):
        print '\t' + _type

        query = """SELECT
%s_id, season_id, b.shot_zone_basic, b.shot_zone_area, a.games, a.attempts, 
(a.zone_pct/b.zone_pct)*100 AS zone_pct_plus, 
(a.efg/b.efg)*100 AS ZONE_efg_plus,
a.attempts*(a.efg-b.efg)*2 AS ZONE_paa,
(a.attempts*(a.efg-b.efg)*2)/a.games AS ZONE_paa_per_game,
(a.efg/c.efg)*100 AS efg_plus,
a.attempts*(a.efg-c.efg)*2 AS paa,
(a.attempts*(a.efg-c.efg)*2)/a.games AS paa_per_game
FROM shots_%s_Distribution_Year a
JOIN shots_League_Distribution_Year b USING (season_id, shot_zone_basic, shot_zone_area)
JOIN shots_League_Distribution_Year c USING (season_id)
WHERE c.shot_zone_basic = 'all'
AND c.shot_zone_area = 'all'
AND season_id = '%s'
"""

        q = query % (_type, _type, season_id)

        res = db.query(q)

        entries = []
        _id = '%s_id' % (_type.lower())
        for row in res:
            type_id, season_id, z_basic, z_area, games, attempts, z_plus, ZONE_efg, ZONE_paa, ZONE_paag, efg, paa, paag = row
            entry = {_id:type_id, "season_id":season_id, "shot_zone_basic":z_basic, "shot_zone_area":z_area, "games":games, "attempts":attempts, "zone_pct_plus":z_plus, "ZONE_efg_plus":ZONE_efg, "ZONE_paa":ZONE_paa, "ZONE_paa_per_game":ZONE_paag, "efg_plus":efg, "paa":paa, "paa_per_game":paag}   
            entries.append(entry)

        table = "shots_%s_Relative_Year" % (_type)
        if entries != []:
            for i in range(0, len(entries), 1000):
                db.insertRowDict(entries[i: i + 1000], table, insertMany=True, replace=True, rid=0,debug=1)
                db.conn.commit()


if __name__ == "__main__":     
    initiate()



