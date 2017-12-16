import tweepy
import time
import sys
import os
import random
import csv
import nba_team_charts as charts
from urllib import urlopen
from bs4 import BeautifulSoup


sys.path.append('/Users/connordog/Dropbox/Desktop_Files/Work_Things/CodeBase/Python_Scripts/Python_Projects/packages')
from py_data_getter import data_getter
from py_db import db
db = db('nba_shots')


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


base_path = os.getcwd()+"/shot_charts_team/"


hashtag_file = os.getcwd()+"/../csvs/team_hashtags.csv"
hashtag_list = {}
with open(hashtag_file, 'rU') as f:
    mycsv = csv.reader(f)
    for row in mycsv:
        team, hashtag = row
        hashtag_list[team]=hashtag

twitter_file = os.getcwd()+"/../csvs/team_twitter.csv"
twitter_list = {}
with open(twitter_file, 'rU') as f:
    mycsv = csv.reader(f)
    for row in mycsv:
        team, twitter = row
        twitter_list[team]=twitter


def initiate(t_name=None, hardcode_tags=None):

    teams = []
    hashtags = []
    # teams = ['']
    # hashtags = ['']

    if t_name is not None:
        teams = [t_name]
    if hardcode_tags is not None:
        for tag in hardcode_tags:
            hashtags.append(tag)

    get_random_pic(teams, hashtags)


def get_random_pic(teams, hashtags):
    if teams == []:

        t_id, city, tname = get_rand_player()
        print city, tname
        team_string = city.replace(' ','_')+'_'+tname.replace(' ','_')+'('+str(t_id)+')'
        team_path = base_path+team_string+'/'
        charts.gen_charts(team_string)
        try:
            rand_chart = os.listdir(team_path)[random.randint(0,len(os.listdir(team_path))-1)]
            tweet(team_path, rand_chart, hashtags, t_id, city, tname)
        except OSError:
            get_random_pic([],hashtags)
    else:
        for tname in teams:
            print tname
            t_id, city = db.query("SELECT team_id, city FROM teams WHERE tname = '%s' ORDER BY start_year DESC" % tname.replace("'","\\'")) [0]
            team_string = city.replace(' ','_')+'_'+tname.replace(' ','_')+'('+str(t_id)+')'
            charts.gen_charts(team_string)
        # raw_input("READY TO TWEET?")
        for team in teams:
            t_id, city = db.query("SELECT team_id, city FROM teams WHERE tname = '%s' ORDER BY start_year DESC" % tname.replace("'","\\'")) [0]
            team_string = city.replace(' ','_')+'_'+tname.replace(' ','_')+'('+str(t_id)+')'
            team_path = base_path+team_string+'/'
            for i in range(max(0, len(os.listdir(team_path))-1), len(os.listdir(team_path))-0):
                chart = os.listdir(team_path)[i]
                tweet(team_path, chart, hashtags, t_id, city, tname)


def tweet(team_path, chart, hashtags, t_id, city, tname):
    tweet_text = parse_text(chart, hashtags, t_id, city, tname)

    pic_path = team_path + chart

    while len(tweet_text) > 280:
        tweet_text = tweet_text.rsplit('#', 1)[0]
    
    print tweet_text, len(tweet_text)
    # raw_input(pic_path)
    time.sleep(15)
    try:
        api.update_with_media(pic_path, status=tweet_text)
    except tweepy.error.TweepError:
        print "\n\n\nNo internet connection....trying again in 10 min"
        time.sleep(600)
        try:
            api.update_with_media(pic_path, status=tweet_text)
        except tweepy.error.TweepError:
            print "No internet connection, please try again later\n\n\n"

def get_rand_player():
    p_list = {}
    p_list_res = db.query("SELECT team_id, city, tname FROM shots_team_relative_year JOIN teams USING (team_id) WHERE season_type = 'reg' AND LEFT(season_id,4) >= start_year AND LEFT(season_id,4) < end_year AND shot_zone_basic = 'all';")
    for i, row in enumerate(p_list_res):
        p_list[i] = [row[0],row[1],row[2]]

    team = random.choice(p_list.items())

    p_id = team[1][0]
    city = team[1][1]
    tname = team[1][2]

    return p_id, city, tname


def parse_text(pic, hashtags, t_id, city, tname):
    tweet = ''

    full_name = city + ' ' + tname

    tweet = full_name+'\'s '


    twitter = twitter_list.get(tname)

    if twitter is not None:
        tweet += '(@' + twitter + ') '

    year = pic.split('_')[-3]

    if year == '2017-18':
        tweet += year + '(in progress) Shot Chart'
    else:
        tweet += year + ' Shot Chart' 

    met_qry = "SELECT attempts, ROUND(efg_plus,1), ROUND(paa,0) FROM shots_Team_Relative_Year WHERE shot_zone_basic = 'all' AND team_id = %s AND season_id = %s AND season_type = 'reg'" % (t_id, year.replace('-',''))

    atts, efg, paa = db.query(met_qry)[0]
    if paa >= 0:
        pos = '+'
    else:
        pos = ''
    tweet += ' (' + str(atts) + ' attempts | ' + str(efg) + ' EFG+ | ' + pos + str(paa) + ' PAA)\n\n' 

    team_hashtag = full_name.replace(' ','').replace("'","").replace('-','').replace('.','').replace('(2)','').replace('(3)','')
    tweet += '#' + team_hashtag

    if hashtags != []:
        tweet += '\n\n'
        for i, tag in enumerate(hashtags):
            tweet += '#' + tag
            if i < (len(hashtags)-1):
                tweet += ' '

    tweet += '\n'
    # tweet += '#NBATwitter\n'

    hashtag = hashtag_list.get(tname)
    if (hashtag is not None and hashtag != tname):
        tweet += '#' + hashtag 

    return tweet


if __name__ == "__main__":
    tweet_dict = {} 
    # tweet_dict = {'Warriors':['Go Dubs',], 'Cavaliers':['Go LeBron']}


    if tweet_dict == {}:
        initiate()
    else:
        for name, tags in tweet_dict.items():
            initiate(p_name=name, hardcode_tags=tags)


