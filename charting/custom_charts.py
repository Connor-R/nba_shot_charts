import requests
import urllib
import os
import shutil
import csv
import sys
import glob
import math
import pandas as pd
import numpy as np
import argparse
import matplotlib as mpb
import matplotlib.pyplot as plt
from matplotlib import  offsetbox as osb
from matplotlib.patches import RegularPolygon
from datetime import date, datetime, timedelta
from time import time



sys.path.append('/Users/connordog/Dropbox/Desktop_Files/Work_Things/CodeBase/Python_Scripts/Python_Projects/packages')
from py_data_getter import data_getter
from py_db import db
db = db('nba_shots')


# setting the color map we want to use
mymap = mpb.cm.YlOrRd


whitelist_pngs = ['charts_description.png', 'nba_logo.png', '0.png', 'chart_icon.png']

base_path = os.getcwd()+"/shot_charts_custom_charts/"


def initiate(_type, _names, season_type, start_date, end_date, custom_title=None, custom_text=None, custom_img=None, custom_file=None):

    start_time = time()

    print '\n\ncharting.....'

    if _type == 'Player':
        print '\n\tplayers:\t',
    else:
        print '\n\tteams:\t\t',
    
    for n in _names:
        print n.replace(' ',''),

    print '\n\tseason type:\t' + str(season_type)
    print '\tstart date: \t' + str(start_date)
    print '\tend date: \t' + str(end_date) 
    if custom_title is not None:
        print '\ttitle: \t\t' + str(custom_title)
    if custom_text is not None:
        print '\ttext: \t\t' + str(custom_text)
    if custom_file is None:
        path_add = str(date.today())+'_'+str(datetime.now().hour)+'_'+str(datetime.now().minute)+'_'+str(datetime.now().second)+'.png'
    else:
        path_add = str(custom_file).replace(' ', '').replace(',','-') + '.png'
        print '\tfilename: \t' + str(custom_file).replace(' ', '_').replace(',','-') + '.png'

    path = base_path + path_add

    id_list = []
    print '\n\t\tgetting ids.....'
    if _type.lower() == 'player':
        for _name in _names:
            idq = """SELECT player_id FROM players WHERE CONCAT(fname, " ", lname) = '%s'""" % (_name)
            _id = int(db.query(idq)[0][0])
            id_list.append(_id)     
    elif _type.lower() == 'team':
        for _name in _names:
            idq = """SELECT team_id FROM teams WHERE CONCAT(city, " ", tname) = '%s'""" % (_name)
            _id = int(db.query(idq)[0][0])
            id_list.append(_id)
    print '\t\t\tDONE'

    ids = tuple(id_list)
    if len(ids) == 1:
        ids = '('+ str(ids[0]) + ')'

    # path_ids = zip(_names, id_list)
    # print len(path_ids)
    # raw_input(path_ids)

    if custom_title is None:
        custom_title = ''
        for n in _names[:-1]:
            custom_title += n
        custom_title += _names[-1]

    start2, end2 = get_dates(_type, ids, start_date, end_date, season_type)

    print '\t\tacquiring shooting data.....'
    shot_df = acquire_shootingData(ids, start_date, end_date, _type, season_type)
    print '\t\t\tDONE'

    if shot_df is not None and len(shot_df.index) != 0:
        shooting_plot(path, _type, shot_df, ids, _names, season_type, start_date, end_date, custom_title, custom_text, custom_img, start2, end2)

    end_time = time()
    elapsed_time = float(end_time - start_time)
    print "time elapsed (in seconds): \t" + str(elapsed_time)
    print "time elapsed (in minutes): \t" + str(elapsed_time/60.0)
    print "\n\n =================================================================================="

