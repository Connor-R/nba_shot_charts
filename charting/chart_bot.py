import tweepy
import time
import sys
import os
import random
import csv
import nba_shot_charts as charts
from urllib import urlopen
from bs4 import BeautifulSoup


from py_data_getter import data_getter
from py_db import db
db = db('nba_shots')


base_path = os.getcwd()+"/shot_charts_player/"

key_file = os.getcwd()+"/../csvs/twitter_keys.csv"
key_list = {}
with open(key_file, 'rU') as f:
    mycsv = csv.reader(f)
    for row in mycsv:
        _type, _key = row
        key_list[_type]=_key
consumer_key = key_list.get('consumer_key')
consumer_sec = key_list.get('consumer_sec')
access_key = key_list.get('access_key')
access_sec = key_list.get('access_sec')

auth = tweepy.OAuthHandler(consumer_key, consumer_sec)
auth.set_access_token(access_key, access_sec)
api = tweepy.API(auth)

hashtag_file = os.getcwd()+"/../csvs/team_hashtags.csv"
hashtag_list = {}
with open(hashtag_file, 'rU') as f:
    mycsv = csv.reader(f)
    for row in mycsv:
        team, hashtag = row
        hashtag_list[team]=hashtag

hardcode_file = os.getcwd()+"/../csvs/hardcode_players.csv"
hardcode_list = {}
with open(hardcode_file, 'rU') as f:
    mycsv = csv.reader(f)
    for row in mycsv:
        player_name, twitter, player_ext = row
        hardcode_list[player_name]=[twitter, player_ext]


def initiate(p_name=None, hardcode_tags=None):

    players = []
    hashtags = []
    thread = None

    ######################

    # """Once, again, inspired by @presidual's post (https://twitter.com/presidual/status/948343815559000065) at @NylonCalculus giving a look at rookie shot charts, I'm posting updating versions of my shot charts for every rookie with >250 shot attempts this year. (THREAD)

    #NBARookieCharts"""

    # p_q = db.query("SELECT CONCAT(fname, ' ', lname) AS p_name FROM shots_player_relative_year p1 LEFT JOIN shots_player_relative_year p2 ON (p1.player_id = p2.player_id AND p1.season_type = p2.season_type AND p1.season_id != p2.season_id) JOIN players ON (p1.player_id = players.player_id) WHERE p1.shot_zone_basic = 'ALL' AND p1.season_id = 201718 AND p1.season_type = 'reg' AND p2.games IS NULL AND p1.attempts > 250 ORDER BY p1.attempts DESC;")
    # for row in p_q:
    #     players.append(row[0])
    # hashtags = ['NBARookieCharts']
    # thread = 948599163708571648

    ######################

    # """Using @bball_ref's MVP Tracker (https://www.basketball-reference.com/friv/mvp.html), I'm posting updating versions of my shot charts for their current top 10 MVP candidates. (Thread)

    #NBAMVPTracker"""

    # players = ['James Harden', 'LeBron James', 'Kevin Durant', 'Giannis Antetokounmpo', 'DeMar DeRozan', 'Russell Westbrook', 'Kyrie Irving', 'Anthony Davis', 'Karl-Anthony Towns', 'Kyle Lowry']
    # hashtags = ['NBAMVPTracker']
    # thread = 950847068297347072

    ######################

    if p_name is not None:
        players = [p_name]
    if hardcode_tags is not None:
        for tag in hardcode_tags:
            hashtags.append(tag)

    get_random_pic(players, hashtags, thread)


