import tweepy
import time
import sys
import os
import random

#keep the quotes, replace this with your information
consumer_key = '123abc...' 
consumer_sec = '123abc...'
access_key = '123abc...'
access_sec = '123abc...'

auth = tweepy.OAuthHandler(consumer_key, consumer_sec)
auth.set_access_token(access_key, access_sec)
api = tweepy.API(auth)

base_path = "/Users/connordog/Dropbox/Desktop_Files/Work_Things/CodeBase/Python_Scripts/Python_Projects/nba_shot_charts/shot_charts/"

def tweet():
    path, pic = get_random_pic()
    tweet_text = parse_text(pic)

    pic_path = path + pic
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

    if pic.split('_')[4] == 'CAREER':
        year = pic.split('_')[5]
        tweet += 'Career (' + year + ') Shot Chart' 
    else:
        year = pic.split('_')[4]
        tweet += year + ' Shot Chart' 

    efg = pic.split('_')[-1].split('.')[0]
    
    tweet += ' (' + efg + '% eFG%).' 

    return tweet


if __name__ == "__main__": 
    tweet()