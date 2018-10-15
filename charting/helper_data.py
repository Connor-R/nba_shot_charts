# A set of helper functions for the nba_shot_chart codebase

import pandas as pd
import numpy as np
import sys


from py_data_getter import data_getter
from py_db import db

db = db('nba_shots')

#Getting the shot data and returning a DataFrame with every shot for a specific player/season combo
def acquire_shootingData(dataType, _id, season='', isCareer=True):

    if isCareer is False:
        start_season_filt = str(season[:4])+'-08-01'
        end_season_filt = str(int(season[:4])+1)+'-08-01'

        query_append = """AND season_id = %s
        AND game_date > '%s'
        AND game_date < '%s'""" % (season.replace('-',''), start_season_filt, end_season_filt)
    else:
        query_append = ''

    shot_query = """SELECT
    season_id, game_id, 
    team_id, game_date,
    event_type, shot_type, 
    shot_zone_basic, shot_zone_area, LOC_X, LOC_Y,
    IF(event_type='Made Shot', 1, 0) AS SHOT_MADE_FLAG,
    zone_pct_plus,
    efg_plus
    FROM shots
    JOIN shots_%s_Relative_Year USING (season_id, season_type, %s_id, shot_zone_basic, shot_zone_area)
    WHERE %s_id = %s
    AND season_type = 'Reg'
    %s"""

    shot_q = shot_query % (dataType, dataType, dataType, _id, query_append)

    shots = db.query(shot_q)

    shot_data = {'season_id':[], 'game_id':[], 'team_id':[], 'game_date':[], 'event_type':[], 'shot_type':[], 'shot_zone_basic':[], 'shot_zone_area':[], 'LOC_X':[], 'LOC_Y':[], 'SHOT_MADE_FLAG':[], 'zone_pct_plus':[], 'efg_plus':[]}

    for row in shots:
        season_id, game_id, team_id, game_date, event_type, shot_type, shot_zone_basic, shot_zone_area, LOC_X, LOC_Y, SHOT_MADE_FLAG, zone_pct_plus, efg_plus = row

        shot_data['season_id'].append(season_id)
        shot_data['game_id'].append(game_id)
        shot_data['team_id'].append(team_id)
        shot_data['game_date'].append(game_date)
        shot_data['event_type'].append(event_type)
        shot_data['shot_type'].append(shot_type)
        shot_data['shot_zone_basic'].append(shot_zone_basic)
        shot_data['shot_zone_area'].append(shot_zone_area)
        shot_data['LOC_X'].append(LOC_X)
        shot_data['LOC_Y'].append(LOC_Y)
        shot_data['SHOT_MADE_FLAG'].append(SHOT_MADE_FLAG)
        shot_data['zone_pct_plus'].append(zone_pct_plus)
        shot_data['efg_plus'].append(efg_plus)

    shot_df = pd.DataFrame(shot_data, columns=shot_data.keys())

    return shot_df


# Get any of a variety of metrics from the Relative/Distribution/Breakdown/ShotSkill tables
def get_metrics(dataType, _id, season_id, isCareer, zone, metric):

    if isCareer is False:
        metric_q = """SELECT
        ROUND(%s,1)
        FROM shots_%s_Relative_Year r
        JOIN shots_%s_Distribution_Year d USING (%s_id, season_id, season_type, shot_zone_basic, shot_zone_area)
        JOIN shots_%s_Breakdown b USING (%s_id, season_id, season_type, shot_zone_basic, shot_zone_area)
        JOIN shot_skill_plus_%s_Year s USING (%s_id, season_id, season_type)
        JOIN percentiles_%s_Year p USING (%s_id, season_id, season_type)
        WHERE season_id = %s
        AND %s_id = %s
        AND shot_zone_area = 'all'
        AND shot_zone_basic = '%s'
        AND season_type = 'reg'
        """
        metric_qry = metric_q % (metric, dataType, dataType, dataType, dataType, dataType, dataType, dataType, dataType, dataType, season_id.replace('-',''), dataType, _id, zone)

    else:
        metric_q = """SELECT
        ROUND(%s,1)
        FROM shots_%s_Relative_Career r
        JOIN shots_%s_Distribution_Career d USING (%s_id, season_id, season_type, shot_zone_basic, shot_zone_area)
        JOIN(
            SELECT 
            %s_id, season_type, shot_zone_basic, shot_zone_area,
            SUM(games) AS games,
            SUM(attempts) AS attempts,
            SUM(makes) AS makes,
            SUM(points) AS points
            FROM shots_%s_Breakdown
            WHERE %s_id = %s
            AND season_type = 'reg'
            GROUP BY shot_zone_area, shot_zone_basic, season_type
        ) b USING (%s_id, season_type, shot_zone_basic, shot_zone_area)
        JOIN shot_skill_plus_%s_Career s USING (%s_id, season_id, season_type)
        JOIN percentiles_%s_Career p USING (%s_id, season_id, season_type)
        WHERE %s_id = %s
        AND shot_zone_area = 'all'
        AND shot_zone_basic = '%s'
        AND season_type = 'reg'
        """
        metric_qry = metric_q % (metric, dataType, dataType, dataType, dataType, dataType, dataType, _id, dataType, dataType, dataType, dataType, dataType, dataType, _id, zone)

    # raw_input(metric_qry)
    try:
        res = db.query(metric_qry)[0][0]
    except IndexError:
        res = 0

    return res


