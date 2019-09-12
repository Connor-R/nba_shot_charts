import requests
import urllib
import csv
import os
import sys
from time import time
import argparse

from py_data_getter import data_getter
from py_db import db

db = db('nba_shots')


def initiate(start_year, end_year):
    start_time = time()
    print "-------------------------"
    print "shots_Relative_Year.py"

    for year in range(start_year,end_year+1):
        season_start = year
        season_id = str(season_start)+str(season_start%100+1).zfill(2)[-2:]
        print season_id
        
        process(season_id)

    end_time = time()
    elapsed_time = float(end_time - start_time)
    print "time elapsed (in seconds): " + str(elapsed_time)
    print "time elapsed (in minutes): " + str(elapsed_time/60.0)
    print "shots_Relative_Year.py"
    print "-------------------------"


def process(season_id):
    for _type in ('Player', 'Team'):
        print '\t' + _type

        query = """SELECT
%s_id, season_id, season_type, b.shot_zone_basic, b.shot_zone_area, a.games, a.attempts, 
IFNULL((a.zone_pct/b.zone_pct)*100,0) AS zone_pct_plus, 
IFNULL((a.efg/b.efg)*100,0) AS ZONE_efg_plus,
IFNULL(a.attempts*(a.efg-b.efg)*2,0) AS ZONE_paa,
IFNULL((a.attempts*(a.efg-b.efg)*2)/a.games,0) AS ZONE_paa_per_game,
IFNULL((a.efg/c.efg)*100,0) AS efg_plus,
IFNULL(a.attempts*(a.efg-c.efg)*2,0) AS paa,
IFNULL((a.attempts*(a.efg-c.efg)*2)/a.games,0) AS paa_per_game,
IFNULL(a.attempts*(a.efg-repEFG)*2,0) AS par,
IFNULL((a.attempts*(a.efg-repEFG)*2)/a.games,0) AS par_per_game
FROM shots_%s_Distribution_Year a
JOIN shots_League_Distribution_Year b USING (season_id, season_type, shot_zone_basic, shot_zone_area)
JOIN shots_League_Distribution_Year c USING (season_id, season_type)
JOIN (SELECT season_id, season_type, MIN(efg) as repEFG FROM shots_Team_Distribution_Year WHERE shot_zone_basic='all' AND shot_zone_area='all' GROUP BY season_id, season_type) rep USING (season_id, season_type)
WHERE c.shot_zone_basic = 'all'
AND c.shot_zone_area = 'all'
AND season_id = '%s'
"""
        
        q = query % (_type, _type, season_id)
        # raw_input(q)

        res = db.query(q)

        entries = []
        _id = '%s_id' % (_type.lower())
        for row in res:
            type_id, season_id, season_type, z_basic, z_area, games, attempts, z_plus, ZONE_efg, ZONE_paa, ZONE_paag, efg, paa, paag, par, parg = row
            entry = {_id:type_id, "season_id":season_id, "season_type":season_type, "shot_zone_basic":z_basic, "shot_zone_area":z_area, "games":games, "attempts":attempts, "zone_pct_plus":z_plus, "ZONE_efg_plus":ZONE_efg, "ZONE_paa":ZONE_paa, "ZONE_paa_per_game":ZONE_paag, "efg_plus":efg, "paa":paa, "paa_per_game":paag, "par":par, "par_per_game":parg}   
            entries.append(entry)

        table = "shots_%s_Relative_Year" % (_type)
        if entries != []:
            for i in range(0, len(entries), 1000):
                db.insertRowDict(entries[i: i + 1000], table, insertMany=True, replace=True, rid=0,debug=1)
                db.conn.commit()


if __name__ == "__main__":     
    parser = argparse.ArgumentParser()
    parser.add_argument('--start_year',type=int,default=2018)
    parser.add_argument('--end_year',type=int,default=2018)

    args = parser.parse_args()
    
    initiate(args.start_year, args.end_year)