def acquire_shootingData(ids, start_date, end_date, _type='Player', season_type='Reg'):

    shot_query = """SELECT
    season_id, game_id, 
    team_id, game_date,
    event_type, shot_type, 
    shot_zone_basic, shot_zone_area, LOC_X, LOC_Y,
    IF(event_type='Made Shot', 1, 0) AS SHOT_MADE_FLAG,
    zone_pct_plus,
    efg_plus
    FROM shots
    JOIN shots_%s_Relative_Year USING (season_id, %s_id, season_type, shot_zone_basic, shot_zone_area)
    WHERE %s_id IN %s
    AND game_date >= '%s'
    AND game_date <= '%s'
    AND season_type = '%s';
    """

    shot_q = shot_query % (_type, _type, _type, ids, start_date, end_date, season_type)

    # raw_input(shot_q)
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


def shooting_plot(path, _type, shot_df, ids, _names, season_type, start_date, end_date, custom_title, custom_text, custom_img, start2, end2, plot_size=(12,12), gridNum=30):

    print '\t\tgetting shooting percentages in each zone.....'
    (ShootingPctLocs, shotNumber), shot_count_all = find_shootingPcts(shot_df, gridNum)
    print '\t\t\tDONE'

    print '\t\tcalculating metrics.....'
    metrics = calculate_metrics(_type, ids, start_date, end_date, season_type)
    print '\t\t\tDONE'

    all_efg_plus = float(get_metrics(metrics, 'all', 'efg_plus'))
    paa = float(get_metrics(metrics, 'all', 'paa'))
    color_efg = max(min(((all_efg_plus/100)-0.5),1.0),0.0)

    fig = plt.figure(figsize=(12,12))

    cmap = mymap

    ax = plt.axes([0.05, 0.15, 0.81, 0.775]) 

    ax.set_axis_bgcolor('#0C232E')

    draw_court(outer_lines=False)

    plt.xlim(-250,250)
    plt.ylim(370, -30)
    
    print '\t\tgetting icon.....'
    img = acquire_custom_pic(custom_img)
    ax.add_artist(img)
    print '\t\t\tDONE'
             
    max_radius_perc = 1.0
    max_rad_multiplier = 100.0/max_radius_perc

    area_multiplier = (3./4.)

    lg_efg = float(get_lg_metrics(start_date, end_date, season_type, 'all', 'efg'))

    print '\t\tplotting each hex bin.....'
    # i is the bin#, and shots is the shooting% for that bin
    for i, shots in enumerate(ShootingPctLocs): 
        x,y = shotNumber.get_offsets()[i]

        # we check the distance from the hoop the bin is. If it in 3pt territory, we add a multiplier of 1.5 to the shooting% to properly encapsulate eFG%
        dist = math.sqrt(x**2 + y**2)
        mult = 1.0
        if abs(x) >= 220:
            mult = 1.5
        elif dist/10 >= 23.75:
            mult = 1.5
        else:
            mult = 1.0

        # Setting the eFG% for a bin, making sure it's never over 1 (our maximum color value)
        color_pct = ((shots*mult)/lg_efg)-0.5
        bin_pct = max(min(color_pct, 1.0), 0.0)
        hexes = RegularPolygon(
            shotNumber.get_offsets()[i], #x/y coords
            numVertices=6, 
            radius=(295/gridNum)*((max_rad_multiplier*((shotNumber.get_array()[i]))/shot_count_all)**(area_multiplier)), 
            color=cmap(bin_pct),
            alpha=0.95, 
            fill=True)

        # setting a maximum radius for our bins at 295 (personal preference)
        if hexes.radius > 295/gridNum: 
            hexes.radius = 295/gridNum
        ax.add_patch(hexes)
    print '\t\t\tDONE'

    print '\t\tcreating the frequency legend.....'
    # we want to have 4 ticks in this legend so we iterate through 4 items
    for i in range(0,4):
        base_rad = max_radius_perc/4

        # the x,y coords for our patch (the first coordinate is (-205,415), and then we move up and left for each addition coordinate)
        patch_x = -205-(10*i)
        patch_y = 365-(14*i)

        # specifying the size of our hexagon in the frequency legend
        patch_rad = (299.9/gridNum)*((base_rad+(base_rad*i))**(area_multiplier))
        patch_perc = base_rad+(i*base_rad)

        # the x,y coords for our text
        text_x = patch_x + patch_rad + 2
        text_y = patch_y

        patch_axes = (patch_x, patch_y)

        # the text will be slightly different for our maximum sized hexagon,
        if i < 3:
            text_text = ' %s%% of Attempted Shots' % ('%.2f' % patch_perc)
        else:
            text_text = '$\geq$%s%% of Attempted Shots' %(str(patch_perc))
        
        # draw the hexagon. the color=map(eff_fg_all_float/100) makes the hexagons in the legend the same color as the player's overall eFG%
        patch = RegularPolygon(patch_axes, numVertices=6, radius=patch_rad, color=cmap(color_efg), alpha=0.95, fill=True)
        ax.add_patch(patch)

        # add the text for the hexagon
        ax.text(text_x, text_y, text_text, fontsize=12, horizontalalignment='left', verticalalignment='center', family='Bitstream Vera Sans', color='white', fontweight='bold')
    print '\t\t\tDONE'


    # Add a title to our frequency legend (the x/y coords are hardcoded).
    # Again, the color=map(eff_fg_all_float/100) makes the hexagons in the legend the same color as the player's overall eFG%
    ax.text(-235, 310, 'Zone Frequencies', fontsize = 15, horizontalalignment='left', verticalalignment='bottom', family='Bitstream Vera Sans', color=cmap(color_efg), fontweight='bold')

    print '\t\tadding text.....'
    # Add a title to our chart (just the player's name)
    chart_title = "%s" % (custom_title)
    ax.text(31.25,-40, chart_title, fontsize=29, horizontalalignment='center', verticalalignment='bottom', family='Bitstream Vera Sans', color=cmap(color_efg), fontweight='bold')

    # Add user text
    ax.text(-250,-31,'CHARTS BY @NBAChartBot',
        fontsize=10,  horizontalalignment='left', verticalalignment = 'bottom', family='Bitstream Vera Sans', color='white', fontweight='bold')

    # Add data source text
    ax.text(31.25,-31,'DATA FROM STATS.NBA.COM',
        fontsize=10,  horizontalalignment='center', verticalalignment = 'bottom', family='Bitstream Vera Sans', color='white', fontweight='bold')

    # Add date text
    _date = date.today()

    ax.text(250,-31,'AS OF %s' % (str(_date)),
        fontsize=10,  horizontalalignment='right', verticalalignment = 'bottom', family='Bitstream Vera Sans', color='white', fontweight='bold')


    key_text = get_key_text(_type, ids, start_date, end_date, metrics)
    # adding breakdown of eFG% by shot zone at the bottom of the chart
    ax.text(307,380, key_text, fontsize=12, horizontalalignment='right', verticalalignment = 'top', family='Bitstream Vera Sans', color='white', linespacing=1.5)

    if _type == 'Player':
        teams_text, team_len = get_teams_text(ids, start_date, end_date, custom_text, season_type)
    elif _type == 'Team':
        team_len = len(_names)
        if custom_text is None:
            teams_text = ''
            if len(_names) == 1:
                teams_text = str(_names[0])
            else:
                i = 0
                for team in _names[0:-1]:
                    if i%2 == 0 and i > 0:
                        teams_text += '\n'
                    text_add = '%s, ' % str(team)
                    teams_text += text_add
                    i += 1
                if i%2 == 0:
                    teams_text += '\n'
                teams_text += str(_names[-1])
        else:
            teams_text = custom_text


    if custom_text is None:
        if season_type == 'Reg':
            season_type_text = 'Regular Season Shots:\n'
        elif season_type == 'AS':
            season_type_text = 'All Star Shots:\n'
        elif season_type == 'Pre':
            season_type_text = 'Pre Season Shots:\n'
        elif season_type == 'Post':
            season_type_text = 'Post Season Shots:\n'
        else:
            season_type_text = 'All Shots:\n'
    else:
        season_type_text = ''

    if team_len > 6:
        ax.text(-250,380, str(start2) + ' to ' + str(end2) + '\n'+ season_type_text + teams_text,
            fontsize=8,  horizontalalignment='left', verticalalignment = 'top', family='Bitstream Vera Sans', color='white', linespacing=1.4)
    else:
        ax.text(-250,380,str(start2) + ' to ' + str(end2) + '\n'+ season_type_text + teams_text,
            fontsize=11,  horizontalalignment='left', verticalalignment = 'top', family='Bitstream Vera Sans', color='white', linespacing=1.5)
    print '\t\t\tDONE'


    # adding a color bar for reference
    ax2 = fig.add_axes([0.875, 0.15, 0.04, 0.775])
    cb = mpb.colorbar.ColorbarBase(ax2,cmap=cmap, orientation='vertical')
    cbytick_obj = plt.getp(cb.ax.axes, 'yticklabels')
    plt.setp(cbytick_obj, color='white', fontweight='bold')
    cb.set_label('EFG+ (100 is League Average)', family='Bitstream Vera Sans', color='white', fontweight='bold', labelpad=-4, fontsize=14)
    cb.set_ticks([0.0, 0.25, 0.5, 0.75, 1.0])
    cb.set_ticklabels(['$\mathbf{\leq}$50','75', '100','125', '$\mathbf{\geq}$150'])

    print 'ALL DONE\n\n'
    figtit = path
    plt.savefig(figtit, facecolor='#26373F', edgecolor='black')
    plt.clf()


