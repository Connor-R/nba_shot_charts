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

    process()

    end_time = time()
    elapsed_time = float(end_time - start_time)
    print "shots_Distribution_Career.py"
    print "time elapsed (in seconds): " + str(elapsed_time)
    print "time elapsed (in minutes): " + str(elapsed_time/60.0)


def process():
    for _type in ('Player', 'Team', 'League'):
        print '\t' + _type
        if _type == 'Player':
            _join = 'JOIN players USING (player_id)\n\t'
            _career = 'CONCAT(GREATEST(1996, from_year),to_year)'
        else:
            _join = ''
            _career = "'1'"

        query = """SELECT *
FROM(
    SELECT
    %s_id, %s AS career, shot_zone_basic, shot_zone_area,
    all_games AS games,
    SUM(attempts) AS attempts, 
    SUM(attempts)/all_atts AS zone_pct,
    SUM(points)/SUM(attempts)/2 AS efg
    FROM shots_%s_Breakdown
    %sJOIN(
        SELECT %s_id, SUM(games) AS all_games, SUM(attempts) AS all_atts
        FROM shots_%s_Breakdown
        WHERE shot_zone_basic = 'all'
        AND shot_zone_area = 'all'
        GROUP BY %s_id  
    ) allatts USING (%s_id)
    GROUP BY %s_id, shot_zone_basic, shot_zone_area
) a
ORDER BY %s_id ASC, shot_zone_basic ASC, shot_zone_area ASC
"""
        q = query % (_type, _career, _type, _join, _type, _type, _type, _type, _type, _type)

        res = db.query(q)

        entries = []
        _id = '%s_id' % (_type.lower())
        for row in res:
            type_id, career, shot_zone_basic, shot_zone_area, games, attempts, zone_pct, efg = row
            entry = {_id:type_id, "season_id":career, "shot_zone_basic":shot_zone_basic, "shot_zone_area":shot_zone_area, "games":games, "attempts":attempts, "zone_pct":zone_pct, "efg":efg}   
            entries.append(entry)

        table = "shots_%s_Distribution_Career" % (_type)
        if entries != []:
            for i in range(0, len(entries), 1000):
                db.insertRowDict(entries[i: i + 1000], table, insertMany=True, replace=True, rid=0,debug=1)
                db.conn.commit()


if __name__ == "__main__":     
    initiate()



    