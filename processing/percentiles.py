import os
import sys
import numpy as np
from time import time
import argparse

from py_data_getter import data_getter
from py_db import db

db = db('nba_shots')


def initiate(start_year, end_year):
    start_time = time()
    print "-------------------------"
    print "percentiles.py"

    print '\n\ncalculating percentile baselines'
    for year in range(start_year,end_year+1):
        season_start = year
        season_id = str(season_start)+str(season_start%100+1).zfill(2)[-2:]

        process_percentiles(season_id)

    print '\n\nupdating yearly percentiles'
    update_yearly_percentiles()

    print '\n\nupdating career percentiles'
    update_career_percentiles()

    end_time = time()
    elapsed_time = float(end_time - start_time)
    print "time elapsed (in seconds): " + str(elapsed_time)
    print "time elapsed (in minutes): " + str(elapsed_time/60.0)
    print "percentiles.py"
    print "-------------------------"
    

def process_percentiles(season_id):
    print season_id
    for season_type in ('Reg', 'Post', 'Pre'):
        for _type in ('Player', 'Team'):

            qry = """SELECT %s_id, season_id, 
            efg_plus, 
            ROUND(attempts/games,1) AS volume,
            ShotSkillPlus,
            paa_per_game,
            par_per_game
            FROM shots_%s_relative_year
            JOIN(
                SELECT 
                %s_id, season_id, ROUND(sum_efg_plus/attempts,2) AS ShotSkillPlus
                FROM(
                    SELECT %s_id, season_id, SUM(attempts*zone_efg_plus) AS sum_efg_plus
                    FROM shots_%s_Relative_Year r
                    WHERE season_type = '%s'
                    AND shot_zone_area = 'all'
                    AND shot_zone_basic != 'all'
                    AND season_id = %s
                    GROUP BY %s_id, season_id
                ) a
                JOIN(
                    SELECT %s_id, season_id, attempts
                    FROM shots_%s_Relative_Year r
                    WHERE season_type = '%s'
                    AND shot_zone_area = 'all'
                    AND shot_zone_basic = 'all'
                    AND season_id = %s
                    GROUP BY %s_id, season_id
                ) b USING (%s_id, season_id)
            ) ShotSkill USING (%s_id, season_id)
            WHERE season_type = '%s'
            AND season_id = %s
            AND shot_zone_basic = 'All'
            AND games > 2
            AND attempts > 25;"""

            query = qry % (_type, _type, _type, _type, _type, season_type, season_id, _type, _type, _type, season_type, season_id, _type, _type, _type, season_type, season_id)
            # raw_input(query)
            res = db.query(query)

            if res == ():
                continue

            EFGplus_list = []
            AttemptsPerGame_list = []
            shotSkillPlus_list = []
            PAAperGame_list = []
            PARperGame_list = []

            for row in res:
                foo, foo, EFGplus, AttemptsPerGame, shotSkillPlus, PAAperGame, PARperGame = row

                EFGplus_list.append(float(EFGplus))
                AttemptsPerGame_list.append(float(AttemptsPerGame))
                shotSkillPlus_list.append(float(shotSkillPlus))
                PAAperGame_list.append(float(PAAperGame))
                PARperGame_list.append(float(PARperGame))

            for cat in ('EFG', 'AttemptsPerGame', 'shotSkill', 'PAAperGame', 'PARperGame'):
                entries = []
                # print '\t', '('+str(len(res))+')', season_type, _type, cat

                if cat == 'EFG':
                    arry = np.array(EFGplus_list)
                elif cat == 'AttemptsPerGame':
                    arry = np.array(AttemptsPerGame_list)
                elif cat == 'shotSkill':
                    arry = np.array(shotSkillPlus_list)
                elif cat == 'PAAperGame':
                    arry = np.array(PAAperGame_list)
                elif cat == 'PARperGame':
                    arry = np.array(PARperGame_list)

                for i in range(0,101):
                    pv = np.percentile(arry, i)
                    percentile_value = np.percentile(arry, i)

                    # print _type, cat, i, percentile_value

                    entry = {'season_id':season_id, 'season_type':season_type, 'player_team':_type, 'category':cat, 'percentile':i, 'floor_value': percentile_value}

                    # print entry
                    entries.append(entry)

                table = "percentile_baselines"
                if entries != []:
                    for i in range(0, len(entries), 1000):
                        db.insertRowDict(entries[i: i + 1000], table, insertMany=True, replace=True, rid=0,debug=1)
                        db.conn.commit()