def find_shootingPcts(shot_df, gridNum):
    x = shot_df.LOC_X[shot_df['LOC_Y']<425.1]
    y = shot_df.LOC_Y[shot_df['LOC_Y']<425.1]
    
    # Grabbing the x and y coords, for all made shots
    x_made = shot_df.LOC_X[(shot_df['SHOT_MADE_FLAG']==1) & (shot_df['LOC_Y']<425.1)]
    y_made = shot_df.LOC_Y[(shot_df['SHOT_MADE_FLAG']==1) & (shot_df['LOC_Y']<425.1)]
    
    #compute number of shots made and taken from each hexbin location
    hb_shot = plt.hexbin(x, y, gridsize=gridNum, extent=(-250,250,425,-50));
    plt.close()
    hb_made = plt.hexbin(x_made, y_made, gridsize=gridNum, extent=(-250,250,425,-50));
    plt.close()
    
    #compute shooting percentage
    ShootingPctLocs = hb_made.get_array() / hb_shot.get_array()
    ShootingPctLocs[np.isnan(ShootingPctLocs)] = 0 #makes 0/0s=0

    shot_count_all = len(shot_df.index)

    # Returning all values
    return (ShootingPctLocs, hb_shot), shot_count_all


def calculate_metrics(_type, ids, start_date, end_date, season_type):

    print '\t\t\tgetting breakdown.....'
    breakdown_q = """SELECT *
    FROM(
        SELECT shot_zone_basic,
        COUNT(*) AS attempts,
        SUM(CASE WHEN event_type = "Made Shot" THEN 1 ELSE 0 END) AS makes,
        SUM(CASE WHEN event_type = "Made Shot" AND shot_type = '2PT Field Goal' THEN 2 
            WHEN event_type = "Made Shot" AND shot_type = '3PT Field Goal' THEN 3
            ELSE 0 END) AS points
        FROM shots
        WHERE %s_id IN %s
        AND game_date >= '%s'
        AND game_date <= '%s'
        AND season_type = '%s'
        GROUP BY  shot_zone_basic
        UNION
        SELECT 'all' AS shot_zone_basic,
        COUNT(*) AS attempts,
        SUM(CASE WHEN event_type = "Made Shot" THEN 1 ELSE 0 END) AS makes,
        SUM(CASE WHEN event_type = "Made Shot" AND shot_type = '2PT Field Goal' THEN 2 
            WHEN event_type = "Made Shot" AND shot_type = '3PT Field Goal' THEN 3
            ELSE 0 END) AS points
        FROM shots
        WHERE %s_id IN %s
        AND game_date >= '%s'
        AND game_date <= '%s'
        AND season_type = '%s'
    ) a
    JOIN(SELECT COUNT(DISTINCT game_id) as games
        FROM shots
        WHERE %s_id IN %s
        AND game_date >= '%s'
        AND game_date <= '%s'
        AND season_type = '%s'
    ) b
    """
    breakdown_qry = breakdown_q % (_type, ids, start_date, end_date, season_type, _type, ids, start_date, end_date, season_type, _type, ids, start_date, end_date, season_type)

    # raw_input(breakdown_qry)
    breakdown = db.query(breakdown_qry)

    zone_data = []
    allatts = 0
    for row in breakdown:
        _z, att, mak, pts, gms = row
        efg = (float(pts)/float(att))/2.0
        entry = {'zone':_z, 'attempts':float(att), 'makes':float(mak), 'points':float(pts), 'games':float(gms), 'efg':efg}
        zone_data.append(entry)
        if _z == 'all':
            allatts = att

    print '\t\t\tgetting all league metrics.....'
    final_data = []
    lgALL_zone = float(get_lg_metrics(start_date, end_date, season_type, 'all', 'zone_pct'))
    lgALL_efg = float(get_lg_metrics(start_date, end_date, season_type, 'all', 'efg'))

    print '\t\t\tgetting zone league metrics.....'
    for entry in zone_data:
        z_pct = float(entry.get('attempts'))/float(allatts)
        entry['z_pct'] = z_pct

        lg_zone = float(get_lg_metrics(start_date, end_date, season_type, entry.get('zone'), 'zone_pct'))
        lg_efg = float(get_lg_metrics(start_date, end_date, season_type, entry.get('zone'), 'efg'))

        if lg_zone == 0:
            entry['zone_pct_plus'] = 0
        else:
            entry['zone_pct_plus'] = 100*(entry.get('z_pct')/lg_zone)

        if lg_efg == 0:
            entry['ZONE_efg_plus'] = 0
        else:
            entry['ZONE_efg_plus'] = 100*(entry.get('efg')/lg_efg)

        if lgALL_efg == 0:
            entry['efg_plus'] = 0
        else:
            entry['efg_plus'] = 100*(entry.get('efg')/lgALL_efg)

        zone_paa = entry.get('attempts')*(entry.get('efg')-lg_efg)*2
        entry['ZONE_paa'] = zone_paa
        entry['ZONE_paa_per_game'] = zone_paa/(entry.get('games')) 

        paa = entry.get('attempts')*(entry.get('efg')-lgALL_efg)*2
        entry['paa'] = paa
        entry['paa_per_game'] = paa/(entry.get('games'))

        final_data.append(entry)
    
    return final_data


