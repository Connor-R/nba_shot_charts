# A set of helper functions for the nba_shot_chart codebase

import urllib
import os
import csv
import sys
import math
import pandas as pd
import numpy as np
import matplotlib as mpb
import matplotlib.pyplot as plt
from matplotlib import offsetbox as osb
from matplotlib.patches import RegularPolygon
from datetime import date


from py_data_getter import data_getter
from py_db import db

import helper_data
db = db('nba_shots')

# setting the color map we want to use
mymap = mpb.cm.OrRd

np.seterr(divide='ignore', invalid='ignore')

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


# we set gridNum to be 30 (basically a grid of 30x30 hexagons)
def shooting_plot(dataType, path, shot_df, _id, season_id, _title, _name, isCareer=False, min_year = 0, max_year = 0, plot_size=(24,24), gridNum=30):

    # get the shooting percentage and number of shots for all bins, all shots, and a subset of some shots
    (ShootingPctLocs, shotNumber), shot_count_all = find_shootingPcts(shot_df, gridNum)

    all_efg_percentile = float(helper_data.get_metrics(dataType, _id, season_id, isCareer, 'all', 'EFG_Percentile'))

    color_efg = max(min((all_efg_percentile/100),1.0),0.0)

    paa = float(helper_data.get_metrics(dataType, _id, season_id, isCareer, 'all', 'paa'))

    # set the figure for drawing on
    fig = plt.figure(figsize=(24,24))

    # cmap will be used as our color map going forward
    cmap = mymap

    # where to place the plot within the figure, first two attributes are the x_min and y_min, and the next 2 are the % of the figure that is covered in the x_direction and y_direction (so in this case, our plot will go from (0.05, 0.15) at the bottom left, and stretches to (0.85,0.925) at the top right)
    ax = plt.axes([0.05, 0.15, 0.81, 0.775]) 

    # setting the background color using a hex code (http://www.rapidtables.com/web/color/RGB_Color.htm)
    # ax.set_facecolor('#0C232E')
    ax.set_facecolor('#152535')


    # draw the outline of the court
    draw_court(outer_lines=False)

    # specify the dimensions of the court we draw
    plt.xlim(-250,250)
    plt.ylim(370, -30)
    
    # drawing the bottom right image
    zoom = 1 # we don't need to zoom the image at all
    if dataType == 'player':
        img = acquire_playerPic(_id, zoom)
    else:
        img = acquire_teamPic(season_id, _title, _id, zoom)
    ax.add_artist(img)
             
    # specify the % a zone that we want to correspond to a maximum sized hexagon [I have this set to any zone with >= 1% of all shots will have a maximum radius, but it's free to be changed based on personal preferences]
    max_radius_perc = 1.0
    max_rad_multiplier = 100.0/max_radius_perc

    # changing to what power we want to scale the area of the hexagons as we increase/decrease the radius. This value can also be changed for personal preferences.
    area_multiplier = (3./4.)

    lg_efg = float(helper_data.get_lg_efg(season_id, isCareer))

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
        ax.text(text_x, text_y, text_text, fontsize=16, horizontalalignment='left', verticalalignment='center', family='DejaVu Sans', color='white', fontweight='bold')

    # Add a title to our frequency legend (the x/y coords are hardcoded).
    # Again, the color=map(eff_fg_all_float/100) makes the hexagons in the legend the same color as the player's overall eFG%
    ax.text(-235, 310, 'Zone Frequencies', fontsize=16, horizontalalignment='left', verticalalignment='bottom', family='DejaVu Sans', color=cmap(color_efg), fontweight='bold')

    # Add a title to our chart (just the player's name)
    chart_title = "%s | %s" % (_title.upper(), season_id)
    ax.text(31.25,-40, chart_title, fontsize=32, horizontalalignment='center', verticalalignment='bottom', family='DejaVu Sans', color=cmap(color_efg), fontweight='bold')

    # Add user text
    ax.text(-250,-31,'CHARTS BY CONNOR REED (@NBAChartBot)',
        fontsize=16,  horizontalalignment='left', verticalalignment = 'bottom', family='DejaVu Sans', color='white', fontweight='bold')

    # Add data source text
    ax.text(31.25,-31,'DATA FROM STATS.NBA.COM',
        fontsize=16,  horizontalalignment='center', verticalalignment = 'bottom', family='DejaVu Sans', color='white', fontweight='bold')

    # Add date text
    _date = date.today()

    ax.text(250,-31,'AS OF %s' % (str(_date)),
        fontsize=16,  horizontalalignment='right', verticalalignment = 'bottom', family='DejaVu Sans', color='white', fontweight='bold')


    key_text = get_key_text(dataType, _id, season_id, isCareer)
    # adding breakdown of eFG% by shot zone at the bottom of the chart
    ax.text(307,380, key_text, fontsize=20, horizontalalignment='right', verticalalignment = 'top', family='DejaVu Sans', color='white', linespacing=1.5)

    if dataType == 'player':
        teams_text, team_len = get_teams_text(_id, season_id, isCareer)
    else:
        teams_text = _title
        team_len = 0

    # adding which season the chart is for, as well as what teams the player is on
    if team_len > 12:
        ax.text(-250,380, season_id + ' Regular Season:\n' + teams_text,
            fontsize=20,  horizontalalignment='left', verticalalignment = 'top', family='DejaVu Sans', color='white', linespacing=1.4)
    else:
        ax.text(-250,380, season_id + ' Regular Season:\n' + teams_text,
            fontsize=20,  horizontalalignment='left', verticalalignment = 'top', family='DejaVu Sans', color='white', linespacing=1.6)

    # adding a color bar for reference
    ax2 = fig.add_axes([0.875, 0.15, 0.04, 0.775])
    cb = mpb.colorbar.ColorbarBase(ax2,cmap=cmap, orientation='vertical')
    cbytick_obj = plt.getp(cb.ax.axes, 'yticklabels')
    plt.setp(cbytick_obj, color='white', fontweight='bold',fontsize=16)
    cb.set_label('EFG+ (100 is League Average)', family='DejaVu Sans', color='white', fontweight='bold', labelpad=-4, fontsize=24)
    cb.set_ticks([0.0, 0.25, 0.5, 0.75, 1.0])
    cb.set_ticklabels(['$\mathbf{\leq}$50','75', '100','125', '$\mathbf{\geq}$150'])

    figtit = path+'%s(%s)_%s.png' % (_name, _id, season_id.replace(' ','').replace('POST-1996',''))
    plt.savefig(figtit, facecolor='#2E3748', edgecolor='black')
    plt.clf()


