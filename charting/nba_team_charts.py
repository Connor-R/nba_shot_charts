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
    teams_cnt = 0
    charts_cnt = 0
    for team_identifier, team_data in p_list.items():
        team_id, city, tname, start_year, end_year = team_data
        start_year, end_year = int(start_year), int(end_year)

        team_title = city + ' ' + tname
        team_name = team_title.replace(" ","_")

        if printer is True:
            print "\n\nProcessing Team " + str(counter) + " of " + list_length + ': ' + team_identifier + ' (' + str(start_year) + ' - ' + str(end_year) + ')\n'
        counter += 1

        start_year = max(1996, start_year)
        end_year = min(2018, end_year)

        path = base_path+'/shot_charts_team/'+str(city.replace(' ','_'))+'_'+str(tname.replace(' ','_'))+'('+str(team_id)+')/'

        if not os.path.exists(path):
            os.makedirs(path)

        os.chdir(path)
        files=glob.glob('*.png')
        for filename in files:
            if 'CAREER' in filename:
                os.unlink(filename)
        os.chdir(base_path)


        for year in range(start_year,end_year):
            season_start = year

            season_id = str(season_start)+'-'+str(season_start%100+1).zfill(2)[-2:]

            if printer is True:
                print '\t',
                print season_id, city, tname, team_id 

            year_shots_df = helper_data.acquire_shootingData('team', team_id, season=season_id, isCareer=False)

            if year_shots_df is not None and len(year_shots_df.index) != 0:
                helper_charting.shooting_plot('team', path, year_shots_df, team_id, season_id, team_title, team_name)
                charts_cnt += 1

        os.chdir(base_path)
        files=glob.glob('*.png')
        for white in whitelist_pngs:
            if white in files:
                files.remove(white)
        for filename in files:
            os.unlink(filename)

        teams_cnt += 1
        temp_end = time()
        elapsed_time = float(temp_end - start_time)
        print "\ntime elapsed (in seconds): \t" + str(elapsed_time)
        print "time elapsed (in minutes): \t" + str(elapsed_time/60.0)
        print "teams processed: \t\t" + str(teams_cnt)
        print "charts made: \t\t\t" + str(charts_cnt)
        print "average seconds per chart: \t" + str(elapsed_time/float(charts_cnt))
        print "average seconds per team: \t" + str(elapsed_time/float(teams_cnt))
        print "\n\n =================================================================================="


#for usage with shot_chart_bot
def gen_charts(team_string):
    p_list = get_plist()
    vals = p_list.get(team_string)
    if vals is None:
        sys.exit('Need a valid team (check spelling)')
    player_list = {team_string:vals}

    initiate(player_list, str(len(player_list)), printer=False)


#teams_list generation
def get_plist(backfill=False):
    p_list = {}
 
    query = """SELECT team_id, city, tname, start_year, end_year, end_year-GREATEST(1996,start_year) AS seasons_cnt
    FROM teams
    WHERE end_year >= 1997
    ORDER BY team_id ASC, end_year DESC"""
    res = db.query(query)
 
    for row in res:
        team_id, city, team_name, start_year, end_year, seasons_cnt = row
 
        team_search_name = city.replace(" ","_") + "_" + team_name.replace(" ","_")
 
        if backfill is True:
            if os.path.exists(os.getcwd()+'/shot_charts_team/'+team_search_name+'('+str(team_id)+')'):
                continue
 
        # a filter for which teams to update
        p_list[city.replace(' ','_')+'_'+team_name.replace(' ','_')+'('+str(team_id)+')'] = [team_id, city, team_name, start_year, end_year]
 
    return p_list


if __name__ == "__main__": 

    team_list = get_plist(backfill=True)

    print "\nBegin processing " + str(len(team_list)) + " teams\n"

    initiate(team_list, str(len(team_list)))