def get_lg_metrics(start_date, end_date, season_type, shot_zone_basic, metric):
    q = """SELECT SUM(%s*attempts)/SUM(attempts) 
    FROM shots_League_Distribution_Year 
    WHERE season_id IN 
        (SELECT
        DISTINCT season_id
        FROM shots s
        WHERE game_date >= '%s'
        AND game_date <= '%s')
    AND shot_zone_basic = '%s'
    AND shot_zone_area = 'all'
    AND season_type  = '%s'
    """
    qry = q % (metric, start_date, end_date, shot_zone_basic, season_type)  
    # raw_input(qry)
    
    lg_val = db.query(qry)[0][0]

    if lg_val is None:
        return 0
    else:
        return lg_val


def get_metrics(metrics, zone, target):
    for row in metrics:
        if row.get('zone').lower() == zone.lower():
            return row.get(target)
    return 0


def draw_court(ax=None, color='white', lw=2, outer_lines=False):
    from matplotlib.patches import Circle, Rectangle, Arc
    if ax is None:
        ax = plt.gca()
    hoop = Circle((0, 0), radius=7.5, linewidth=lw, color=color, fill=False)
    backboard = Rectangle((-30, -7.5), 60, -1, linewidth=lw, color=color)
    outer_box = Rectangle((-80, -47.5), 160, 190, linewidth=lw, color=color,
                          fill=False)
    inner_box = Rectangle((-60, -47.5), 120, 190, linewidth=lw, color=color,
                          fill=False)
    top_free_throw = Arc((0, 142.5), 120, 120, theta1=0, theta2=180,
                         linewidth=lw, color=color, fill=False)
    bottom_free_throw = Arc((0, 142.5), 120, 120, theta1=180, theta2=0,
                            linewidth=lw, color=color, linestyle='dashed')
    restricted = Arc((0, 0), 80, 80, theta1=0, theta2=180, linewidth=lw,
                     color=color)
    corner_three_a = Rectangle((-220, -50.0), 0, 140, linewidth=lw,
                               color=color)
    corner_three_b = Rectangle((219.75, -50.0), 0, 140, linewidth=lw, color=color)
    three_arc = Arc((0, 0), 475, 475, theta1=22, theta2=158, linewidth=lw,
                    color=color)
    center_outer_arc = Arc((0, 422.5), 120, 120, theta1=180, theta2=0,
                           linewidth=lw, color=color)
    center_inner_arc = Arc((0, 422.5), 40, 40, theta1=180, theta2=0,
                           linewidth=lw, color=color)
    court_elements = [hoop, backboard, outer_box, inner_box, top_free_throw,
                      bottom_free_throw, restricted, corner_three_a,
                      corner_three_b, three_arc, center_outer_arc,
                      center_inner_arc]
    if outer_lines:
        outer_lines = Rectangle((-250, -47.5), 500, 470, linewidth=lw,
                                color=color, fill=False)
        court_elements.append(outer_lines)

    for element in court_elements:
        ax.add_patch(element)
    
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.set_xticks([])
    ax.set_yticks([])
    return ax