#Producing the text for the bottom of the shot chart
def get_key_text(dataType, _id, season_id, isCareer, isTwitter=False):

    text = ''

    total_atts = ("%.0f" % helper_data.get_metrics(dataType, _id, season_id, isCareer, 'all', 'r.attempts'))
    total_makes = ("%.0f" % helper_data.get_metrics(dataType, _id, season_id, isCareer, 'all', 'b.makes'))
    total_games = ("%.0f" % helper_data.get_metrics(dataType, _id, season_id, isCareer, 'all', 'r.games'))
    total_attPerGame = ("%.1f" % helper_data.get_metrics(dataType, _id, season_id, isCareer, 'all', 'r.attempts/r.games'))
    vol_percentile = ("%.0f" % helper_data.get_metrics(dataType, _id, season_id, isCareer, 'all', 'AttemptsPerGame_percentile'))
    vol_word = helper_data.get_text_description('AttemptsPerGame', vol_percentile)
    vol_text = '$\mathbf{' + vol_word.upper() + '}$ Volume | ' + str(total_makes) + ' for ' + str(total_atts) + ' in ' + str(total_games) + ' Games | ' + str(total_attPerGame) + ' FGA/Game, $\mathbf{P_{' + str(vol_percentile) + '}}$'
    vol_twitter_text = 'Volume: ' + vol_word.upper() + ' | P_' + str(vol_percentile) + ' (percentile)'


    shotSkillPlus = ("%.1f" % helper_data.get_metrics(dataType, _id, season_id, isCareer, 'All', 's.ShotSkillPlus'))
    shotSkill_percentile = ("%.0f" % helper_data.get_metrics(dataType, _id, season_id, isCareer, 'all', 'shotSkill_Percentile'))
    shotSkill_word = helper_data.get_text_description('shotSkill', shotSkill_percentile)
    shotSkill_text = '$\mathbf{' + shotSkill_word.upper() + '}$ Shot Skill | ' + str(shotSkillPlus) + ' ShotSkill+, $\mathbf{P_{' + str(shotSkill_percentile) + '}}$'
    shotSkill_twitter_text = 'Shot Skill: ' + shotSkill_word.upper() + ' | P_' + str(shotSkill_percentile)


    efg = ("%.1f" % helper_data.get_metrics(dataType, _id, season_id, isCareer, 'All', 'd.efg*100'))
    efgPlus = ("%.1f" % helper_data.get_metrics(dataType, _id, season_id, isCareer, 'All', 'r.efg_plus'))
    efg_percentile = ("%.0f" % helper_data.get_metrics(dataType, _id, season_id, isCareer, 'all', 'EFG_Percentile'))
    efg_word = helper_data.get_text_description('EFG', efg_percentile)
    efg_text = '$\mathbf{' + efg_word.upper() + '}$ Efficiency | ' + str(efg) + ' EFG% | ' + str(efgPlus) + ' EFG+, $\mathbf{P_{' + str(efg_percentile) + '}}$'
    efg_twitter_text = 'Efficiency: ' + efg_word.upper() + ' | P_' + str(efg_percentile)


    PAA = ("%.1f" % helper_data.get_metrics(dataType, _id, season_id, isCareer, 'All', 'r.paa'))
    PAAperGame = ("%.1f" % helper_data.get_metrics(dataType, _id, season_id, isCareer, 'All', 'r.paa_per_game'))
    PAA_percentile = ("%.0f" % helper_data.get_metrics(dataType, _id, season_id, isCareer, 'all', 'PAAperGame_percentile'))
    PAA_word = helper_data.get_text_description('PAAperGame', PAA_percentile)
    PAA_text = '$\mathbf{' + PAA_word.upper() + '}$ Efficiency Value Added | ' + str(PAA) + ' Total PAA | ' + str(PAAperGame) + ' PAA/Game, $\mathbf{P_{' + str(PAA_percentile) + '}}$'
    PAA_twitter_text = 'Efficiency Value: ' + PAA_word.upper() + ' | P_' + str(PAA_percentile)


    fav_zone, fav_zoneVal = helper_data.get_extreme_zones(dataType, _id, season_id, isCareer, 'positive', 'ROUND(zone_pct_plus-100,0)')
    if fav_zoneVal >= 0:
        fav_zoneTextAdd = "+"
    else:
        fav_zoneTextAdd = ""
    fav_zoneTEXT = '$\mathbf{Favorite Zone}$ (Relative to League Averages) -- $\mathbf{' + str(fav_zone) + '}$ (' + str(fav_zoneTextAdd) + str(fav_zoneVal) + '% distribution)'
    fav_twitter_zoneTEXT = 'Favorite Zone: ' + str(fav_zone)


    skill_zone, skill_zoneVal = helper_data.get_extreme_zones(dataType, _id, season_id, isCareer, 'positive', 'ROUND(zone_efg_plus-100,0)')
    if skill_zoneVal >= 0:
        skill_zoneTextAdd = 'above'
    else:
        skill_zoneTextAdd = 'below'
    skill_zoneTEXT = '$\mathbf{Best Skill}$ -- $\mathbf{' + str(skill_zone) + '}$ (' + str(abs(skill_zoneVal)) + '% ' + str(skill_zoneTextAdd) + ' average)'
    skill_twitter_zoneTEXT = 'Best Skill Zone: ' + str(skill_zone)


    value_zone, value_zoneVal = helper_data.get_extreme_zones(dataType, _id, season_id, isCareer, 'positive', 'ROUND(paa, 0)')
    if value_zoneVal >= 0:
        value_zoneTextAdd = "+"
    else:
        value_zoneTextAdd = ""
    value_zoneTEXT = '$\mathbf{Best Value}$ -- $\mathbf{' + str(value_zone) + '}$ (' + str(value_zoneTextAdd) + str(value_zoneVal) + ' PAA)'
    value_twitter_zoneTEXT = 'Best Value Zone: ' + str(value_zone)


    LEASTskill_zone, LEASTskill_zoneVal = helper_data.get_extreme_zones(dataType, _id, season_id, isCareer, 'negative', 'ROUND(zone_efg_plus-100,0)')
    if LEASTskill_zoneVal >= 0:
        LEASTskill_zoneTextAdd = 'above'
    else:
        LEASTskill_zoneTextAdd = 'below'
    LEASTskill_zoneTEXT = '$\mathbf{Worst Skill}$ -- $\mathbf{' + str(LEASTskill_zone) + '}$ (' + str(abs(LEASTskill_zoneVal)) + '% ' + str(LEASTskill_zoneTextAdd) + ' average)'


    LEASTvalue_zone, LEASTvalue_zoneVal = helper_data.get_extreme_zones(dataType, _id, season_id, isCareer, 'negative', 'ROUND(paa, 0)')
    if LEASTvalue_zoneVal >= 0:
        LEASTvalue_zoneTextAdd = "+"
    else:
        LEASTvalue_zoneTextAdd = ""
    LEASTvalue_zoneTEXT = '$\mathbf{Least Value}$ -- $\mathbf{' + str(LEASTvalue_zone) + '}$ (' + str(LEASTvalue_zoneTextAdd) + str(LEASTvalue_zoneVal) + ' PAA)'


    if isTwitter is False:
        text += vol_text
        text += '\n'+shotSkill_text
        text += '\n'+efg_text
        text += '\n'+PAA_text
        text += '\n'+fav_zoneTEXT
        text += '\n'+skill_zoneTEXT
        text += ' | '+value_zoneTEXT
        text += '\n'+LEASTskill_zoneTEXT
        text += ' | '+LEASTvalue_zoneTEXT

    else:
        text += ':\n\n'+vol_twitter_text
        text += '\n'+shotSkill_twitter_text
        text += '\n'+efg_twitter_text
        text += '\n'+PAA_twitter_text
        text += '\n\n'+fav_twitter_zoneTEXT
        text += '\n'+skill_twitter_zoneTEXT
        text += '\n'+value_twitter_zoneTEXT

    return text



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


