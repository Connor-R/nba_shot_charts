import tweepy
import time
import sys
import os
import random
import csv
from urllib import urlopen
from bs4 import BeautifulSoup

#keep the quotes, replace this with your information
consumer_key = 'iBh2GInLhKDb4FfcrXnCIg1SP' 
consumer_sec = 't3QfvfLaiYDAZTFGpJutuprez3VTtaVmwVXy3L5mL5Tl2TY2uQ'
access_key = '829083054106816512-L1TZJEJocnqD5LerlTVcaQzTJEOadhv'
access_sec = 'gVtpmYOYw1KSyx0y92VKvAYozf2pfzqrB39jX2Tf0vKlB'

auth = tweepy.OAuthHandler(consumer_key, consumer_sec)
auth.set_access_token(access_key, access_sec)
api = tweepy.API(auth)

base_path = os.getcwd()+"/shot_charts/"

hashtag_file = os.getcwd()+"/nba_hashtags.csv"
hashtag_list = {}
with open(hashtag_file, 'rU') as f:
    mycsv = csv.reader(f)
    for row in mycsv:
        team, hashtag = row
        hashtag_list[team]=hashtag


def tweet():
    path, pic = get_random_pic()
    tweet_text = parse_text(pic)

    pic_path = path + pic

    raw_input(tweet_text)
    api.update_with_media(pic_path, status=tweet_text)

def get_random_pic():

    rand_player = os.listdir(base_path)[random.randint(0,len(os.listdir(base_path))-1)]
    player_path = base_path+rand_player+'/'
    rand_chart = os.listdir(player_path)[random.randint(0,len(os.listdir(player_path))-1)]

    return player_path, rand_chart

def parse_text(pic):
    tweet = ''
    fname = pic.split('_')[2]
    lname = pic.split('_')[3]
    tweet = fname + ' ' + lname +'\'s '

    twitter = get_twitter(fname, lname)
    if twitter is not None:
        tweet += '(' + twitter + ') '

    year = pic.split('_')[-2]
    if pic.split('_')[4] == 'CAREER':
        tweet += 'Career (' + year + ') Shot Chart' 
        teams = get_reference(fname, lname, year, isCareer=True)
    else:
        tweet += year + ' Shot Chart' 
        teams = get_reference(fname, lname, year)

    efg = pic.split('_')[-1].split('.')[0]
    
    tweet += ' (' + efg + '% eFG%).' 

    for team in teams:
        if team is not None:
            hashtag = hashtag_list.get(team)
            if hashtag is None:
                tweet += ' #' + team
            else:
                tweet += ' #' + hashtag


    return tweet

def get_reference(fname, lname, year, isCareer=False):
    search_letter = lname[:1]
    search_name = fname + ' ' + lname

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

def get_twitter(fname, lname):
    search_name = fname + ' ' + lname
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

    return twitter_name

if __name__ == "__main__": 
    tweet()