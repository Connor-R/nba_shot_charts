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


sys.path.append('/Users/connordog/Dropbox/Desktop_Files/Work_Things/CodeBase/Python_Scripts/Python_Projects/packages')
from py_data_getter import data_getter
from py_db import db
db = db('nba_shots')


# setting the color map we want to use
mymap = mpb.cm.YlOrRd


whitelist_pngs = ['charts_description.png',]


# taking in a dictionary of player information and initializing the processes
def initiate(p_list, list_length, printer=True):
    # setting our base directory, I have this set to your current working directory (cwd)
    base_path = os.getcwd()

    # iterating through our player dictionary to grab the player_title and player_id
    counter = 1
    for player_title, player_data in p_list.items():
        player_id, start_year, end_year = player_data
        start_year, end_year = int(start_year), int(end_year)

        if printer is True:
            print "\n\nProcessing Player " + str(counter) + " of " + list_length + ': ' + player_title + ' (' + str(start_year) + ' - ' + str(end_year) + ')\n'
        counter += 1

        if start_year < 1996:
            start_year = 1996
        if end_year > 2017:
            end_year = 2017

        player_name = player_title.replace(" ","_")

        checker_q = "SELECT * FROM shots_Player_Distribution_Career WHERE player_id = %s" % (player_id)
        checker = db.query(checker_q)
        if checker == ():
            print "\tNo shots, continuing to next player"
            continue

        # defines a path to a directory for saving the charts of the current player
        path = base_path+'/shot_charts_player/'+player_name+'('+str(player_id)+')/'

        # checks if our desired directory exists, archived the charts if they exist, and (re-)create the directory
        if not os.path.exists(path):
            os.makedirs(path)
        # if you download this code and re-use it, you'll either have to alter the path in the next line, or delete the following 3 lines
        else:
            arch_path = '/Users/connordog/Desktop/archived_charts/'+str(date.today())+'_'+str(datetime.now().hour)+'_'+player_name+'('+str(player_id)+')/'
            if os.path.exists(arch_path):
                shutil.rmtree(arch_path)
            os.rename(path, arch_path)
            os.makedirs(path)

        # deletes previous versions of images
        os.chdir(path)
        files=glob.glob('*.png')
        for filename in files:
            os.unlink(filename)
        os.chdir(base_path)

        # we set an empty DataFrame and will append each year's shots, creating a career shot log
        all_shots_df = pd.DataFrame()

        # we iterate through each year of a player's career, creating a shot chart for every year while also adding each season's data to our all_shots_df DataFrame
        for year in range(start_year,end_year):
            season_start = year

            # takes a season (e.g. 2008) and returns the nba ID (e.g. 2008-09)
            season_id = str(season_start)+'-'+str(season_start%100+1).zfill(2)[-2:]

            if printer is True:
                # we print the season/player combo in order to monitor progress
                print '\t',
                print season_id, player_name, player_id 

            # a DataFrame of the shots a player took in a given season
            year_shots_df = acquire_shootingData(player_id, season=season_id, isCareer=False)

            # if the DataFrame isn't empty (i.e., if the player played this season), we make a shot chart for this season
            if year_shots_df is not None and len(year_shots_df.index) != 0:

                # plotting the data for the given season/player combination we are iterating through
                shooting_plot(path, year_shots_df, player_id, season_id, player_title, player_name)

        career_string = "CAREER (%s-%s)" % (start_year, end_year)
        if printer is True:
            print '\t\t\t', career_string, player_name

        all_shots_df = acquire_shootingData(player_id, isCareer=True)

        shooting_plot(path, all_shots_df, player_id, career_string, player_title, player_name, isCareer=True, min_year=start_year, max_year=end_year)

        # after we finish the script, we remove all the player images that were saved to the directory during the acquire_playerPic function
        os.chdir(base_path)
        files=glob.glob('*.png')
        for white in whitelist_pngs:
            if white in files:
                files.remove(white)
        for filename in files:
            os.unlink(filename)



