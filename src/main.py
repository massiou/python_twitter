#!/usr/bin/python
# -*- coding:utf-8 -*

# standard lib imports
import re
import sys

# Tierce imports
import twitter

# Globals
KEYS = {
        'consumer_key':'',
        'consumer_secret': '',
        'access_token_key': '',
        'access_token_secret': ''
        }

# logging imports
import logging
from logging.handlers import RotatingFileHandler
from logging import StreamHandler

# fabric imports
from fabric.colors import red
from fabric.colors import yellow
from fabric.colors import blue
from fabric.colors import white

# logger object creation
logger = logging.getLogger('tweet')
logger.setLevel(logging.DEBUG)
# Build formatter for each handler
formatter_file = logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s')
formatter_console = logging.Formatter(yellow('[%(asctime)s]') + \
                                      blue('[%(levelname)s]') + \
                                      white(' %(message)s'))

# Set handlers filesize is < 1Mo
file_handler = RotatingFileHandler('tweet.log', 'a', 1000000, 1)
stream_handler = logging.StreamHandler(stream=sys.stdout)

# Set formatters
file_handler.setFormatter(formatter_file)
stream_handler.setFormatter(formatter_console)

# Set level
file_handler.setLevel(logging.DEBUG)
stream_handler.setLevel(logging.INFO)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


class TwitterInstance(object):
    '''my twitter '''
    _instance = None
    _timeline = None

    def __init__(self):
        '''init my instance twitter'''
        self._instance = twitter.Api(consumer_key=KEYS['consumer_key'], \
                                    consumer_secret=KEYS['consumer_secret'], \
                                    access_token_key=KEYS['access_token_key'], \
                                    access_token_secret=KEYS['access_token_secret'])

        self._timeline = self._instance.GetHomeTimeline()

    @property
    def instance(self):
        '''get instance'''
        return self._instance

    @property
    def timeline(self):
        '''get timeline'''
        return self._timeline

    def get_followers(self):
        '''get tweets from user_list'''
        return [ follower for follower in self._instance.GetFollowers()]

    def get_followers_name(self):
        '''get tweets from user_list'''
        return [ follower.name for follower in self._instance.GetFollowers()]

    def get_tweets_given_words(self, words_list):
        ''' get timeline tweets regarding to word list'''
        tweets = [ (status.id, status.text) for status in self.instance.GetHomeTimeline() \
                   if all([re.search(word, status.text) for word in words_list]) ]
        return tweets

    def get_all_tweets_given_words(self, words_list):
        ''' get all tweets regarding to word list'''
        return self.instance.GetSearch(words_list)        

if __name__ == '__main__':

    # Create twitter instance
    mv_twitter = TwitterInstance()

    # get tweets from all tweets search
    tweets_to_rt = mv_twitter.get_all_tweets_given_words(["concours", "RT", "Follow"])

    for tweet in tweets_to_rt:
        logger.info('%s: %s', tweet.id, tweet.text)
        try:
            # RT
            mv_twitter.instance.PostRetweet(tweet.id)
            # Follow
            mv_twitter.instance.CreateFriendship(tweet.GetUser())
        except twitter.TwitterError as msg:
            logger.error(msg)
        except Exception as msg:
            raise msg
    



