import requests
import urllib
import os
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
from datetime import date


# setting the color map we want to use
mymap = mpb.cm.YlOrRd

# taking in a dictionary of player information and initializing the processes
def initiate(p_list):
    # setting our base directory (this will be different for each user)
    base_path = "/Users/connordog/Dropbox/Desktop_Files/Work_Things/CodeBase/Python_Scripts/Python_Projects/nba_shot_charts/"

    # iterating through our player dictionary to grab the player_title and player_id
    for player_title, player_data in p_list.items():
        player_id, start_year, end_year = player_data

        player_name = player_title.replace(" ","_")

        # defines a path to a directory for saving the charts of the current player
        path = base_path+'shot_charts/'+player_name+'/'

        # checks if our desired directory exists, and if not, creates it
        if not os.path.exists(path):
            os.makedirs(path)

        # deletes previous versions of images
        os.chdir(path)
        files=glob.glob('*.png')
        for filename in files:
            os.unlink(filename)
        os.chdir(base_path)

        # We set a min and max year to later overwrite (for usage in noting a player's career length)
        min_year = 9999
        max_year = 0

        # we set an empty DataFrame and will append each year's shots, creating a career shot log
        all_shots_df = pd.DataFrame()

        # we iterate through each year of a player's career, creating a shot chart for every year while also adding each season's data to our all_shots_df DataFrame
        for year in range(start_year,end_year):
            season_start = year

            # takes a season (e.g. 2008) and returns the nba ID (e.g. 2008-09)
            season_id = str(season_start)+'-'+str(season_start%100+1).zfill(2)[-2:]

            # we print the season/player combo in order to monitor progress
            print season_id, player_name

            # a DataFrame of the shots a player took in a given season
            year_shots_df = acquire_shootingData(player_id, season_id)

            # if the DataFrame isn't empty (i.e., if the player played this season), we make a shot chart for this season as well as append the career DataFrame for the player and overwrite the current min_year and max_year variables
            if year_shots_df is not None and len(year_shots_df.index) != 0:
                
                if year < min_year:
                    min_year = year

                if (year+1) > max_year:
                    max_year = (year+1)

                # plotting the data for the given season/player combination we are iterating through
                shooting_plot(path, year_shots_df, player_id, season_id, player_title, player_name)

                # appending the career shots DataFrame
                all_shots_df = all_shots_df.append(year_shots_df, ignore_index=True)

        # making a text string for usage in the career shot chart
        career_string = "CAREER (%s-%s)" % (min_year, max_year)
        print '\t\t', career_string, player_name

        # making a shot chart for all shots in the player's career. note that we have to use the option isCareer, min_year, and max_year arguments to properly format this chart
        shooting_plot(path, all_shots_df, player_id, career_string, player_title, player_name, isCareer=True, min_year=min_year, max_year=max_year)

    # after we finish the script, we remove all the player images that were saved to the directory during the acquire_playerPic function
    os.chdir(base_path)
    files=glob.glob('*.png')
    for filename in files:
        os.unlink(filename)


