import tweepy
import time
import sys
import os
import random
import csv
import nba_shot_charts as charts
from urllib import urlopen
from bs4 import BeautifulSoup

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

base_path = os.getcwd()+"/shot_charts/"

hashtag_file = os.getcwd()+"/team_hashtags.csv"
hashtag_list = {}
with open(hashtag_file, 'rU') as f:
    mycsv = csv.reader(f)
    for row in mycsv:
        team, hashtag = row
        hashtag_list[team]=hashtag

hardcode_file = os.getcwd()+"/hardcode_players.csv"
hardcode_list = {}
with open(hardcode_file, 'rU') as f:
    mycsv = csv.reader(f)
    for row in mycsv:
        player_name, twitter, player_ext = row
        hardcode_list[player_name]=[twitter, player_ext]

def initiate():
    players = ['']
    hashtags = ['']
    # players = ['']
    # hashtags = ['']

    get_random_pic(players, hashtags)

def get_random_pic(players, hashtags):

    if players == ['']:
        p_name = get_rand_player()
        print p_name
        chart_player = p_name.replace(' ','_')
        player_path = base_path+chart_player+'/'
        charts.gen_charts(p_name)
        rand_chart = os.listdir(player_path)[random.randint(0,len(os.listdir(player_path))-1)]
        tweet(player_path, rand_chart, hashtags)
    else:
        for player in players:
            print player
            charts.gen_charts(player)
        for player in players:
            player_path = base_path+player.replace(' ','_')+'/'
                # tweets current season chart
            # for i in range(max(0, len(os.listdir(player_path))-2), len(os.listdir(player_path))-1):
                # tweets last 3 seasons as well as career chart
            for i in range(max(0, len(os.listdir(player_path))-2), len(os.listdir(player_path))-0):
                chart = os.listdir(player_path)[i]
                tweet(player_path, chart, hashtags)

def tweet(player_path, chart, hashtags):
    tweet_text = parse_text(chart, hashtags)

    pic_path = player_path + chart

    print tweet_text, len(tweet_text)
    # raw_input(pic_path)
    time.sleep(15)
    api.update_with_media(pic_path, status=tweet_text)

def get_rand_player():
    p_list = charts.get_plist()
    player = random.choice(p_list.keys())

    return player

def parse_text(pic, hashtags):
    tweet = ''
    fname = pic.split('_')[2]
    if pic.split('_')[-3] == 'CAREER':
        lname = pic.split('_')[3:-3]
    else:
        lname = pic.split('_')[3:-2]
    tweet = fname + ' '

    for i in range(0,len(lname)-1):
        tweet += lname[i] + ' '
    tweet += lname[-1]
    full_name = tweet
    tweet += '\'s '

    twitter = get_twitter(fname, lname, full_name)
    if twitter is not None:
        tweet += '(' + twitter + ') '

    year = pic.split('_')[-2]
    if pic.split('_')[-3] == 'CAREER':
        tweet += 'Career (' + year + ') Shot Chart' 
        teams = get_reference(fname, lname, year, full_name, isCareer=True)
    else:
        tweet += year + ' Shot Chart' 
        teams = get_reference(fname, lname, year, full_name)

    efg = pic.split('_')[-1].split('.')[0]
    
    tweet += ' (' + efg + '% eFG%).' 

    for team in teams:
        if team is not None:
            hashtag = hashtag_list.get(team)
            if hashtag is None:
                tweet += ' #' + team
            else:
                tweet += ' #' + hashtag

    player_hashtag = fname
    for name in lname:
        player_hashtag += name
    player_hashtag = player_hashtag.replace('-','').replace('.','').replace('CAREER','').replace('(2)','').replace('(3)','')

    tweet += ' #' + player_hashtag

    if hashtags != ['']:
        for tag in hashtags:
            tweet += ' #' + tag

    return tweet

def get_reference(fname, lname, year, full_name, isCareer=False):
    search_letter = lname[0][:1]
    search_name = fname + ' '
    for i in range(0,len(lname)-1):
        search_name += lname[i] + ' '
    search_name += lname[-1]

    try:
        player_ext = hardcode_list.get(full_name)[1]
    except TypeError:
        player_ext = ''

    if player_ext != '':
        player_url = 'http://www.basketball-reference.com' + player_ext
        teams = get_curr_team(player_url, year, isCareer)
        return teams
    else:
        index_url = "http://www.basketball-reference.com/players/%s/" % search_letter.lower()
        ind_html = urlopen(index_url)
        ind_soup = BeautifulSoup(ind_html, "lxml")

        data_rows = ind_soup.findAll('tr')[1:]
        for row in data_rows:
            p_data = row.findAll('th')
            p_name = p_data[0].getText()

            if p_name[:len(search_name)] == search_name:
                player_url = 'http://www.basketball-reference.com' + row.findAll('a', href=True)[0]['href']
                teams = get_curr_team(player_url, year, isCareer)
                return teams

    return [None]

def get_curr_team(player_url, year, isCareer):
    teams = []
    html = urlopen(player_url)
    soup = BeautifulSoup(html, "lxml")

    data_rows = soup.findAll('p')[1:]

    curr_team = None
    season_team = None
    for row in data_rows:
        if row.getText()[:5] == 'Team:':
            team_data = row.getText()
            curr_team = row.getText().split(' ')[-1]
            teams.append(curr_team)
            break

    tables = soup.findAll('tr')[1:]
    for row in tables:
        if row.getText()[:7] == year:
            season_team_url = 'http://www.basketball-reference.com' + row.findAll('a', href=True)[1]['href']
            season_team_html = urlopen(season_team_url)
            season_team_soup = BeautifulSoup(season_team_html, "lxml")

            h1_data = season_team_soup.findAll('h1')[0]

            seas_team = h1_data.findAll('span')[1].getText().split(' ')[-1]
            if seas_team != 'NBA':
                teams.append(seas_team)

    if isCareer is True:
        teams.append('NBA')

    teams = list(set(teams))
    return teams

def get_twitter(fname, lname, full_name):
    try:
        twitter_name = hardcode_list.get(full_name)[0]
    except TypeError:
        twitter_name = None

    if twitter_name in (None, ''):

        search_name = fname + ' '
        for i in range(0,len(lname)-1):
            search_name += lname[i] + ' '
        search_name += lname[-1]
        url = "http://www.basketball-reference.com/friv/twitter.html"
        html = urlopen(url)
        soup = BeautifulSoup(html, "lxml")

        data_rows = soup.findAll('tr')[2:] 

        for row in data_rows:
            p_entry = {}
            p_data = row.findAll('td')
            p_name = p_data[0].getText()

            if p_name == search_name:
                twitter_name = p_data[1].getText()
                break
            else:
                twitter_name = None

    if twitter_name == 'notwitter':
        twitter_name = None

    return twitter_name


if __name__ == "__main__": 
    initiate()