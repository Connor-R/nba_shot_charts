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

    process()

    end_time = time()
    elapsed_time = float(end_time - start_time)
    print "shots_YearDistribution.py"
    print "time elapsed (in seconds): " + str(elapsed_time)
    print "time elapsed (in minutes): " + str(elapsed_time/60.0)

def process():
    for _type in ('Player', 'Team', 'League'):
        print '\t' + _type

        query = """SELECT *
FROM(
    SELECT
    %s_id, season_id, shot_zone_basic, shot_zone_area,
    SUM(attempts) AS attempts,
    SUM(attempts)/all_atts AS zone_pct,
    SUM(points)/SUM(attempts)/2 AS efg
    FROM shots_%s_Breakdown
    JOIN(
        SELECT %s_id, season_id, SUM(attempts) AS all_atts
        FROM shots_%s_Breakdown
        GROUP BY %s_id, season_id
    ) allatts USING (%s_id, season_id)
    GROUP BY %s_id, season_id, shot_zone_basic, shot_zone_area
    UNION
    SELECT
    %s_id, season_id, shot_zone_basic, 'all' AS shot_zone_area,
    SUM(attempts) AS attempts,
    SUM(attempts)/all_atts AS zone_pct,
    SUM(points)/SUM(attempts)/2 AS efg
    FROM shots_%s_Breakdown
    JOIN(
        SELECT %s_id, season_id, SUM(attempts) AS all_atts
        FROM shots_%s_Breakdown
        GROUP BY %s_id, season_id
    ) allatts USING (%s_id, season_id)
    GROUP BY %s_id, season_id, shot_zone_basic
    UNION
    SELECT
    %s_id, season_id, 'all' AS shot_zone_basic, 'all' AS shot_zone_area,
    SUM(attempts) AS attempts,
    SUM(attempts)/SUM(attempts) AS zone_pct,
    SUM(points)/SUM(attempts)/2 AS efg
    FROM shots_%s_Breakdown
    GROUP BY %s_id, season_id
) a
ORDER BY %s_id ASC, season_id ASC, shot_zone_basic ASC, shot_zone_area ASC
"""
        q = query % (_type, _type, _type, _type, _type, _type, _type, _type, _type, _type, _type, _type, _type, _type, _type, _type, _type, _type)

        res = db.query(q)

        entries = []
        _id = '%s_id' % (_type.lower())
        for row in res:
            type_id, season_id, shot_zone_basic, shot_zone_area, attempts, zone_pct, efg = row
            entry = {_id:type_id, "season_id":season_id, "shot_zone_basic":shot_zone_basic, "shot_zone_area":shot_zone_area, "attempts":attempts, "zone_pct":zone_pct, "efg":efg}   
            entries.append(entry)

        table = "shots_%s_YearDistribution" % (_type)
        if entries != []:
            for i in range(0, len(entries), 1000):
                db.insertRowDict(entries[i: i + 1000], table, insertMany=True, replace=True, rid=0,debug=1)
                db.conn.commit()

if __name__ == "__main__":     
    initiate()
