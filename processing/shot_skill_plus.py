 # tables:
 #    -shot_skill_plus_player_year
 #    -shot_skill_plus_player_career
 #    -shot_skill_plus_team_year
 #    -shot_skill_plus_team_career

import requests
import urllib
import csv
import os
import sys
from time import time


from py_data_getter import data_getter
from py_db import db

db = db('nba_shots')


def initiate():
    start_time = time()
    print "-------------------------"
    print "shot_skill_plus.py"

    for group_type in ('Player', 'Team'):
        for time_type in ('Year', 'Career'):
            print '\t', group_type, time_type

            process(group_type, time_type)

    end_time = time()
    elapsed_time = float(end_time - start_time)
    print "time elapsed (in seconds): " + str(elapsed_time)
    print "time elapsed (in minutes): " + str(elapsed_time/60.0)
    print "shot_skill_plus.py"
    print "-------------------------"



def process(group_type, time_type):
    query = """SELECT %s_id, season_id, season_type, attempts, ROUND(sum_efg_plus/attempts,4) AS ShotSkillPlus
        FROM(
            SELECT %s_id, season_id, season_type, SUM(attempts*zone_efg_plus) AS sum_efg_plus
            FROM shots_%s_Relative_%s r
            WHERE shot_zone_area != 'all'
            AND shot_zone_basic != 'all'
            GROUP BY %s_id, season_id, season_type
        ) a
        JOIN(
            SELECT %s_id, season_id, season_type, attempts
            FROM shots_%s_Relative_%s r
            WHERE shot_zone_area = 'all'
            AND shot_zone_basic = 'all'
            GROUP BY %s_id, season_id, season_type          
        ) b USING (%s_id, season_id, season_type);
"""


    q = query % (group_type, group_type, group_type, time_type, group_type, group_type, group_type, time_type, group_type, group_type)

    # raw_input(q)
    res = db.query(q)
    # raw_input(res)
    entries = []
    _id = '%s_id' % (group_type.lower())
    for row in res:
        # print row
        type_id, season_id, season_type, attempts, shotskillplus = row
        entry = {_id:type_id, "season_id":season_id, "season_type":season_type, "attempts":attempts, "ShotSkillPlus":shotskillplus}   
        entries.append(entry)

    table = "shot_skill_plus_%s_%s" % (group_type, time_type)

    if time_type == "Career":
        db.query("TRUNCATE TABLE %s;" % (table))

    if entries != []:
        for i in range(0, len(entries), 1000):
            db.insertRowDict(entries[i: i + 1000], table, insertMany=True, replace=True, rid=0,debug=1)
            db.conn.commit()



if __name__ == "__main__":     
    initiate()