# we set gridNum to be 30 (basically a grid of 30x30 hexagons)
def shooting_plot(path, shot_df, player_id, season_id, player_title, player_name, isCareer=False, min_year = 0, max_year = 0, plot_size=(12,12), gridNum=30):

    # get the shooting percentage and number of shots for all bins, all shots, and a subset of some shots
    (ShootingPctLocs, shotNumber), shot_pts_all, shot_pts_3, shot_pts_2, shot_pts_mid, shot_pts_NONres, shot_pts_res, shot_count_all, shot_count_3, shot_count_2, shot_count_mid, shot_count_NONres, shot_count_res, team_list = find_shootingPcts(shot_df, gridNum)

    # returns the effective FG% values for usage later in the chart's text
    def get_efg(shot_pts, shot_count):
        try:
            eff_fg_float = float((float(shot_pts)/2.0)/float(shot_count))*100.0
        except ZeroDivisionError:
            eff_fg_float = 0.0
        eff_fg = ("%.2f" % eff_fg_float)
        pct_float = float(shot_count)/float(shot_count_all)*100
        pct = ("%.2f" % pct_float)

        return eff_fg_float, eff_fg, pct_float, pct

    eff_fg_all_float, eff_fg_all, pct_all_float, pct_all = get_efg(shot_pts_all, shot_count_all)
    eff_fg_3_float, eff_fg_3, pct_3_float, pct_3 = get_efg(shot_pts_3, shot_count_3)
    eff_fg_2_float, eff_fg_2, pct_2_float, pct_2 = get_efg(shot_pts_2, shot_count_2)
    eff_fg_mid_float, eff_fg_mid, pct_mid_float, pct_mid = get_efg(shot_pts_mid, shot_count_mid)
    eff_fg_NONres_float, eff_fg_NONres, pct_NONres_float, pct_NONres = get_efg(shot_pts_NONres, shot_count_NONres)
    eff_fg_res_float, eff_fg_res, pct_res_float, pct_res = get_efg(shot_pts_res, shot_count_res)

    # Creates a text string for all teams that a player has played on in a given season or career
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

    # set the figure for drawing on
    fig = plt.figure(figsize=(12,12))

    # cmap will be used as our color map going forward
    cmap = mymap

    # where to place the plot within the figure, first two attributes are the x_min and y_min, and the next 2 are the % of the figure that is covered in the x_direction and y_direction (so in this case, our plot will go from (0.05, 0.0125) at the bottom left, and stretches to (0.85,0.925) at the top right)
    ax = plt.axes([0.05, 0.125, 0.81, 0.81]) 

    # setting the background color using a hex code (http://www.rapidtables.com/web/color/RGB_Color.htm)
    ax.set_axis_bgcolor('#08374B')

    # draw the outline of the court
    draw_court(outer_lines=False)

    # specify the dimensions of the court we draw
    plt.xlim(-250,250)
    plt.ylim(420, -30)
    
    # draw player image
    zoom = 1 # we don't need to zoom the image at all
    img = acquire_playerPic(player_id, zoom)
    ax.add_artist(img)
             
    # specify the % a zone that we want to correspond to a maximum sized hexagon [I have this set to any zone with >= 1% of all shots will have a maximum radius, but it's free to be changed based on personal preferences]
    max_radius_perc = 1.0
    max_rad_multiplier = 100.0/max_radius_perc

    # changing to what power we want to scale the area of the hexagons as we increase/decrease the radius. This value can also be changed for personal preferences.
    area_multiplier = (3./4.)

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
        bin_pct = min(shots*mult, 1.0) 
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
        patch_y = 415-(14*i)

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
        patch = RegularPolygon(patch_axes, numVertices=6, radius=patch_rad, color=cmap(eff_fg_all_float/100), alpha=0.95, fill=True)
        ax.add_patch(patch)

        # add the text for the hexagon
        ax.text(text_x, text_y, text_text, fontsize=12, horizontalalignment='left', verticalalignment='center', family='Bitstream Vera Sans', color='white', fontweight='bold')

    # Add a title to our frequency legend (the x/y coords are hardcoded).
    # Again, the color=map(eff_fg_all_float/100) makes the hexagons in the legend the same color as the player's overall eFG%
    ax.text(-235, 360, 'Zone Frequencies', fontsize = 15, horizontalalignment='left', verticalalignment='bottom', family='Bitstream Vera Sans', color=cmap(eff_fg_all_float/100), fontweight='bold')

    # Add a title to our chart (just the player's name)

    chart_title = "%s" % (player_title.upper())
    ax.text(31.25,-40, chart_title, fontsize=29, horizontalalignment='center', verticalalignment='bottom', family='Bitstream Vera Sans', color=cmap(eff_fg_all_float/100), fontweight='bold')

    # Add user text
    ax.text(-250,-31,'CHARTS BY CONNOR REED',
        fontsize=8,  horizontalalignment='left', verticalalignment = 'bottom', family='Bitstream Vera Sans', color='white', fontweight='bold')

    # Add data source text
    ax.text(31.25,-31,'DATA FROM STATS.NBA.COM',
        fontsize=8,  horizontalalignment='center', verticalalignment = 'bottom', family='Bitstream Vera Sans', color='white', fontweight='bold')

    # Add date text
    ax.text(250,-31,'AS OF %s' % (str(date.today())),
        fontsize=8,  horizontalalignment='right', verticalalignment = 'bottom', family='Bitstream Vera Sans', color='white', fontweight='bold')


    # adding breakdown of eFG% by shot zone at the bottom of the chart
    ax.text(250,430, '%s Points - %s Shots [TOTAL (%s%% of total)] (%s eFG%%)'
        '\n%s Points - %s Shots [All 3PT (%s%%)] (%s eFG%%)'
        '\n%s Points - %s Shots [All 2PT (%s%%)] (%s eFG%%)'
        '\n%s Points - %s Shots [Mid-Range (%s%%)] (%s eFG%%)'
        '\n%s Points - %s Shots [Paint (Non-Restricted) (%s%%)] (%s eFG%%)'
        '\n%s Points - %s Shots [Paint (Restricted) (%s%%)] (%s eFG%%)' % (shot_pts_all, shot_count_all, pct_all, eff_fg_all, shot_pts_3, shot_count_3, pct_3, eff_fg_3, shot_pts_2, shot_count_2, pct_2, eff_fg_2, shot_pts_mid, shot_count_mid, pct_mid, eff_fg_mid, shot_pts_NONres, shot_count_NONres, pct_NONres, eff_fg_NONres, shot_pts_res, shot_count_res, pct_res, eff_fg_res),
        fontsize=10, horizontalalignment='right', verticalalignment = 'top', family='Bitstream Vera Sans', color='white', linespacing=1.5)

    # adding which season the chart is for, as well as what teams the player is on
    ax.text(-250,430,'%s Regular Season'
        '\n%s' % (season_id, team_text),
        fontsize=10,  horizontalalignment='left', verticalalignment = 'top', family='Bitstream Vera Sans', color='white', linespacing=1.5)

    # adding a color bar for reference
    ax2 = fig.add_axes([0.875, 0.125, 0.04, 0.81])
    cb = mpb.colorbar.ColorbarBase(ax2,cmap=cmap, orientation='vertical')
    cbytick_obj = plt.getp(cb.ax.axes, 'yticklabels')
    plt.setp(cbytick_obj, color='white', fontweight='bold')
    cb.set_label('Effective Field Goal %', family='Bitstream Vera Sans', color='white', fontweight='bold', labelpad=-9)
    cb.set_ticks([0.0, 0.25, 0.5, 0.75, 1.0])
    cb.set_ticklabels(['0%','25%', '50%','75%', '$\mathbf{\geq}$100%'])
    
    # if the isCareer argument is set to True, we have to slightly alter the title of the plot
    if isCareer is False:
        figtit= path+'shot_charts_%s_%s_%s.png' % (player_name, season_id, str(int(eff_fg_all_float)))
    else:
        figtit = path+'shot_charts_%s_CAREER_%s-%s_%s.png' % (player_name, min_year, max_year, str(int(eff_fg_all_float)))
    plt.savefig(figtit, facecolor='#305E72', edgecolor='black')
    plt.clf()