def get_random_pic(players, hashtags, thread):
    if players == []:
        p_name, p_id = get_rand_player()
        print p_name
        chart_player = p_name.replace(' ','_')
        player_path = base_path+chart_player+'('+str(p_id)+')/'
        charts.gen_charts(p_id)
        try:
            rand_chart = os.listdir(player_path)[random.randint(0,len(os.listdir(player_path))-1)]
            tweet(player_path, rand_chart, hashtags, p_id, thread)
        except OSError:
            get_random_pic([],hashtags,thread)
    else:
        for player in players:
            print player
            try:
                p_id = db.query("SELECT player_id FROM players WHERE CONCAT(fname, ' ', lname) = '%s'" % player.replace("'","\\'")) [0][0]
            except (OSError, IndexError):
                if player == 'Mike James':
                    p_id = 1628455
                elif player == 'J.J. Redick':
                    p_id = 200755
                elif player == 'C.J. McCollum':
                    p_id = 203468


            charts.gen_charts(p_id)
        raw_input("READY TO TWEET?")

        for player in players:
            try:
                p_id = db.query("SELECT player_id FROM players WHERE CONCAT(fname, ' ', lname) = '%s'" % player.replace("'","\\'")) [0][0]
            except (OSError, IndexError):
                if player == 'Mike James':
                    p_id = 1628455
                elif player == 'J.J. Redick':
                    p_id = 200755
                elif player == 'C.J. McCollum':
                    p_id = 203468
                
            player_path = base_path+player.replace(' ','_')+'('+str(p_id)+')/'
            # tweets a range of seasons (-1 is career, -2 is current season, -3 is 2 seasons previous, etc.)
            for i in range(max(0, len(os.listdir(player_path))-2), len(os.listdir(player_path))-1):
                chart = os.listdir(player_path)[i]
                # print chart
                tweet(player_path, chart, hashtags, p_id, thread)


def tweet(player_path, chart, hashtags, p_id, thread):
    tweet_text = parse_text(chart, hashtags, p_id)

    pic_path = player_path + chart

    while len(tweet_text) > 280:
        tweet_text = tweet_text.rsplit('#', 1)[0]
    
    print tweet_text, len(tweet_text)
    # raw_input(pic_path)


    time.sleep(15)

    try:
        # putting tweets in a thread
        if thread is not None:
            api.update_with_media(pic_path, status=tweet_text, in_reply_to_status_id=thread)
        else:
            api.update_with_media(pic_path, status=tweet_text)
    except tweepy.error.TweepError:
        print "\n\n\nNo internet connection....trying again in 10 min"
        time.sleep(600)
        try:
            # putting tweets in a thread
            if thread is not None:
                api.update_with_media(pic_path, status=tweet_text, in_reply_to_status_id=thread)
            else:
                api.update_with_media(pic_path, status=tweet_text)
        except tweepy.error.TweepError:
            print "No internet connection, please try again later\n\n\n"

def get_rand_player():
    p_list = {}
    p_list_res = db.query("SELECT CONCAT(fname, ' ', lname) AS p_name, player_id FROM shots_player_relative_year JOIN players USING (player_id) WHERE season_type = 'reg' AND shot_zone_basic = 'all';")
    for i, row in enumerate(p_list_res):
        p_list[i] = [row[0],row[1]]

    player = random.choice(p_list.items())

    p_id = player[1][1]
    p_name = player[1][0]

    if p_name.split(' ')[0][1].isupper() and p_name not in ('OG Anunoby',):
        temp_name = p_name
        p_name = ''
        for i in range(0, len(temp_name.split(' ')[0])):
            p_name += temp_name.split(' ')[0][i] + '.'
        for i in range(1, len(temp_name.split(' '))):
            p_name += ' ' + temp_name.split(' ')[i]

    return p_name, p_id