# Find the most extreme zone for a given player or team
def get_extreme_zones(dataType, _id, season_id, isCareer, positive_negative, metric):

    if isCareer is False:
        qry_add = "\nAND season_id = %s" % (season_id.replace('-',''))
        yearCareer = "Year"
    else:
        qry_add = ""
        yearCareer = "Career"

    if positive_negative == "positive":
        order_qry = "DESC"
    elif positive_negative == "negative":
        order_qry = "ASC"

    metric_q = """SELECT shot_zone_basic, %s
    FROM(
        SELECT
        shot_zone_basic, zone_pct, zone_pct_plus, zone_efg_plus, efg_plus, paa
        FROM shots_%s_Relative_%s r
        JOIN shots_%s_Distribution_%s d USING (%s_id, season_id, season_type, shot_zone_basic, shot_zone_area)
        WHERE %s_id = %s%s
        AND shot_zone_area = 'all'
        AND shot_zone_basic NOT IN ('all', 'Backcourt')
        AND season_type = 'reg'
        AND (zone_pct > 0.15 OR r.attempts > 50)
        ORDER BY %s %s
    ) a;"""

    metric_qry = metric_q % (metric, dataType, yearCareer, dataType, yearCareer, dataType, dataType, _id, qry_add, metric, order_qry)

    # raw_input(metric_qry)

    zone_name, zone_value = db.query(metric_qry)[0]

    zones_dict = {
    'all': 'All',
    'Above the Break 3': 'Break3',
    'Corner 3': 'Corner3',
    'In The Paint (Non-RA)': 'Paint(NonRA)',
    'Mid-Range': 'MidRange',
    'Restricted Area': 'Restricted',
    'Backcourt': 'Backcourt'}

    zone_name = zones_dict.get(zone_name)

    return zone_name, zone_value


# Get a text description based on a value and category
def get_text_description(category, value):
    qry = """SELECT word
    FROM percentile_text_descriptors
    WHERE category = '%s'
    AND percentile_floor = (
        SELECT max(percentile_floor)
        FROM percentile_text_descriptors
        WHERE category = '%s'
        AND %s >= percentile_floor
    );"""

    query = qry % (category, category, value)

    text_word = db.query(query)[0][0]

    return text_word


# Get percentile values from the percentiles table
def get_percentiles(dataType, _id, season_id, isCareer, zone, metric):

    if isCareer is False:
        metric_q = """SELECT
        ROUND(%s,1)
        FROM shots_%s_Relative_Year r
        JOIN shots_%s_Distribution_Year d USING (%s_id, season_id, season_type, shot_zone_basic, shot_zone_area)
        JOIN shots_%s_Breakdown b USING (%s_id, season_id, season_type, shot_zone_basic, shot_zone_area)
        JOIN shot_skill_plus_%s_Year s USING (%s_id, season_id, season_type)
        WHERE season_id = %s
        AND %s_id = %s
        AND shot_zone_area = 'all'
        AND shot_zone_basic = '%s'
        AND season_type = 'reg'
        """
        metric_qry = metric_q % (metric, dataType, dataType, dataType, dataType, dataType, dataType, dataType, season_id.replace('-',''), dataType, _id, zone)

    else:
        metric_q = """SELECT
        ROUND(%s,1)
        FROM shots_%s_Relative_Career r
        JOIN shots_%s_Distribution_Career d USING (%s_id, season_id, season_type, shot_zone_basic, shot_zone_area)
        JOIN(
            SELECT 
            %s_id, season_type, shot_zone_basic, shot_zone_area,
            SUM(games) AS games,
            SUM(attempts) AS attempts,
            SUM(makes) AS makes,
            SUM(points) AS points
            FROM shots_%s_Breakdown
            WHERE %s_id = %s
            AND season_type = 'reg'
            GROUP BY shot_zone_area, shot_zone_basic, season_type
        ) b USING (%s_id, season_type, shot_zone_basic, shot_zone_area)
        JOIN shot_skill_plus_%s_Career s USING (%s_id, season_id, season_type)
        WHERE %s_id = %s
        AND shot_zone_area = 'all'
        AND shot_zone_basic = '%s'
        AND season_type = 'reg'
        """
        metric_qry = metric_q % (metric, dataType, dataType, dataType, dataType, dataType, dataType, _id, dataType, dataType, dataType, dataType, _id, zone)

    # raw_input(metric_qry)
    try:
        res = db.query(metric_qry)[0][0]
    except IndexError:
        res = 0

    return res


#Getting the league efg for the season. If we're looking at a career, we naively use the league efg of all shots since 1996
def get_lg_efg(season_id, isCareer):
    if isCareer is False:
        q = """SELECT efg 
        FROM shots_League_Distribution_Year 
        WHERE season_id = %s
        AND shot_zone_basic = 'all'
        AND season_type = 'reg'
        """
        qry = q % (season_id.replace('-',''))

    else:
        q = """SELECT efg 
        FROM shots_League_Distribution_Career 
        WHERE shot_zone_basic = 'all'
        AND season_type = 'reg'
        """
        qry = q        
    
    lg_efg = db.query(qry)[0][0]

    return lg_efg