#Getting the shooting percentages for each grid.
#The general idea of this function, as well as a substantial block of the actual code was recycled from Dan Vatterott [http://www.danvatterott.com/]
def find_shootingPcts(shot_df, gridNum):
    x = shot_df.LOC_X[shot_df['LOC_Y']<425.1]
    y = shot_df.LOC_Y[shot_df['LOC_Y']<425.1]
    
    # Grabbing the x and y coords, for all made shots
    x_made = shot_df.LOC_X[(shot_df['SHOT_MADE_FLAG']==1) & (shot_df['LOC_Y']<425.1)]
    y_made = shot_df.LOC_Y[(shot_df['SHOT_MADE_FLAG']==1) & (shot_df['LOC_Y']<425.1)]

    # Recording the point value of each made shot
    shot_pts = 2*((shot_df['SHOT_MADE_FLAG']==1) & (shot_df['SHOT_TYPE']=='2PT Field Goal')) + 3*((shot_df['SHOT_MADE_FLAG']==1) & (shot_df['SHOT_TYPE']=='3PT Field Goal'))

    # Recording the team name of a player for each made shot
    shot_teams = (shot_df['TEAM_NAME'])
    # Dropping all the duplicate entries for the team names
    teams = shot_teams.drop_duplicates()

    # Grabbing all points made from different shot locations, as well as counting all times a shot was missed from that zone
    pts_3 = 3*((shot_df['SHOT_MADE_FLAG']==1) & (shot_df['SHOT_TYPE']=='3PT Field Goal'))
    miss_3 = 1*((shot_df['SHOT_MADE_FLAG']==0) & (shot_df['SHOT_TYPE']=='3PT Field Goal'))
    pts_2 = 2*((shot_df['SHOT_MADE_FLAG']==1) & (shot_df['SHOT_TYPE']=='2PT Field Goal'))
    miss_2 = 1*((shot_df['SHOT_MADE_FLAG']==0) & (shot_df['SHOT_TYPE']=='2PT Field Goal'))
    pts_mid = 2*((shot_df['SHOT_MADE_FLAG']==1) & (shot_df['SHOT_ZONE_BASIC']=='Mid-Range'))
    miss_mid = 1*((shot_df['SHOT_MADE_FLAG']==0) & (shot_df['SHOT_ZONE_BASIC']=='Mid-Range'))
    pts_NONrestricted = 2*((shot_df['SHOT_MADE_FLAG']==1) & (shot_df['SHOT_ZONE_BASIC']=='In The Paint (Non-RA)'))
    miss_NONrestricted = 1*((shot_df['SHOT_MADE_FLAG']==0) & (shot_df['SHOT_ZONE_BASIC']=='In The Paint (Non-RA)'))
    pts_restricted = 2*((shot_df['SHOT_MADE_FLAG']==1) & (shot_df['SHOT_ZONE_BASIC']=='Restricted Area'))
    miss_restricted = 1*((shot_df['SHOT_MADE_FLAG']==0) & (shot_df['SHOT_ZONE_BASIC']=='Restricted Area'))
    
    #compute number of shots made and taken from each hexbin location
    hb_shot = plt.hexbin(x, y, gridsize=gridNum, extent=(-250,250,425,-50));
    plt.close()
    hb_made = plt.hexbin(x_made, y_made, gridsize=gridNum, extent=(-250,250,425,-50));
    plt.close()
    
    #compute shooting percentage
    ShootingPctLocs = hb_made.get_array() / hb_shot.get_array()
    ShootingPctLocs[np.isnan(ShootingPctLocs)] = 0 #makes 0/0s=0

    # creating a list of all teams a player played for in a given season/career
    team_list = []
    for team in teams:
        team_list.append(team)

    # Summing all made points from the shot zones
    shot_pts_all = sum(shot_pts)
    shot_pts_3 = sum(pts_3)
    shot_pts_2 = sum(pts_2)
    shot_pts_mid = sum(pts_mid)
    shot_pts_NONres = sum(pts_NONrestricted)
    shot_pts_res = sum(pts_restricted)

    # Counting the total number of shots from the shot zones
    shot_count_all = len(shot_df.index)
    shot_count_3 = sum(miss_3) + sum(pts_3)/3
    shot_count_2 = sum(miss_2) + sum(pts_2)/2
    shot_count_mid = sum(miss_mid) + sum(pts_mid)/2
    shot_count_NONres = sum(miss_NONrestricted) + sum(pts_NONrestricted)/2
    shot_count_res = sum(miss_restricted) + sum(pts_restricted)/2

    # Returning all values
    return (ShootingPctLocs, hb_shot), shot_pts_all, shot_pts_3, shot_pts_2, shot_pts_mid, shot_pts_NONres, shot_pts_res, shot_count_all, shot_count_3, shot_count_2, shot_count_mid, shot_count_NONres, shot_count_res, team_list