#Getting the player picture that we will later place in the chart
#Most of this code was recycled from Savvas Tjortjoglou [http://savvastjortjoglou.com] 
def acquire_playerPic(player_id, zoom, offset=(250,370)):
    try:
        img_path = os.getcwd()+'/'+str(player_id)+'.png'
        player_pic = plt.imread(img_path)
    except (ValueError,IOError):
        try:
            pic = urllib.urlretrieve("https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/"+str(player_id)+".png",str(player_id)+".png")

            player_pic = plt.imread(pic[0])
        except (ValueError, IOError):
            try:
                pic = urllib.urlretrieve("http://stats.nba.com/media/players/230x185/"+str(player_id)+".png",str(player_id)+".png")
                player_pic = plt.imread(pic[0])
            except (ValueError, IOError):
                img_path = os.getcwd()+'/chart_icon.png'
                player_pic = plt.imread(img_path)      


    img = osb.OffsetImage(player_pic, zoom)
    img = osb.AnnotationBbox(img, offset,xycoords='data',pad=0.0, box_alignment=(1,0), frameon=False)
    return img


#Getting the team picture that we will later place in the chart
def acquire_teamPic(season_id, team_title, team_id, zoom, offset=(250,370)):
    abb_file = os.getcwd()+"/../csvs/team_abbreviations.csv"
    abb_list = {}
    with open(abb_file, 'rU') as f:
        mycsv = csv.reader(f)
        for row in mycsv:
            team, abb, imgurl = row
            abb_list[team] = [abb, imgurl]

    img_url = abb_list.get(team_title)[1]
    try:
        img_path = os.getcwd()+'/'+str(team_id)+'.png'
        team_pic = plt.imread(img_path)
    except IOError:
        try:
            pic = urllib.urlretrieve(img_url,str(team_id)+'.png')
            team_pic = plt.imread(pic[0])
        except (ValueError, IOError):
            img_path = os.getcwd()+'/nba_logo.png'
            player_pic = plt.imread(img_path)    

    img = osb.OffsetImage(team_pic, zoom)
    img = osb.AnnotationBbox(img, offset,xycoords='data',pad=0.0, box_alignment=(1,0), frameon=False)
    return img


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
    # raw_input(team_qry)

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
            if i%3 == 0 and i > 0:
                team_text += '\n'
            text_add = '%s, ' % str(team)
            team_text += text_add
            i += 1
        if i%3 == 0:
            team_text += '\n'
        # raw_input(team_list)
        team_text += str(team_list[-1])

    return team_text, len(team_list)