#Getting the shot data and returning a DataFrame with every shot for a specific player/season combo
def acquire_shootingData(player_id,season='',isCareer=True):


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
    JOIN shots_Player_Relative_Year USING (season_id, player_id, shot_zone_basic, shot_zone_area)
    WHERE player_id = %s
    %s"""

    shot_q = shot_query % (player_id, query_append)

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


# we set gridNum to be 30 (basically a grid of 30x30 hexagons)
def shooting_plot(path, shot_df, player_id, season_id, player_title, player_name, isCareer=False, min_year = 0, max_year = 0, plot_size=(12,12), gridNum=30):

    # get the shooting percentage and number of shots for all bins, all shots, and a subset of some shots
    (ShootingPctLocs, shotNumber), shot_count_all = find_shootingPcts(shot_df, gridNum)

    all_efg_plus = float(get_metrics(player_id, season_id, isCareer, 'all', 'efg_plus'))
    paa = float(get_metrics(player_id, season_id, isCareer, 'all', 'paa'))
    color_efg = max(min(((all_efg_plus/100)-0.5),1.0),0.0)

    # set the figure for drawing on
    fig = plt.figure(figsize=(12,12))

    # cmap will be used as our color map going forward
    cmap = mymap

    # where to place the plot within the figure, first two attributes are the x_min and y_min, and the next 2 are the % of the figure that is covered in the x_direction and y_direction (so in this case, our plot will go from (0.05, 0.15) at the bottom left, and stretches to (0.85,0.925) at the top right)
    ax = plt.axes([0.05, 0.15, 0.81, 0.775]) 

    # setting the background color using a hex code (http://www.rapidtables.com/web/color/RGB_Color.htm)
    ax.set_axis_bgcolor('#0C232E')

    # draw the outline of the court
    draw_court(outer_lines=False)

    # specify the dimensions of the court we draw
    plt.xlim(-250,250)
    plt.ylim(370, -30)
    
    # draw player image
    zoom = 1 # we don't need to zoom the image at all
    img = acquire_playerPic(player_id, zoom)
    ax.add_artist(img)
             
    # specify the % a zone that we want to correspond to a maximum sized hexagon [I have this set to any zone with >= 1% of all shots will have a maximum radius, but it's free to be changed based on personal preferences]
    max_radius_perc = 1.0
    max_rad_multiplier = 100.0/max_radius_perc

    # changing to what power we want to scale the area of the hexagons as we increase/decrease the radius. This value can also be changed for personal preferences.
    area_multiplier = (3./4.)

    lg_efg = float(get_lg_efg(season_id, isCareer))

    # draw hexagons
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

    # creating the frequency legend
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

    # Add a title to our frequency legend (the x/y coords are hardcoded).
    # Again, the color=map(eff_fg_all_float/100) makes the hexagons in the legend the same color as the player's overall eFG%
    ax.text(-235, 310, 'Zone Frequencies', fontsize = 15, horizontalalignment='left', verticalalignment='bottom', family='Bitstream Vera Sans', color=cmap(color_efg), fontweight='bold')

    # Add a title to our chart (just the player's name)
    chart_title = "%s" % (player_title.upper())
    ax.text(31.25,-40, chart_title, fontsize=29, horizontalalignment='center', verticalalignment='bottom', family='Bitstream Vera Sans', color=cmap(color_efg), fontweight='bold')

    # Add user text
    ax.text(-250,-31,'CHARTS BY CONNOR REED',
        fontsize=10,  horizontalalignment='left', verticalalignment = 'bottom', family='Bitstream Vera Sans', color='white', fontweight='bold')

    # Add data source text
    ax.text(31.25,-31,'DATA FROM STATS.NBA.COM',
        fontsize=10,  horizontalalignment='center', verticalalignment = 'bottom', family='Bitstream Vera Sans', color='white', fontweight='bold')

    # Add date text
    _date = date.today()

    ax.text(250,-31,'AS OF %s' % (str(_date)),
        fontsize=10,  horizontalalignment='right', verticalalignment = 'bottom', family='Bitstream Vera Sans', color='white', fontweight='bold')


    key_text = get_key_text(player_id, season_id, isCareer)
    # adding breakdown of eFG% by shot zone at the bottom of the chart
    ax.text(307,380, key_text, fontsize=12, horizontalalignment='right', verticalalignment = 'top', family='Bitstream Vera Sans', color='white', linespacing=1.5)

    teams_text, team_len = get_teams_text(player_id, season_id, isCareer)
    # adding which season the chart is for, as well as what teams the player is on
    if team_len > 12:
        ax.text(-250,380, season_id + ' Regular Season:\n' + teams_text,
            fontsize=10,  horizontalalignment='left', verticalalignment = 'top', family='Bitstream Vera Sans', color='white', linespacing=1.4)
    else:
        ax.text(-250,380,season_id + ' Regular Season:\n' + teams_text,
            fontsize=10,  horizontalalignment='left', verticalalignment = 'top', family='Bitstream Vera Sans', color='white', linespacing=1.6)

    # adding a color bar for reference
    ax2 = fig.add_axes([0.875, 0.15, 0.04, 0.775])
    cb = mpb.colorbar.ColorbarBase(ax2,cmap=cmap, orientation='vertical')
    cbytick_obj = plt.getp(cb.ax.axes, 'yticklabels')
    plt.setp(cbytick_obj, color='white', fontweight='bold')
    cb.set_label('EFG+ (100 is League Average)', family='Bitstream Vera Sans', color='white', fontweight='bold', labelpad=-4, fontsize=14)
    cb.set_ticks([0.0, 0.25, 0.5, 0.75, 1.0])
    cb.set_ticklabels(['$\mathbf{\leq}$50','75', '100','125', '$\mathbf{\geq}$150'])

    figtit = path+'shot_charts_%s(%s)_%s_%s_%s.png' % (player_name, player_id, season_id.replace(' ',''), str(int(round(all_efg_plus))), str(int(round(paa))) )
    plt.savefig(figtit, facecolor='#26373F', edgecolor='black')
    plt.clf()


#Producing the text for the bottom of the shot chart
def get_teams_text(player_id, season_id, isCareer):

    if isCareer is True:
        season_q = ''
    else:
        season_q = '\nAND season_id = %s' % (season_id.replace('-',''))

    team_q = """SELECT
    DISTINCT CONCAT(city, ' ', tname)
    FROM shots s
    JOIN teams t USING (team_id)
    WHERE player_id = %s%s
    AND LEFT(season_id, 4) >= t.start_year
    AND LEFT(season_id, 4) < t.end_year;
    """

    team_qry = team_q % (player_id, season_q)

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


#Producing the text for the bottom of the shot chart
def get_key_text(player_id, season_id, isCareer):

    text = ''

    for _type in ('All', 'Above The Break 3', 'Corner 3', 'Mid-Range', 'In The Paint (Non-RA)', 'Restricted Area'):
        if _type == 'All':
            text += 'All Shots | '
        elif _type == 'Above The Break 3':
            text += '\n' + 'Arc 3 | '
        elif _type == 'In The Paint (Non-RA)':
            text += '\n' + 'Paint(Non-RA) | '
        elif _type == 'Restricted Area':
            text += '\n' + 'Restricted | '
        else:
            text += '\n' + _type + ' | '        

        atts = ("%.0f" %get_metrics(player_id, season_id, isCareer, _type, 'r.attempts'))
        makes = ("%.0f" %get_metrics(player_id, season_id, isCareer, _type, 'b.makes'))
        zone_pct = ("%.1f" % get_metrics(player_id, season_id, isCareer, _type, 'zone_pct*100'))
        zone_pct_plus = ("%.1f" % get_metrics(player_id, season_id, isCareer, _type, 'zone_pct_plus'))
        efg = ("%.1f" % get_metrics(player_id, season_id, isCareer, _type, 'efg*100'))
        efg_plus = ("%.1f" % get_metrics(player_id, season_id, isCareer, _type, 'efg_plus'))
        zone_efg_plus = ("%.1f" % get_metrics(player_id, season_id, isCareer, _type, 'zone_efg_plus'))
        paa = ("%.1f" % get_metrics(player_id, season_id, isCareer, _type, 'paa'))
        paa_game = ("%.1f" % get_metrics(player_id, season_id, isCareer, _type, 'paa_per_game'))
        
        if _type == 'All':
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


#Getting the player's metrics for the given season
def get_metrics(player_id, season_id, isCareer, zone, metric):

    if isCareer is False:
        metric_q = """SELECT
        ROUND(%s,1)
        FROM shots_Player_Relative_Year r
        JOIN shots_Player_Distribution_Year d USING (player_id, season_id, shot_zone_basic, shot_zone_area)
        JOIN shots_Player_Breakdown b USING (player_id, season_id, shot_zone_basic, shot_zone_area)
        WHERE season_id = %s
        AND player_id = %s
        AND shot_zone_area = 'all'
        AND shot_zone_basic = '%s'
        """
        metric_qry = metric_q % (metric, season_id.replace('-',''), player_id, zone)

    else:
        metric_q = """SELECT
        ROUND(%s,1)
        FROM shots_Player_Relative_Career r
        JOIN shots_Player_Distribution_Career d USING (player_id, season_id, shot_zone_basic, shot_zone_area)
        JOIN(
            SELECT 
            player_id, shot_zone_basic, shot_zone_area,
            SUM(games) AS games,
            SUM(attempts) AS attempts,
            SUM(makes) AS makes,
            SUM(points) AS points
            FROM shots_Player_Breakdown
            WHERE player_id = %s
            GROUP BY shot_zone_area, shot_zone_basic
        ) b USING (player_id, shot_zone_basic, shot_zone_area)
        WHERE player_id = %s
        AND shot_zone_area = 'all'
        AND shot_zone_basic = '%s'
        """
        metric_qry = metric_q % (metric, player_id, player_id, zone)

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
        """
        qry = q % (season_id.replace('-',''))

    else:
        q = """SELECT efg 
        FROM shots_League_Distribution_Career 
        WHERE shot_zone_basic = 'all'
        """
        qry = q        
    
    lg_efg = db.query(qry)[0][0]

    return lg_efg


