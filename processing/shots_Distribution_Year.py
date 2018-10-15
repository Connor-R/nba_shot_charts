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
    print "shots_Distribution_Year.py"

    for year in range(start_year,end_year+1):
        season_start = year
        season_id = str(season_start)+str(season_start%100+1).zfill(2)[-2:]
        print season_id
        
        process(season_id)

    end_time = time()
    elapsed_time = float(end_time - start_time)
    print "time elapsed (in seconds): " + str(elapsed_time)
    print "time elapsed (in minutes): " + str(elapsed_time/60.0)
    print "shots_Distribution_Year.py"
    print "-------------------------"


def process(season_id):
    for _type in ('Player', 'Team', 'League'):
        print '\t' + _type

        query = """SELECT *
FROM(
    SELECT
    %s_id, season_id, season_type, shot_zone_basic, shot_zone_area,
    games,
    SUM(attempts) AS attempts,
    SUM(attempts)/all_atts AS zone_pct,
    SUM(points)/SUM(attempts)/2 AS efg
    FROM shots_%s_Breakdown
    JOIN(
        SELECT %s_id, season_id, season_type, SUM(attempts) AS all_atts
        FROM shots_%s_Breakdown
        WHERE season_id = '%s'
        AND shot_zone_basic = 'all'
        AND shot_zone_area = 'all'
        GROUP BY %s_id, season_id, season_type
    ) allatts USING (%s_id, season_id, season_type)
    WHERE season_id = '%s'
    GROUP BY %s_id, season_id, season_type, shot_zone_basic, shot_zone_area
) a
ORDER BY %s_id ASC, season_id ASC, shot_zone_basic ASC, shot_zone_area ASC, season_type DESC
"""
        q = query % (_type, _type, _type, _type, season_id, _type, _type, season_id, _type, _type)

        # raw_input(q)
        res = db.query(q)

        entries = []
        _id = '%s_id' % (_type.lower())
        for row in res:
            type_id, season_id, season_type, shot_zone_basic, shot_zone_area, games, attempts, zone_pct, efg = row
            entry = {_id:type_id, "season_id":season_id, "season_type":season_type, "shot_zone_basic":shot_zone_basic, "shot_zone_area":shot_zone_area, "games":games, "attempts":attempts, "zone_pct":zone_pct, "efg":efg}   
            entries.append(entry)

        table = "shots_%s_Distribution_Year" % (_type)
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
