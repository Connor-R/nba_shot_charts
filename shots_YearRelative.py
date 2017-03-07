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
    print "shots_YearRelative.py"
    print "time elapsed (in seconds): " + str(elapsed_time)
    print "time elapsed (in minutes): " + str(elapsed_time/60.0)


def process():
    for _type in ('Player', 'Team'):
        print '\t' + _type

        query = """SELECT
%s_id, season_id, shot_zone_basic, shot_zone_area, a.attempts, 
a.zone_pct/b.zone_pct AS zone_pct_plus, 
(a.efg/b.efg)*100 AS efg_plus
FROM shots_%s_YearDistribution a
JOIN shots_League_YearDistribution b USING (season_id, shot_zone_basic, shot_zone_area)
"""

        q = query % (_type, _type)

        res = db.query(q)

        entries = []
        _id = '%s_id' % (_type.lower())
        for row in res:
            type_id, season_id, shot_zone_basic, shot_zone_area, attempts, zone_pct_plus, efg_plus = row
            entry = {_id:type_id, "season_id":season_id, "shot_zone_basic":shot_zone_basic, "shot_zone_area":shot_zone_area, "attempts":attempts, "zone_pct_plus":zone_pct_plus, "efg_plus":efg_plus}   
            entries.append(entry)

        table = "shots_%s_YearRelative" % (_type)
        if entries != []:
            for i in range(0, len(entries), 1000):
                db.insertRowDict(entries[i: i + 1000], table, insertMany=True, replace=True, rid=0,debug=1)
                db.conn.commit()


if __name__ == "__main__":     
    initiate()