#Getting the shot data and returning a DataFrame with every shot for a specific player/season combo
def acquire_shootingData(player_id,season):
    import requests
    shot_chart_temp = 'http://stats.nba.com/stats/shotchartdetail?CFID=33&CFPARAMS=%s&ContextFilter=&ContextMeasure=FGA&DateFrom=&DateTo=&GameID=&GameSegment=&LastNGames=0&LeagueID=00&Location=&MeasureType=Base&Month=0&OpponentTeamID=0&Outcome=&PaceAdjust=N&PerMode=PerGame&Period=0&PlayerID=%s&PlusMinus=N&PlayerPosition=&Rank=N&RookieYear=&Season=%s&SeasonSegment=&SeasonType=Regular+Season&TeamID=0&VsConference=&VsDivision=&mode=Advanced&showDetails=0&showShots=1&showZones=0'
    shot_chart_url = shot_chart_temp % (season, player_id, season)

    # print shot_chart_url
    # user agent makes it seem as though we're an actual user getting the data
    user_agent = 'User-Agent:Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36'
    response = requests.get(shot_chart_url, headers={'User-Agent': user_agent})

    # headers is the column titles for our DataFrame
    headers = response.json()['resultSets'][0]['headers']

    # shots will be each row in the DataFrame
    shots = response.json()['resultSets'][0]['rowSet']

    # if there were no shots at that URL, we return nothing
    if shots == []:
        return

    # creating our DataFrame from our shots and headers variables
    shot_df = pd.DataFrame(shots, columns=headers)
    return shot_df


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
    corner_three_a = Rectangle((-220, -47.5), 0, 140, linewidth=lw,
                               color=color)
    corner_three_b = Rectangle((220, -47.5), 0, 140, linewidth=lw, color=color)
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