def update_yearly_percentiles():

    for _type in ('Player', 'Team'):
        print '\t', _type
        entries = []

        relative_qry = """SELECT 
        %s_id, season_id, season_type, 
        r.attempts, r.games, 
        r.attempts/r.games, efg_plus, paa/r.games, par/r.games, ShotSkillPlus
        FROM shots_%s_relative_Year r
        JOIN shot_skill_plus_%s_Year ss USING (%s_id, season_id, season_type)
        WHERE shot_zone_basic = 'all'
        AND season_type != 'AS';"""
        relative_query = relative_qry % (_type, _type, _type, _type)

        relative_res = db.query(relative_query)

        for i, row in enumerate(relative_res):
            entry = {}
           
            _id, season_id, season_type, attempts, games, att_per_game, efg_plus, paa, par, ShotSkillPlus = row
           
            id_key = _type+'_id'
            entry[id_key] = _id
            entry['season_id'] = season_id
            entry['season_type'] = season_type
            entry['games'] = games
            entry['attempts'] = attempts

            category_dict = {
            'AttemptsPerGame': att_per_game,
            'EFG': efg_plus,
            'PAAperGame': paa,
            'PARperGame': par,
            'shotSkill': ShotSkillPlus,
            }

            for category, category_value in category_dict.items():
                qry = """SELECT IFNULL(MIN(percentile),100)
                FROM percentile_baselines
                WHERE season_type = '%s'
                AND player_team = '%s'
                AND season_id = %s
                AND category = '%s'
                AND IFNULL(%s,0) <= floor_value;"""

                query = qry % (season_type, _type, season_id, category, category_value)
                # print query
                category_percentile = db.query(query)[0][0]

                category_key = category+'_percentile'
                entry[category_key] = category_percentile
                entries.append(entry)


        table = "percentiles_%s_Year" % (_type)
        if entries != []:
            for i in range(0, len(entries), 1000):
                db.insertRowDict(entries[i: i + 1000], table, insertMany=True, replace=True, rid=0,debug=1)
                db.conn.commit()

# Career percentiles are WEIGHTED AVERAGE percentiles over the players career
def update_career_percentiles():

    for _type in ('Player', 'Team'):
        print '\t', _type
        entries = []

        qry = """SELECT 
        %s_id, ssp.season_id, season_type, SUM(attempts), SUM(games),
        ROUND(SUM(AttemptsPerGame_percentile*games)/SUM(games),1),
        ROUND(SUM(EFG_Percentile*attempts)/SUM(attempts),1),
        ROUND(SUM(PAAperGame_percentile*attempts)/SUM(attempts),1),
        ROUND(SUM(PARperGame_percentile*attempts)/SUM(attempts),1),
        ROUND(SUM(shotSkill_Percentile*attempts)/SUM(attempts),1)
        FROM percentiles_%s_Year
        JOIN (SELECT %s_id, season_id, season_type FROM shot_skill_plus_%s_Career) ssp USING (%s_id, season_type)
        GROUP By %s_id, season_type;""" 

        query = qry % (_type, _type, _type, _type, _type, _type)

        res = db.query(query)
        for i, row in enumerate(res):
            entry = {}
           
            _id, season_id, season_type, attempts, games, AttemptsPerGame_percentile, EFG_Percentile, PAAperGame_percentile, PARperGame_percentile, shotSkill_Percentile = row

            id_key = _type+'_id'
            entry[id_key] = _id
            entry['season_id'] = season_id
            entry['season_type'] = season_type
            entry['games'] = games
            entry['attempts'] = attempts
            entry['AttemptsPerGame_percentile'] = AttemptsPerGame_percentile
            entry['EFG_Percentile'] = EFG_Percentile
            entry['PAAperGame_percentile'] = PAAperGame_percentile
            entry['PARperGame_percentile'] = PAAperGame_percentile
            entry['shotSkill_Percentile'] = shotSkill_Percentile

            entries.append(entry)

        table = "percentiles_%s_Career" % (_type)

        db.query("TRUNCATE TABLE %s;" % (table))

        if entries != []:
            for i in range(0, len(entries), 1000):
                db.insertRowDict(entries[i: i + 1000], table, insertMany=True, replace=True, rid=0,debug=1)
                db.conn.commit()





if __name__ == "__main__":     
    parser = argparse.ArgumentParser()
    parser.add_argument('--start_year',type=int,default=1996)
    parser.add_argument('--end_year',type=int,default=2018)

    args = parser.parse_args()
    
    initiate(args.start_year, args.end_year)



