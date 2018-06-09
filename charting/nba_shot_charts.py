import os
import shutil
import sys
import glob
import pandas as pd
import argparse
from datetime import date, datetime
from time import time


from py_data_getter import data_getter
from py_db import db
import helper_charting
import helper_data


db = db('nba_shots')


whitelist_pngs = ['charts_description.png', 'nba_logo.png', '0.png', 'chart_icon.png']


def initiate(p_list, list_length, printer=True):
    start_time = time()

    base_path = os.getcwd()

    counter = 1
    players_cnt = 0
    charts_cnt = 0
    for player_id, player_data in p_list.items():
        player_title, start_year, end_year = player_data
        start_year, end_year = int(start_year), int(end_year)

        if printer is True:
            print "\n\nProcessing Player " + str(counter) + " of " + list_length + ': ' + player_title + ' (' + str(start_year) + ' - ' + str(end_year) + ')'
        counter += 1

        start_year = max(1996, start_year)
        end_year = min(2019, end_year)

        player_name = player_title.replace(" ","_")

        checker_q = "SELECT * FROM shots_Player_Distribution_Career WHERE player_id = %s  AND season_type = 'reg'" % (player_id)
        checker = db.query(checker_q)
        if checker == ():
            print "\tNo shots, continuing to next player"
            continue

        path = base_path+'/shot_charts_player/'+player_name+'('+str(player_id)+')/'

        if not os.path.exists(path):
            os.makedirs(path)

        os.chdir(path)
        files=glob.glob('*.png')
        for filename in files:
            os.unlink(filename)
        os.chdir(base_path)

        all_shots_df = pd.DataFrame()

        for year in range(start_year,end_year):
            season_start = year

            season_id = str(season_start)+'-'+str(season_start%100+1).zfill(2)[-2:]

            # if printer is True:
            #     print '\n\t', season_id, player_name, player_id 

            year_shots_df = helper_data.acquire_shootingData('player', player_id, season=season_id, isCareer=False)

            if year_shots_df is not None and len(year_shots_df.index) != 0:

                helper_charting.shooting_plot('player', path, year_shots_df, player_id, season_id, player_title, player_name)
                charts_cnt += 1

        career_string = "CAREER (%s-%s)" % (start_year, end_year)
        # if printer is True:
        #     print '\t\t\t', career_string, player_name

        all_shots_df = helper_data.acquire_shootingData('player', player_id, isCareer=True)

        helper_charting.shooting_plot('player', path, all_shots_df, player_id, career_string, player_title, player_name, isCareer=True, min_year=start_year, max_year=end_year)
        players_cnt += 1
        charts_cnt += 1

        os.chdir(base_path)
        files=glob.glob('*.png')
        for white in whitelist_pngs:
            if white in files:
                files.remove(white)
        for filename in files:
            os.unlink(filename)

        temp_end = time()
        elapsed_time = float(temp_end - start_time)
        print "\ntime elapsed (in seconds): \t" + str(elapsed_time)
        print "time elapsed (in minutes): \t" + str(elapsed_time/60.0)
        print "players processed: \t\t" + str(players_cnt)
        print "charts made: \t\t\t" + str(charts_cnt)
        print "average seconds per chart: \t" + str(elapsed_time/float(charts_cnt))
        print "average seconds per player: \t" + str(elapsed_time/float(players_cnt))
        print "\n\n =================================================================================="


#for usage with shot_chart_bot
def gen_charts(player_id):
    p_list = get_plist()
    
    vals = p_list.get(player_id)

    if vals is None:
        sys.exit('Need a valid player (check spelling)')

    player_list = {player_id:vals}
    # raw_input(player_list)

    initiate(player_list, str(len(player_list)), printer=False)


#player_list generation
def get_plist(operator='', filt_value=0, backfill=False):
    p_list = {}

    query = """SELECT player_id, CONCAT(fname, ' ', lname), from_year, to_year
    FROM players
    WHERE games_played_FLAG = 1
    AND to_year >= 1997
    ORDER BY lname ASC, fname ASC, player_id ASC"""
    res = db.query(query)

    for row in res:
        player_id, player_title, start_year, end_year = row

        if player_title.split(' ')[0][1].isupper() and player_title not in ('OG Anunoby',):
            temp_name = player_title
            player_title = ''
            for i in range(0, len(temp_name.split(' ')[0])):
                player_title += temp_name.split(' ')[0][i] + '.'
            for i in range(1, len(temp_name.split(' '))):
                player_title += ' ' + temp_name.split(' ')[i]

        player_search_name = player_title.replace(" ","_")

        # Charts for only new players (only for backfilling)
        if backfill is True:
            if os.path.exists(os.getcwd()+'/shot_charts_player/'+player_search_name+'('+str(player_id)+')'):
                continue

        # a filter for which players to update
        if operator is '':
            p_list[player_id]=[str(player_title), int(start_year), int(end_year)]
        else:
            if operator == '>=':
                if int(end_year) >= filt_value:
                    p_list[player_id]=[str(player_title), int(start_year), int(end_year)]
            elif operator == '<=':
                if int(end_year) <= filt_value:
                    p_list[player_id]=[str(player_title), int(start_year), int(end_year)]
            else:
                print 'unknown operator, using =='
                if int(end_year) == filt_value:
                    p_list[player_id]=[str(player_title), int(start_year), int(end_year)]

    return p_list


if __name__ == "__main__": 

    parser = argparse.ArgumentParser()

    # call via [python nba_shot_charts.py --player_name "Zach Randolph"]
    parser.add_argument('--player_name',type=str,   default='')
    args = parser.parse_args()

    if args.player_name != '':
        p_list = get_plist()
        for k,vs in p_list.items():
            if args.player_name == vs[0]:
                vals = vs
                p_key = k
        if vals is None:
            sys.exit('Need a valid player name')
        player_list = {p_key:vals}
    else:
        # If we don't have a name, we assume we're trying to backfill
        # player_list = get_plist(operator='==', filt_value=2018, backfill=False)
        player_list = get_plist(operator='<=', filt_value=9999, backfill=True)

    print "\nBegin processing " + str(len(player_list)) + " players"

    initiate(player_list, str(len(player_list)))