#Getting the player picture that we will later place in the chart
#Most of this code was recycled from Savvas Tjortjoglou [http://savvastjortjoglou.com] 
def acquire_playerPic(player_id, zoom, offset=(250,420)):
    from matplotlib import  offsetbox as osb
    import urllib
    pic = urllib.urlretrieve("http://stats.nba.com/media/players/230x185/"+str(player_id)+".png",str(player_id)+".png")
    player_pic = plt.imread(pic[0])
    img = osb.OffsetImage(player_pic, zoom)
    img = osb.AnnotationBbox(img, offset,xycoords='data',pad=0.0, box_alignment=(1,0), frameon=False)
    return img


if __name__ == "__main__": 

    # a list of interesting players/player_id's that I want to generate shot charts for
    p_list = {
        'Aaron Gordon':[203932,2014,2017],
        'Al Horford':[201143,2007,2017],
        'Alec Burks':[202692,2011,2017],
        'Allen Crabbe':[203459,2013,2017],
        'Allen Iverson':[947,1996,2010],
        'Amar\'e Stoudemire':[2405,2002,2017],
        'Anderson Varejao':[2760,2004,2017],
        'Andre Drummond':[203083,2012,2017],
        'Andre Iguodala':[2738,2004,2017],
        'Andre Roberson':[203460,2013,2017],
        'Andrei Kirilenko':[1905,2001,2015],
        'Andrew Wiggins':[203952,2014,2017],
        'Antawn Jamison':[1712,1998,2014],
        'Anthony Bennett':[203461,2013,2017],
        'Anthony Davis':[203076,2012,2017],
        'Anthony Morrow':[201627,2008,2017],
        'Anthony Tolliver':[201229,2008,2017],
        'Antoine Walker':[952,1996,2008],
        'Austin Rivers':[203085,2012,2017],
        'Avery Bradley':[202340,2010,2017],
        'Baron Davis':[1884,2001,2012],
        'Bismack Biyombo':[202687,2011,2017],
        'Blake Griffin':[201933,2010,2017],
        'Boban Marjanovic':[1626246,2015,2017],
        'Boris Diaw':[2564,2003,2017],
        'Bradley Beal':[203078,2012,2017],
        'Brandon Ingram':[1627742,2016,2017],
        'Brandon Knight':[202688,2011,2017],
        'Brandon Roy':[200750,2006,2013],
        'Brook Lopez':[201572,2008,2017],
        'Bruno Caboclo':[203998,2014,2017],
        'Buddy Hield':[1627741,2016,2017],
        'C.J. McCollum':[203468,2013,2017],
        'Cameron Payne':[1626166,2015,2017],
        'Carmelo Anthony':[2546,2003,2017],
        'Chandler Parsons':[202718,2011,2017],
        'Channing Frye':[101112,2005,2017],
        'Chris Bosh':[2547,2003,2017],
        'Chris Paul':[101108,2005,2017],
        'Chris Webber':[185,1996,2008],
        'Clint Capela':[203991,2014,2017],
        'Cody Zeller':[203469,2013,2017],
        'Corey Brewer':[201147,2007,2017],
        'Cory Joseph':[202709,2011,2017],
        'Courtney Lee':[201584,2008,2017],
        'D\'Angelo Russell':[1626156,2015,2017],
        'Damian Jones':[1627745,2016,2017],
        'Damian Lillard':[203081,2012,2017],
        'Danilo Gallinari':[201568,2008,2017],
        'Danny Green':[201980,2009,2017],
        'Dante Exum':[203957,2014,2017],
        'Dario Saric':[203967,2014,2017],
        'David Lee':[101135,2005,2017],
        'David West':[2561,2003,2017],
        'DeAndre Jordan':[201599,2008,2017],
        'DeAndre Liggins':[202732,2011,2017],
        'Dejounte Murray':[1627749,2016,2017],
        'DeMar DeRozan':[201942,2009,2017],
        'DeMarcus Cousins':[202326,2010,2017],
        'DeMarre Carroll':[201960,2009,2017],
        'Dennis Schroder':[203471,2013,2017],
        'Denzel Valentine':[1627756,2016,2017],
        'Deron Williams':[101114,2005,2017],
        'Derrick Favors':[202324,2010,2017],
        'Derrick Rose':[201565,2008,2017],
        'Devin Booker':[1626164,2015,2017],
        'Dewayne Dedmon':[203473,2013,2017],
        'Deyonta Davis':[1627738,2016,2017],
        'Dion Waiters':[203079,2012,2017],
        'Dirk Nowitzki':[1717,1998,2017],
        'Domantas Sabonis':[1627734,2016,2017],
        'Dorian Finney-Smith':[1627827,2016,2017],
        'Doug McDermott':[203926,2014,2017],
        'Dragan Bender':[1627733,2016,2017],
        'Draymond Green':[203110,2012,2017],
        'Dwight Howard':[2730,2004,2017],
        'Dwight Powell':[203939,2014,2017],
        'Dwyane Wade':[2548,2003,2017],
        'Ed Davis':[202334,2010,2017],
        'Elfrid Payton':[203901,2014,2017],
        'Emmanuel Mudiay':[1626144,2015,2017],
        'Enes Kanter':[202683,2011,2017],
        'Eric Bledsoe':[202339,2010,2017],
        'Eric Gordon':[201569,2008,2017],
        'Ersan Ilyasova':[101141,2006,2017],
        'Evan Fournier':[203095,2012,2017],
        'Evan Turner':[202323,2010,2017],
        'Frank Kaminsky':[1626163,2015,2017],
        'George Hill':[201588,2008,2017],
        'Giannis Antetokounmpo':[203507,2013,2017],
        'Goran Dragic':[201609,2008,2017],
        'Gordon Hayward':[202330,2010,2017],
        'Greg Monroe':[202328,2010,2017],
        'Greg Oden':[201141,2008,2014],
        'Harrison Barnes':[203084,2012,2017],
        'Hassan Whiteside':[202355,2010,2017],
        'Ian Clark':[203546,2013,2017],
        'Iman Shumpert':[202697,2011,2017],
        'Isaiah Thomas':[202738,2011,2017],
        'Ish Smith':[202397,2010,2017],
        'J.J. Barea':[200826,2006,2017],
        'J.J. Redick':[200755,2006,2017],
        'J.R. Smith':[2747,2004,2017],
        'Jaahil Okafor':[1626143,2015,2017],
        'Jabari Parker':[203953,2014,2017],
        'Jae Crowder':[203109,2012,2017],
        'Jake Layman':[1627774,2016,2017],
        'Jakob Poeltl':[1627751,2016,2017],
        'Jamal Crawford':[2037,2000,2017],
        'Jamal Murray':[1627750,2016,2017],
        'James Harden':[201935,2009,2017],
        'James Johnson':[201949,2009,2017],
        'James Michael McAdoo':[203949,2014,2017],
        'JaMychal Green':[203210,2014,2017],
        'Jared Dudley':[201162,2007,2017],
        'Jared Sullinger':[203096,2012,2017],
        'Jason Richardson':[2202,2001,2017],
        'Jason Terry':[1891,1999,2017],
        'Jason Williams':[1715,1998,2017],
        'JaVale McGee':[201580,2008,2017],
        'Jaylen Brown':[1627759,2016,2017],
        'Jeff Green':[201145,2007,2017],
        'Jeff Teague':[201952,2009,2017],
        'Jerami Grant':[203924,2014,2017],
        'Jeremy Lin':[202391,2010,2017],
        'Jerian Grant':[1626170,2015,2017],
        'Jimmy Butler':[202710,2011,2017],
        'Joe Ingles':[204060,2014,2017],
        'Joe Johnson':[2207,2001,2017],
        'Joel Embiid':[203954,2016,2017],
        'John Wall':[202322,2010,2017],
        'Jonas Valanciunas':[202685,2012,2017],
        'Jonathan Simmons':[203613,2015,2017],
        'Jordan Clarkson':[203903,2014,2017],
        'Josh Richardson':[1626196,2015,2017],
        'Jrue Holiday':[201950,2009,2017],
        'Julius Randle':[203944,2014,2017],
        'Justice Winslow':[1626163,2015,2017],
        'Justin Anderson':[1626147,2015,2017],
        'Justin Holiday':[203200,2012,2017],
        'Jusuf Nurkic':[203994,2014,2017],
        'K.J. McDaniels':[203909,2014,2017],
        'Karl-Anthony Towns':[1626157,2015,2017],
        'Kawhi Leonard':[202695,2011,2017],
        'Kemba Walker':[202689,2011,2017],
        'Kenneth Farier':[202703,2011,2017],
        'Kent Bazemore':[203145,2012,2017],
        'Kentavious Caldwell-Pope':[203484,2013,2017],
        'Kevin Durant':[201142,2007,2017],
        'Kevin Garnett':[708,1996,2016],
        'Kevin Love':[201567,2008,2017],
        'Kevon Looney':[1626172,2015,2017],
        'Khris Middleton':[203114,2012,2017],
        'Klay Thompson':[202691,2011,2017],
        'Kobe Bryant':[977,1996,2016],
        'Kosta Koufos':[201585,2008,2017],
        'Kris Dunn':[1627739,2016,2017],
        'Kristaps Porzingis':[204001,2015,2017],
        'Kyle Anderson':[203937,2014,2017],
        'Kyle Korver':[2594,2003,2017],
        'Kyle Lowry':[200768,2006,2017],
        'Kyle Singler':[202713,2011,2017],
        'Kyrie Irving':[202681,2011,2017],
        'LaMarcus Aldridge':[200746,2006,2017],
        'Larry Nance Jr.':[1626204,2015,2017],
        'Leandro Barbosa':[2571,2003,2017],
        'LeBron James':[2544,2003,2017],
        'Lou Williams':[101150,2005,2017],
        'Luke Babbitt':[202337,2010,2017],
        'Luke Walton':[2575,2003,2013],
        'Malachi Richardson':[1627781,2016,2017],
        'Malcom Brogdon':[1627763,2016,2017],
        'Manu Ginobili':[1938,2002,2017],
        'Marc Gasol':[201188,2008,2017],
        'Marcus Smart':[203935,2014,2017],
        'Mario Hezonja':[1626209,2015,2017],
        'Mark Jackson':[349,1996,2004],
        'Marquese Chriss':[1627737,2016,2017],
        'Marreese Speights':[201578,2008,2017],
        'Marshall Plumlee':[1627850,2016,2017],
        'Marvin Williams':[101107,2005,2017],
        'Mason Plumlee':[203486,2013,2017],
        'Matt Bonner':[2588,2004,2017],
        'Matthew Dellavedova':[203521,2013,2017],
        'Maurice Harkless':[203090,2012,2017],
        'Meyers Leonard':[203086,2012,2017],
        'Michael Carter-Williams':[203487,2013,2017],
        'Michael Jordan':[893,1996,2017],
        'Michael Kidd-Gilchrist':[203077,2012,2017],
        'Michael Redd':[2072,2000,2017],
        'Mike Conley Jr.':[201144,2007,2017],
        'Mike Dunleavy Jr.':[2399,2002,2017],
        'Mike Miller':[2034,2000,2017],
        'Miles Plumlee':[203101,2012,2017],
        'Mirza Teletovic':[203141,2012,2017],
        'Monta Ellis':[101145,2005,2017],
        'Montrezl Harrel':[1626149,2015,2017],
        'Myles Turner':[1626167,2015,2017],
        'Nene':[2403,2002,2017],
        'Nerlens Noel':[203457,2014,2017],
        'Nick Young':[201156,2007,2017],
        'Nicolas Batum':[201587,2008,2017],
        'Nik Stauskas':[203917,2014,2017],
        'Nikola Jokic':[203999,2015,2017],
        'Nikola Mirotic':[202703,2011,2017],
        'Nikola Vucevic':[202696,2011,2017],
        'Noah Vonleh':[203943,2014,2017],
        'Norman Powell':[1626181,2015,2017],
        'Otto Porter':[203490,2013,2017],
        'P.J. Tucker':[200782,2006,2017],
        'Pascal Siakam':[1627783,2016,2017],
        'Patrick Beverley':[201976,2012,2017],
        'Patrick McCaw':[1627775,2016,2017],
        'Patrick Patterson':[202335,2010,2017],
        'Patty Mills':[201988,2009,2017],
        'Pau Gasol':[2200,2001,2017],
        'Paul George':[202331,2010,2017],
        'Paul Millsap':[200794,2006,2017],
        'Paul Pierce':[1718,1998,2017],
        'Peja Stojakovic':[978,1998,2011],
        'Rajon Rondo':[200765,2006,2017],
        'Ray Allen':[951,1996,2014],
        'Reggie Jackson':[202704,2011,2017],
        'Richard Jefferson':[2210,2001,2017],
        'Ricky Rubio':[201937,2011,2017],
        'Robert Covington':[203496,2013,2017],
        'Robin Lopez':[201577,2008,2017],
        'Rodney Hood':[203918,2014,2017],
        'Ron Baker':[1627758,2016,2017],
        'Rondae Hollis-Jefferson':[1626178,2015,2017],
        'Rudy Gay':[200752,2006,2017],
        'Rudy Gobert':[203497,2013,2017],
        'Russell Westbrook':[201566,2008,2017],
        'Ryan Anderson':[201583,2008,2017],
        'Sam Dekker':[1626155,2015,2017],
        'Sean Kilpatrick':[203930,2014,2017],
        'Serge Ibaka':[201586,2009,2017],
        'Sergio Rodriguez':[200771,2006,2017],
        'Seth Curry':[203552,2013,2017],
        'Shabazz Muhammad':[203498,2013,2017],
        'Shane Battier':[2203,2001,2014],
        'Shaquille O\'Neal':[406,1996,2011],
        'Shaun Livingston':[2733,2004,2017],
        'Skal Labissiere':[1627746,2016,2017],
        'Spencer Hawes':[201150,2007,2017],
        'Stanley Johnson':[1626169,2015,2017],
        'Stephen Curry':[201939,2009,2017],
        'Steve Kerr':[70,1996,2003],
        'Steve Nash':[959,1996,2014],
        'Steven Adams':[203500,2013,2017],
        'T.J. McConnell':[204456,2015,2017],
        'Taurean Prince':[1627752,2016,2017],
        'Terrence Ross':[203082,2012,2017],
        'Thaddeus Young':[201152,2007,2017],
        'Thon Maker':[1627748,2016,2017],
        'Tim Duncan':[1495,1997,2006],
        'Tim Frazier':[204025,2014,2017],
        'Tim Hardaway Jr.':[203501,2013,2017],
        'Timothe Luwawu-Cabarrot':[1627789,2016,2017],
        'Tobias Harris':[202699,2011,2017],
        'Tony Allen':[2754,2004,2017],
        'Tony Parker':[2225,2001,2017],
        'Tracy McGrady':[1503,1997,2012],
        'Trevor Ariza':[2772,2004,2017],
        'Trey Burke':[203504,2013,2017],
        'Trey Lyles':[1626168,2015,2017],
        'Tristan Thompson':[202684,2011,2017],
        'Tyler Johnson':[204020,2014,2017],
        'Tyler Zeller':[203092,2012,2017],
        'Tyreke Evans':[201936,2009,2017],
        'Victor Oladipo':[203506,2013,2017],
        'Vince Carter':[1713,1998,2017],
        'Wesley Matthews':[202083,2009,2017],
        'Willie Cauley-Stein':[1626161,2015,2017],
        'Yao Ming':[2397,2002,2011],
        'Zach LaVine':[203897,2014,2017],
        'Zach Randolph':[2216,2001,2017],
        # 'Ben Simmons':[1627732,2016,2017],
    }

    parser = argparse.ArgumentParser()

    # call via [python shot_charts.py --player_name 'Zach Randolph' --player_id 2216 --start_year 2001 --end_year 2017]
    parser.add_argument('--player_name',type=str,   default='')
    parser.add_argument('--player_id',  type=int,   default=0)
    parser.add_argument('--start_year', type=int,   default=1996)
    parser.add_argument('--end_year',   type=int,   default=2017)
    args = parser.parse_args()

    if args.player_name != '':
        if args.player_id == 0:
            vals = p_list.get(args.player_name)
            if vals is None:
                sys.exit('Need a valid player_id')
            player_list = {args.player_name:vals}
        else:
            player_list = {args.player_name:[args.player_id, args.start_year, args.end_year],}
    else:
        player_list = p_list
    
    initiate(player_list)


