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
    print "-------------------------"
    print "shots_Relative_Career.py"


    start_time = time()

    process()

    end_time = time()
    elapsed_time = float(end_time - start_time)
    print "time elapsed (in seconds): " + str(elapsed_time)
    print "time elapsed (in minutes): " + str(elapsed_time/60.0)
    print "shots_Relative_Career.py"
    print "-------------------------"

def process():
    for _type in ('Player', 'Team'):
        print '\t' + _type
        if _type == 'Player':
            _join = 'JOIN players USING (player_id)\n'
            _career = 'CONCAT(GREATEST(1996, from_year),to_year)'
        else:
            _join = ''
            _career = "'1'"

        query = """SELECT
%s_id, %s AS career, season_type, c.shot_zone_basic, c.shot_zone_area,
all_games AS games,
SUM(a.attempts) AS attempts,
IFNULL(100*(SUM(b.attempts*b.zone_pct/c.zone_pct)/SUM(b.attempts)),0) AS zone_pct_plus,
IFNULL(100*(SUM(b.attempts*b.efg/c.efg)/SUM(b.attempts)),0) AS ZONE_efg_plus,
IFNULL(SUM(ZONE_paa),0) as ZONE_paa,
IFNULL(SUM(ZONE_paa)/all_games,0) as ZONE_paa_per_game,
IFNULL(100*(SUM(b.attempts*b.efg/d.efg)/SUM(b.attempts)),0) AS efg_plus,
IFNULL(SUM(paa),0) AS paa,
IFNULL(SUM(paa)/all_games,0) AS paa_per_game,
IFNULL(SUM(par),0) AS par,
IFNULL(SUM(par)/all_games,0) AS par_per_game
FROM shots_%s_Relative_Year a
%sJOIN shots_%s_Distribution_Year b USING (%s_id, season_id, season_type, shot_zone_basic, shot_zone_area)
JOIN shots_League_Distribution_Year c USING (season_id, season_type, shot_zone_basic, shot_zone_area)
JOIN shots_League_Distribution_Year d USING (season_id, season_type)
JOIN(
    SELECT %s_id, season_type, SUM(games) AS all_games
    FROM shots_%s_Breakdown
    WHERE shot_zone_basic = 'all'
    AND shot_zone_area = 'all'
    GROUP BY %s_id, season_type
) g USING (%s_id, season_type)
WHERE d.shot_zone_basic = 'all'
AND d.shot_zone_area = 'all'
GROUP BY %s_id, season_type, shot_zone_basic, shot_zone_area
"""

        q = query % (_type, _career, _type, _join, _type, _type, _type, _type, _type, _type, _type)

        # raw_input(q)
        res = db.query(q)

        entries = []
        _id = '%s_id' % (_type.lower())
        for row in res:
            type_id, season_id, season_type, z_basic, z_area, games, attempts, z_plus, ZONE_efg, ZONE_paa, ZONE_paag, efg, paa, paag, par, parg = row
            entry = {_id:type_id, "season_id":season_id, "season_type":season_type, "shot_zone_basic":z_basic, "shot_zone_area":z_area, "games":games, "attempts":attempts, "zone_pct_plus":z_plus, "ZONE_efg_plus":ZONE_efg, "ZONE_paa":ZONE_paa, "ZONE_paa_per_game":ZONE_paag, "efg_plus":efg, "paa":paa, "paa_per_game":paag, "par":par, "par_per_game":parg}

            entries.append(entry)

        table = "shots_%s_Relative_Career" % (_type)
        if entries != []:
            for i in range(0, len(entries), 1000):
                db.insertRowDict(entries[i: i + 1000], table, insertMany=True, replace=True, rid=0,debug=1)
                db.conn.commit()


if __name__ == "__main__":     
    initiate()