def parse_text(pic, hashtags, p_id):
    tweet = ''

    fname, lname, full_name = db.query("SELECT fname, lname, CONCAT(fname, ' ', lname) FROM players WHERE player_id = "+str(p_id))[0]

    tweet = full_name+'\'s '

    twitter = get_twitter(full_name)
    if twitter is not None:
        tweet += '(@' + twitter + ') '

    year = pic.split('_')[-3]

    if pic.split('_')[-3][:6] == 'CAREER':
        tweet += year + ' Shot Chart' 
        teams = get_teams(p_id, year, isCareer=True)
        met_qry = "SELECT games, attempts, ROUND(attempts/games,1), ROUND(efg_plus,0), ROUND(paa,0), ROUND(paa_per_game,1) FROM shots_Player_Relative_Career WHERE shot_zone_basic = 'all' AND player_id = %s AND season_type = 'reg'" % (p_id)
        ShotSkill = get_ShotSkillPlus(p_id, year.replace('-',''), isCareer=True)
    else:
        if year == '2017-18':
            tweet += year + '(in progress) Shot Chart'
        else:
            tweet += year + ' Shot Chart' 
        teams = get_teams(p_id, year)
        met_qry = "SELECT games, attempts, ROUND(attempts/games,1), ROUND(efg_plus,0), ROUND(paa,0), ROUND(paa_per_game,1) FROM shots_Player_Relative_Year WHERE shot_zone_basic = 'all' AND player_id = %s AND season_id = %s AND season_type = 'reg'" % (p_id, year.replace('-',''))
        ShotSkill = get_ShotSkillPlus(p_id, year.replace('-',''), isCareer=False)

    # raw_input(met_qry)
    games, atts, volume, efg, paa, paag = db.query(met_qry)[0]

    if paa >= 0:
        pos = '+'
    else:
        pos = ''

    vol_grade = get_descriptor('volume', volume)
    eff_grade = get_descriptor('efficiency', efg)
    shot_grade = get_descriptor('shot_making', ShotSkill)
    ev_grade = get_descriptor('efficiency_value', paag)


    tweet += ':\nVolume: %s | %s Attempts per Game (%s attempts in %s games)' % (vol_grade, volume, atts, games)
    tweet += '\nEfficiency: %s | %s EFG+' % (eff_grade, efg)
    tweet += '\nShot Making: %s | %s ShotSkill+' % (shot_grade, ShotSkill)
    tweet += '\nEfficiency Value: %s | %s%s PAA/G (%s%s PAA)' % (ev_grade, pos, paag, pos, paa)

    tweet += '\n\n'

    if efg == 0:
        hashtags.append('Randy')

    player_hashtag = full_name.replace(' ','').replace("'","").replace('-','').replace('.','').replace('(2)','').replace('(3)','')
    tweet += '#' + player_hashtag

    if hashtags != []:
        tweet += '\n\n'
        for i, tag in enumerate(hashtags):
            tweet += '#' + tag
            if i < (len(hashtags)-1):
                tweet += ' '

    tweet += '\n'

    for i, team in enumerate(teams):
        if team is not None:
            tweet += '#' + team.replace(" ","")
            if i < (len(teams)-1):
                tweet += ' '

    tweet += '\n'
    # tweet += '#NBATwitter\n'

    for j, team in enumerate(teams):
        if team is not None:
            hashtag = hashtag_list.get(team)
            if (hashtag is not None and hashtag != team):
                tweet += '#' + hashtag
                if j < (len(teams)-1):
                    tweet += ' '

    return tweet

#Getting the player's overall zone percentage
def get_ShotSkillPlus(player_id, season_id, isCareer):
    if isCareer is False:
        metric_q = """SELECT ROUND(sum_efg_plus/attempts,0)
        FROM(
            SELECT SUM(attempts*zone_efg_plus) AS sum_efg_plus
            FROM shots_Player_Relative_Year r
            WHERE season_id = %s
            AND player_id = %s
            AND season_type = 'reg'
            AND shot_zone_area = 'all'
            AND shot_zone_basic != 'all'
        ) a
        JOIN(
            SELECT attempts
            FROM shots_Player_Relative_Year r
            WHERE season_id = %s
            AND player_id = %s
            AND season_type = 'reg'
            AND shot_zone_area = 'all'
            AND shot_zone_basic = 'all'
        ) b;
        """
        metric_qry = metric_q % (season_id.replace('-',''), player_id, season_id.replace('-',''), player_id)

    else:
        metric_q = """SELECT ROUND(sum_efg_plus/attempts,0)
        FROM(
            SELECT SUM(attempts*zone_efg_plus) AS sum_efg_plus
            FROM shots_Player_Relative_Career r
            WHERE player_id = %s
            AND season_type = 'reg'
            AND shot_zone_area = 'all'
            AND shot_zone_basic != 'all'
        ) a
        JOIN(
            SELECT attempts
            FROM shots_Player_Relative_Career r
            WHERE player_id = %s
            AND season_type = 'reg'
            AND shot_zone_area = 'all'
            AND shot_zone_basic = 'all'
        ) b;
        """
        metric_qry = metric_q % (player_id, player_id)

    # raw_input(metric_qry)
    try:
        res = db.query(metric_qry)[0][0]
    except IndexError:
        res = 0

    return res


