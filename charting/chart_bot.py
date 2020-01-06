import tweepy
import time
import sys
import os
import random
import csv
from numpy.random import choice
import nba_shot_charts as charts
from urllib import urlopen
from bs4 import BeautifulSoup

import helper_charting
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
        # raw_input("READY TO TWEET?")

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
            for i in range(max(0, len(os.listdir(player_path))-1), len(os.listdir(player_path))-0):
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
        print "\n\n\nNo internet connection....trying again in 2 minutes"
        time.sleep(120)
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
    p_list_res = db.query("""SELECT CONCAT(fname, ' ', lname) AS p_name
    , player_id
    , SUM(attempts) as p_att
    FROM shots_Player_Distribution_Career
    JOIN players USING (player_id)
    WHERE 1
        AND season_type = 'Reg'
        AND shot_zone_basic = 'all'
        AND shot_zone_area = 'all'
    GROUP BY player_id
    ;""")

    p_dict = {}
    plrs = []
    wghts = []
    for i, row in enumerate(p_list_res):
        pname, pid, p_shots = row
        p_dict[pid] = pname
        plrs.append(pid)
        wghts.append(float(p_shots)**0.8)


    norm_wghts = [float(i)/sum(wghts) for i in wghts]
    p_id = choice(plrs, p=norm_wghts)
    p_name = p_dict.get(p_id)

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

    year = pic.split('.png')[0].split('_')[-1]

    if year[:6] == 'CAREER':
        start_year = db.query("SELECT from_year FROM players WHERE player_id = %s" % (p_id)) [0][0]
        if start_year < 1996:
            tweet += 'PBP ERA (1996/97 onward) ' + year + ' Shot Chart'
        else:
            tweet += year + ' Shot Chart' 
        isCareer = True
        teams = get_teams(p_id, year, isCareer=isCareer)
    else:
        if year == '2018-19':
            tweet += year + ' Shot Chart'
            # tweet += year + '(in progress) Shot Chart'
        else:
            tweet += year + ' Shot Chart' 
        isCareer = False
        teams = get_teams(p_id, year, isCareer)

    season_id = year.replace('-','')

    tweet += helper_charting.get_key_text('Player', p_id, season_id, isCareer, isTwitter=True)

    tweet += '\n\n'

    # Player name hashtag
    player_hashtag = full_name.replace(' ','').replace("'","").replace('-','').replace('.','').replace('(2)','').replace('(3)','')
    tweet += '#' + player_hashtag

    # Custom hashtag
    if hashtags != []:
        tweet += '\n\n'
        for i, tag in enumerate(hashtags):
            tweet += '#' + tag
            if i < (len(hashtags)-1):
                tweet += ' '

    # Team name hashtag
    tweet += '\n'
    for i, team in enumerate(teams):
        if team is not None:
            tweet += '#' + team.replace(" ","")
            if i < (len(teams)-1):
                tweet += ' '

    # Team emoji hashtag
    tweet += '\n'
    for j, team in enumerate(teams):
        if team is not None:
            hashtag = hashtag_list.get(team)
            if (hashtag is not None and hashtag != team):
                tweet += '#' + hashtag
                if j < (len(teams)-1):
                    tweet += ' '

    return tweet


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
    #     'Jimmy Butler':['76ers'],
    #     'Robert Covington':['Timberwolves'],
    #     'Dario Saric':['Timberwolves'],
    #     'Justin Patton':['76ers']    
    #     }


    if tweet_dict == {}:
        initiate()
    else:
        for name, tags in tweet_dict.items():
            initiate(p_name=name, hardcode_tags=tags)