#Getting the shooting percentages for each grid.
#The general idea of this function, as well as a substantial block of the actual code was recycled from Dan Vatterott [http://www.danvatterott.com/]
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


#Drawing the outline of the court
#Most of this code was recycled from Savvas Tjortjoglou [http://savvastjortjoglou.com] 
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

#for usage with shot_chart_bot
def gen_charts(player_name):
    p_list = get_plist()
    vals = p_list.get(player_name)
    if vals is None:
        sys.exit('Need a valid player (check spelling)')
    player_list = {player_name:vals}

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

        if player_title.split(' ')[0][1].isupper():
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
            p_list[player_title]=[int(player_id), int(start_year), int(end_year)]
        else:
            if operator == '>=':
                if int(end_year) >= filt_value:
                    p_list[player_title]=[int(player_id), int(start_year), int(end_year)]
            elif operator == '<=':
                if int(end_year) <= filt_value:
                    p_list[player_title]=[int(player_id), int(start_year), int(end_year)]
            else:
                print 'unknown operator, using =='
                if int(end_year) == filt_value:
                    p_list[player_title]=[int(player_id), int(start_year), int(end_year)]

    return p_list


#Getting the player picture that we will later place in the chart
#Most of this code was recycled from Savvas Tjortjoglou [http://savvastjortjoglou.com] 
def acquire_playerPic(player_id, zoom, offset=(250,370)):
    from matplotlib import  offsetbox as osb
    import urllib
    
    try:
        img_path = os.getcwd()+'/'+str(player_id)+'.png'
        player_pic = plt.imread(img_path)
    except IOError:
        try:
            pic = urllib.urlretrieve("http://stats.nba.com/media/players/230x185/"+str(player_id)+".png",str(player_id)+".png")
            player_pic = plt.imread(pic[0])
        except ValueError:
            pic = urllib.urlretrieve("http://stats.nba.com/media/players/230x185/0.png", str(player_id)+'.png')
            player_pic = plt.imread(pic[0])    


    img = osb.OffsetImage(player_pic, zoom)
    img = osb.AnnotationBbox(img, offset,xycoords='data',pad=0.0, box_alignment=(1,0), frameon=False)
    return img


if __name__ == "__main__": 

    parser = argparse.ArgumentParser()

    # call via [python nba_shot_charts.py --player_name "Zach Randolph"]
    parser.add_argument('--player_name',type=str,   default='')
    args = parser.parse_args()

    if args.player_name != '':
        p_list = get_plist()
        vals = p_list.get(args.player_name)
        if vals is None:
            sys.exit('Need a valid player name')
        player_list = {args.player_name:vals}
    else:
        # If we don't have a name, we assume we're trying to backfill
        player_list = get_plist(operator='<=', filt_value=9999, backfill=True)

    print "\nBegin processing " + str(len(player_list)) + " players\n"

    initiate(player_list, str(len(player_list)))

