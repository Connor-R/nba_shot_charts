import tweepy
import time
import sys
import os
import random
import csv
import nba_shot_charts as charts
from urllib import urlopen
from bs4 import BeautifulSoup


sys.path.append('/Users/connordog/Dropbox/Desktop_Files/Work_Things/CodeBase/Python_Scripts/Python_Projects/packages')
from py_data_getter import data_getter
from py_db import db
db = db('nba_shots')


key_file = os.getcwd()+"/twitter_keys.csv"
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


base_path = os.getcwd()+"/shot_charts_player/"


# hashtag_file = os.getcwd()+"/team_hashtags.csv"
# hashtag_list = {}
# with open(hashtag_file, 'rU') as f:
#     mycsv = csv.reader(f)
#     for row in mycsv:
#         team, hashtag = row
#         hashtag_list[team]=hashtag


hardcode_file = os.getcwd()+"/hardcode_players.csv"
hardcode_list = {}
with open(hardcode_file, 'rU') as f:
    mycsv = csv.reader(f)
    for row in mycsv:
        player_name, twitter, player_ext = row
        hardcode_list[player_name]=[twitter, player_ext]


def initiate(p_name=None, hardcode_tags=None):

    players = []
    hashtags = []
    # players = ['Andre Iguodala','JJ Redick','David West','Amir Johnson','Taj Gibson','Serge Ibaka','Paul Millsap','Kyle Korver','Ben McLemore','Justin Holliday','Joe Ingles','P.J. Tucker','Cristiano Felicio']
    # hashtags = ['NBAFreeAgencyCharts']

    if p_name is not None:
        players = [p_name]
    if hardcode_tags is not None:
        for tag in hardcode_tags:
            hashtags.append(tag)

    get_random_pic(players, hashtags)


def get_random_pic(players, hashtags):
    if players == []:
        p_name, p_id = get_rand_player()
        print p_name
        chart_player = p_name.replace(' ','_')
        player_path = base_path+chart_player+'('+str(p_id)+')/'
        charts.gen_charts(p_name)
        try:
            rand_chart = os.listdir(player_path)[random.randint(0,len(os.listdir(player_path))-1)]
            tweet(player_path, rand_chart, hashtags, p_id)
        except OSError:
            get_random_pic([],hashtags)
    else:
        for player in players:
            print player
            charts.gen_charts(player)
        # raw_input("READY TO TWEET?")
        for player in players:
            p_id = db.query("SELECT player_id FROM players WHERE CONCAT(fname, ' ', lname) = '%s'" % player.replace("'","\\'")) [0][0]
            player_path = base_path+player.replace(' ','_')+'('+str(p_id)+')/'
            # tweets a range of seasons (-1 is career, -2 is current season, -3 is 2 seasons previous, etc.)
            for i in range(max(0, len(os.listdir(player_path))-2), len(os.listdir(player_path))-1):
                chart = os.listdir(player_path)[i]
                tweet(player_path, chart, hashtags, p_id)


def tweet(player_path, chart, hashtags, p_id):
    tweet_text = parse_text(chart, hashtags, p_id)

    pic_path = player_path + chart

    while len(tweet_text) > 140:
        tweet_text = tweet_text.rsplit(' #', 1)[0]
    
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
    p_list = charts.get_plist()
    player = random.choice(p_list.items())

    p_name = player[0]
    p_id = player[1][0]

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
        met_qry = "SELECT ROUND(efg_plus,0), ROUND(paa,0) FROM shots_Player_Relative_Career WHERE shot_zone_basic = 'all' AND player_id = %s AND season_type = 'reg'" % (p_id)
    else:
        if year == '2017-18':
            tweet += year + '(in progress) Shot Chart'
        else:
            tweet += year + ' Shot Chart' 
        teams = get_teams(p_id, year)
        met_qry = "SELECT ROUND(efg_plus,0), ROUND(paa,0) FROM shots_Player_Relative_Year WHERE shot_zone_basic = 'all' AND player_id = %s AND season_id = %s AND season_type = 'reg'" % (p_id, year.replace('-',''))

    efg, paa = db.query(met_qry)[0]
    if paa >= 0:
        pos = '+'
    else:
        pos = ''
    tweet += ' (' + str(efg) + ' EFG+ | ' + pos + str(paa) + ' PAA).' 

    if efg == 0:
        hashtags.append('Randy')

    player_hashtag = full_name.replace(' ','').replace("'","").replace('-','').replace('.','').replace('(2)','').replace('(3)','')
    tweet += ' #' + player_hashtag

    if hashtags != []:
        for tag in hashtags:
            tweet += ' #' + tag

    for team in teams:        
        # if team is not None:
        #     hashtag = hashtag_list.get(team)
        #     if hashtag is None:
        #         tweet += ' #' + team.replace(" ","")
        #     else:
        #         tweet += ' #' + hashtag
        tweet += ' #' + team.replace(" ","")

    return tweet


def get_teams(p_id, year, isCareer=False):
    
    teams = []

    curr_q = """SELECT DISTINCT tname 
    FROM shots 
    JOIN teams USING (team_id)
    WHERE player_id = %s
    AND season_id = 201617
    AND start_year <= LEFT(season_id, 4)
    AND end_year > LEFT(season_id, 4)
    AND season_type = 'Reg'
    ORDER BY game_date DESC"""

    curr_qry = curr_q % (p_id)

    curr_team = db.query(curr_qry)

    if curr_team != ():
        curr_team = curr_team[0][0]
        teams.append(curr_team)


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
    # tweet_dict = {'DeMarcus Cousins':['Pelicans'],}


    if tweet_dict == {}:
        initiate()
    else:
        for name, tags in tweet_dict.items():
            initiate(p_name=name, hardcode_tags=tags)