def get_teams_text(ids, start_date, end_date, custom_text, season_type):

    if custom_text is None:

        team_q = """SELECT
        DISTINCT CONCAT(city, ' ', tname)
        FROM shots s
        JOIN teams t USING (team_id)
        WHERE Player_id IN %s
        AND game_date >= '%s'
        AND game_date <= '%s'
        AND LEFT(season_id, 4) >= t.start_year
        AND LEFT(season_id, 4) < t.end_year
        AND season_type = '%s';
        """

        team_qry = team_q % (ids, start_date, end_date, season_type)

        teams = db.query(team_qry)

        team_list = []
        for team in teams:
            team_list.append(team[0])

        team_text = ""
        if len(team_list) == 1:
            team_text = str(team_list[0])
        else:
            i = 0
            for team in team_list[0:-1]:
                if i%2 == 0 and i > 0:
                    team_text += '\n'
                text_add = '%s, ' % str(team)
                team_text += text_add
                i += 1
            if i%2 == 0:
                team_text += '\n'
            team_text += str(team_list[-1])

        return team_text, len(team_list)

    else:
        return custom_text, 0


def get_key_text(_type, ids, start_date, end_date, metrics):

    text = ''

    for zone in ('All', 'Above The Break 3', 'Corner 3', 'Mid-Range', 'In The Paint (Non-RA)', 'Restricted Area'):
        if zone == 'All':
            text += 'All Shots | '
        elif zone == 'Above The Break 3':
            text += '\n' + 'Arc 3 | '
        elif zone == 'In The Paint (Non-RA)':
            text += '\n' + 'Paint(Non-RA) | '
        elif zone == 'Restricted Area':
            text += '\n' + 'Restricted | '
        else:
            text += '\n' + zone + ' | '    

        atts = ("%.0f" % get_metrics(metrics, zone, 'attempts'))
        makes = ("%.0f" % get_metrics(metrics, zone, 'makes'))
        zone_pct = ("%.1f" % (float(100)*get_metrics(metrics, zone, 'z_pct')))
        zone_pct_plus = ("%.1f" % get_metrics(metrics, zone, 'zone_pct_plus'))
        efg = ("%.1f" % (float(100)*get_metrics(metrics, zone, 'efg')))
        efg_plus = ("%.1f" % get_metrics(metrics, zone, 'efg_plus'))
        zone_efg_plus = ("%.1f" % get_metrics(metrics, zone, 'ZONE_efg_plus'))
        paa = ("%.1f" % get_metrics(metrics, zone, 'paa'))
        paa_game = ("%.1f" % get_metrics(metrics, zone, 'paa_per_game'))
        
        if zone == 'All':
            text += str(makes) + ' for ' + str(atts) + ' | '
            text += str(efg) + ' EFG% ('
            text += str(efg_plus) + ' EFG+ | '
            text += str(paa) + ' PAA) | '
            text += str(paa_game) + ' PAA/G'
        else:
            text += str(makes) + '/' + str(atts) + ' | '
            text += str(zone_pct) + '% z% (' + str(zone_pct_plus) + ' z%+) | '
            text += str(zone_efg_plus) + ' zEFG+ ('
            text += str(efg_plus) + ' EFG+ | '
            text += str(paa) + ' PAA)'
    return text