def get_descriptor(category, metric):

    # from the bot_percentiles.py scripte\
    # < 15 percentile group for lowest group
    # 15-35 for 2nd lowest
    # 35-65 for middle
    # 65-85 for 2nd highest
    # > 85 for highest

    vol_dict = {"Extreme":[1000,13.9], "High":[13.9,10.0], "Average":[10.0,6.6], "Low":[6.6,4.9], "Miniscule":[4.9,-1]}
    shot_dict = {"Excellent":[1000,108.3], "Good":[108.3,102.8], "Average":[102.8,96.5], "Poor":[96.5,90.8], "Bad":[90.8,-1]}
    eff_dict = {"Excellent":[1000,109.2], "Good":[109.2,103.2], "Average":[103.2,96.8], "Poor":[96.8,91.7], "Bad":[91.7,-1]}
    ev_dict = {"Excellent":[1000,0.7], "Good":[0.7,0.3], "Average":[0.3,-0.2], "Poor":[-0.2,-0.6], "Bad":[-0.6,-1000]}


    descriptor = ''
    if category == 'volume':
        desc_dict = vol_dict
    elif category == 'shot_making':
        desc_dict = shot_dict
    elif category == 'efficiency':
        desc_dict = eff_dict
    elif category == 'efficiency_value':
        desc_dict = ev_dict

    for k,v in desc_dict.items():
        high, low = v
        if (metric > low and metric <= high):
            descriptor = k.upper()

    return descriptor


def get_teams(p_id, year, isCareer=False):
    
    teams = []

    # curr_q = """SELECT DISTINCT tname 
    # FROM shots 
    # JOIN teams USING (team_id)
    # WHERE player_id = %s
    # AND season_id = 201718
    # AND start_year <= LEFT(season_id, 4)
    # AND end_year > LEFT(season_id, 4)
    # AND season_type = 'Reg'
    # ORDER BY game_date DESC"""

    # curr_qry = curr_q % (p_id)

    # curr_team = db.query(curr_qry)

    # if curr_team != ():
    #     curr_team = curr_team[0][0]
    #     teams.append(curr_team)


    if isCareer is False:
        team_q = """SELECT DISTINCT tname 
    FROM shots 
    JOIN teams USING (team_id)
    WHERE player_id = %s
    AND season_id = %s
    AND start_year <= LEFT(season_id, 4)
    AND end_year > LEFT(season_id, 4)
    AND season_type = 'Reg'"""

        team_qry = team_q % (p_id, year.replace('-',''))

    else:
        team_q = """SELECT DISTINCT tname 
    FROM shots 
    JOIN teams USING (team_id)
    WHERE player_id = %s
    AND start_year <= LEFT(season_id, 4)
    AND end_year > LEFT(season_id, 4)
    AND season_type = 'Reg'"""

        team_qry = team_q % (p_id)

    add_teams = db.query(team_qry)
    for team in add_teams:
        tname, = team
        teams.append(tname)

    teams = list(set(teams))
    return teams


def get_twitter(full_name):
    try:
        twitter_name = hardcode_list.get(full_name)[0]
    except TypeError:
        twitter_name = None

    if twitter_name in (None, ''):

        url = "http://www.basketball-reference.com/friv/twitter.html"
        try:
            html = urlopen(url)
        except IOError:
            return None
        soup = BeautifulSoup(html, "lxml")

        data_rows = soup.findAll('tr')[2:] 

        for row in data_rows:
            p_entry = {}
            p_data = row.findAll('td')
            p_name = p_data[0].getText()

            if p_name == full_name:
                twitter_name = p_data[1].getText()
                break
            else:
                twitter_name = None

    if twitter_name == 'notwitter':
        twitter_name = None

    return twitter_name


if __name__ == "__main__":
    tweet_dict = {} 
    # tweet_dict = {
    #     'Carmelo Anthony':['Thunder'],
    #     'Enes Kanter':['Knicks'],
    #     'Doug McDermott':['Knicks'],
    #     }


    if tweet_dict == {}:
        initiate()
    else:
        for name, tags in tweet_dict.items():
            initiate(p_name=name, hardcode_tags=tags)


