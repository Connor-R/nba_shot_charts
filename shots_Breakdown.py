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
    print "-------------------------"
    print "shots_Breakdown.py"

    for year in range(2016,2017):
        season_start = year
        season_id = str(season_start)+str(season_start%100+1).zfill(2)[-2:]
        print season_id
        
        process(season_id)

    end_time = time()
    elapsed_time = float(end_time - start_time)
    print "time elapsed (in seconds): " + str(elapsed_time)
    print "time elapsed (in minutes): " + str(elapsed_time/60.0)
    print "shots_Breakdown.py"
    print "-------------------------"



def process(season_id):
    for _type in ('League', 'Team', 'Player'):
        print '\t' + _type

        query_id = _type
        if query_id == 'League':
            query_id = "'00' AS League"


        query = """SELECT *
FROM(
    SELECT %s_id, season_id, season_type, shot_zone_basic, shot_zone_area,
    COUNT(*) AS attempts,
    AVG(shot_distance) AS avg_dist,
    SUM(CASE WHEN event_type = "Made Shot" THEN 1 ELSE 0 END) AS makes,
    SUM(CASE WHEN event_type = "Made Shot" AND shot_type = '2PT Field Goal' THEN 2 
        WHEN event_type = "Made Shot" AND shot_type = '3PT Field Goal' THEN 3
        ELSE 0 END) AS points
    FROM shots
    WHERE season_id = %s
    GROUP BY %s_id, season_id, season_type, shot_zone_basic, shot_zone_area
) a
JOIN(
    SELECT %s_id, season_id, season_type,
    COUNT(DISTINCT game_id) AS games
    FROM shots
    WHERE season_id = %s
    GROUP BY %s_id, season_id, season_type
) g USING (%s_id, season_id, season_type)
UNION
SELECT *
FROM(
    SELECT %s_id, season_id, season_type, shot_zone_basic, 'all' AS shot_zone_area,
    COUNT(*) AS attempts,
    AVG(shot_distance) AS avg_dist,
    SUM(CASE WHEN event_type = "Made Shot" THEN 1 ELSE 0 END) AS makes,
    SUM(CASE WHEN event_type = "Made Shot" AND shot_type = '2PT Field Goal' THEN 2 
        WHEN event_type = "Made Shot" AND shot_type = '3PT Field Goal' THEN 3
        ELSE 0 END) AS points
    FROM shots
    WHERE season_id = %s
    GROUP BY %s_id, season_id, season_type, shot_zone_basic
) a
JOIN(
    SELECT %s_id, season_id, season_type, 
    COUNT(DISTINCT game_id) AS games
    FROM shots
    WHERE season_id = %s
    GROUP BY %s_id, season_id, season_type
) g USING (%s_id, season_id, season_type)
UNION
SELECT *
FROM(
    SELECT %s_id, season_id, season_type, 'all' AS shot_zone_basic, 'all' AS shot_zone_area,
    COUNT(*) AS attempts,
    AVG(shot_distance) AS avg_dist,
    SUM(CASE WHEN event_type = "Made Shot" THEN 1 ELSE 0 END) AS makes,
    SUM(CASE WHEN event_type = "Made Shot" AND shot_type = '2PT Field Goal' THEN 2 
        WHEN event_type = "Made Shot" AND shot_type = '3PT Field Goal' THEN 3
        ELSE 0 END) AS points
    FROM shots
    WHERE season_id = %s
    GROUP BY %s_id, season_id, season_type
) a
JOIN(
    SELECT %s_id, season_id, season_type, 
    COUNT(DISTINCT game_id) AS games
    FROM shots
    WHERE season_id = %s
    GROUP BY %s_id, season_id, season_type
) g USING (%s_id, season_id, season_type)
ORDER BY %s_id ASC, season_id ASC, shot_zone_basic ASC, shot_zone_area ASC
"""


        q = query % (query_id, season_id, _type, query_id, season_id, _type, _type, query_id, season_id, _type, query_id, season_id, _type, _type, query_id, season_id, _type, query_id, season_id, _type, _type, _type)

        # raw_input(q)
        res = db.query(q)

        entries = []
        _id = '%s_id' % (_type.lower())
        for row in res:
            type_id, season_id, season_type, shot_zone_basic, shot_zone_area, attempts, avg_dist, makes, points, games = row
            entry = {_id:type_id, "season_id":season_id, "season_type":season_type, "shot_zone_basic":shot_zone_basic, "shot_zone_area":shot_zone_area, "attempts":attempts, "avg_dist":avg_dist, "makes":makes, "points":points, "games":games}   
            entries.append(entry)

        table = "shots_%s_Breakdown" % (_type)
        if entries != []:
            for i in range(0, len(entries), 1000):
                db.insertRowDict(entries[i: i + 1000], table, insertMany=True, replace=True, rid=0,debug=1)
                db.conn.commit()



if __name__ == "__main__":     
    initiate()