def get_dates(_type, ids, start_date, end_date, season_type):
    q = """SELECT MIN(game_date), MAX(game_date)
    FROM shots
    WHERE %s_id IN %s
    AND game_date >= '%s'
    AND game_date <= '%s'
    AND season_type = '%s';"""

    qry = q % (_type, ids, start_date, end_date, season_type)

    dates = db.query(qry)[0]

    start_date, end_date = dates

    return dates

def acquire_custom_pic(custom_img, offset=(250,370)):
    from matplotlib import offsetbox as osb
    import urllib
    
    if custom_img is not None:
        try:
            img_path = os.getcwd()+'/'+custom_img+'.png'
            player_pic = plt.imread(img_path)
        except IOError:
            img_path = os.getcwd()+'/chart_icon.png'
            player_pic = plt.imread(img_path)
    else:
        img_path = os.getcwd()+'/chart_icon.png'
        player_pic = plt.imread(img_path)

    img = osb.OffsetImage(player_pic)
    img = osb.AnnotationBbox(img, offset,xycoords='data',pad=0.0, box_alignment=(1,0), frameon=False)
    return img


# def gen_charts():


if __name__ == "__main__": 

    parser = argparse.ArgumentParser()

    # parser.add_argument('--_type',          default = 'Player')
    # parser.add_argument('--_names',         default = ["Paul Pierce"])
    # parser.add_argument('--season_type',    default = 'Post')
    # parser.add_argument('--start_date',     default = '1996-04-01')
    # parser.add_argument('--end_date',       default = '2017-10-01')
    # parser.add_argument('--custom_title',   default = 'Paul Pierce - Career Playoffs')
    # parser.add_argument('--custom_text',    default =  None)    
    # parser.add_argument('--custom_img',     default =  None) 
    # parser.add_argument('--custom_file',    default =  'PaulPierce_Playoffs')


    # parser.add_argument('--_type',          default = 'Player')
    # parser.add_argument('--_names',         default = ['John Wall', 'DeMar DeRozan', 'Jimmy Butler', 'Draymond Green', 'DeAndre Jordan'])
    # parser.add_argument('--season_type',    default = 'Reg')
    # parser.add_argument('--start_date',     default = '2016-06-14')
    # parser.add_argument('--end_date',       default = date.today())
    # parser.add_argument('--custom_title',   default = '2016-17 All NBA 3rd Team')
    # parser.add_argument('--custom_text',    default = 'John Wall\nDeMar DeRozan\nJimmy Butler\nDraymond Green\nDeAndre Jordan')
    # parser.add_argument('--custom_img',     default =  None) 
    # parser.add_argument('--custom_file',    default =  'AllNBA_3_201617') 


    parser.add_argument('--_type',          default = 'Player')
    parser.add_argument('--_names',         default = ["Blake Griffin"])
    parser.add_argument('--season_type',    default = 'Reg')
    parser.add_argument('--start_date',     default = '2017-06-01')
    parser.add_argument('--end_date',       default = '2018-06-01')
    parser.add_argument('--custom_title',   default = 'Blake Griffin - 2017/18')
    parser.add_argument('--custom_text',    default = None)    
    parser.add_argument('--custom_img',     default =  None) 
    parser.add_argument('--custom_file',    default =  'Blake Griffin_201718') 



    args = parser.parse_args()
    
    initiate(args._type, args._names, args.season_type, args.start_date, args.end_date, args.custom_title, args.custom_text, args.custom_img, args.custom_file)  
