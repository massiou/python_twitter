#!/usr/bin/python
# -*- coding:utf-8 -*

# standard lib imports
import re
import sys
import json
import time
import random
# Tierce imports
import twitter

# Globals

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
if sys.stdout.isatty():
    formatter_console = logging.Formatter(yellow('[%(asctime)s]') +
                                      blue('[%(levelname)s]') +
                                      white(' %(message)s'))
else:
    formatter_console = logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s')

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

class TooMuchFriendsToDelete(Exception):
    ''' You try to delete too much friends '''

class TwitterInstance(object):
    '''my twitter '''
    _instance = None
    _timeline = None
    _friendIDs = None

    def __init__(self, keys):
        '''init my instance twitter'''
        print keys
        self._instance = twitter.Api(consumer_key=str(keys['consumer_key']), \
                                    consumer_secret=str(keys['consumer_secret']), \
                                    access_token_key=str(keys['access_token_key']), \
                                    access_token_secret=str(keys['access_token_secret']))

        self._timeline = self._instance.GetHomeTimeline()
        self._friendIDs = self.instance.GetFriendIDs()

    @property
    def instance(self):
        '''get instance'''
        return self._instance

    @property
    def timeline(self):
        '''get timeline'''
        return self._timeline

    @property
    def friendIDs(self):
        '''get friends ID list'''
        return self._friendIDs

    def post_status(self, message):
        ''' post a status on time line'''
            return self.instance.PostUpdate(message)
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

    def get_all_tweets_given_words(self, words_list, lang='fr', count=300, result_type='recent', date_from=None):
        ''' get all tweets regarding to word list'''
        return self.instance.GetSearch(term=words_list, lang=lang, result_type=result_type, count=count, until=date_from)

    def destroy_friendship(self, friend_id):
        logger.info('Destroy friendship: %d' % friend_id)
        self.instance.DestroyFriendship(friend_id)

    def destroy_last_friends(self, number):
        ''' destroy all friends except first number'''
        if len(self.friendIDs) - number < 50:
            raise TooMuchFriendsToDelete
        friends_to_delete = self.friendIDs[:number]
        for friend in friends_to_delete:
            self.destroy_friendship(friend)

    def destroy_old_friends(self, from_number):
        ''' destroy friends from from_number id'''
        if from_number < 1000:
            raise TooMuchFriendsToDelete
        friends_to_delete = self.friendIDs[from_number:]
        logger.info('destroy OLD friends from %d' % from_number)
        for friend in friends_to_delete:
            self.destroy_friendship(friend)

def get_account_globals(json_file):

    with open(json_file, 'r') as json_current:
        account_globals = json.load(json_current)

    return account_globals

if __name__ == '__main__':

    # Globals relied to account
    ACCOUNT_GLOBALS = get_account_globals('./twitter.json')
    KEYS = ACCOUNT_GLOBALS['KEYS']
    print KEYS
    BLACKLIST_ID = ACCOUNT_GLOBALS['BLACKLIST_ID']
    FORBIDDEN_WORDS = ACCOUNT_GLOBALS['FORBIDDEN_WORDS']
    MESSAGES = ACCOUNT_GLOBALS['MESSAGES']

    # Create twitter instance
    mv_twitter = TwitterInstance(KEYS)

    # Ensure number of friends is correct (twitter limit is 2000)
    if len(mv_twitter.friendIDs) > 1950:
        mv_twitter.destroy_old_friends(1949)

    #Post a message
    random_message_index = random.randint(0, len(MESSAGES)-1)
    mv_twitter.post_status(MESSAGES[random_message_index])

    # get tweets from all tweets search
    date_from = time.strftime('%Y-%m-%d')

    tweets_to_rt = mv_twitter.get_all_tweets_given_words(["Concours", "follow"], lang='fr', count=20, result_type='popular')
    tweets_to_rt += mv_twitter.get_all_tweets_given_words(["Concours", "follow"], lang='fr', count=20, result_type='recent')
    tweets_to_rt += mv_twitter.get_all_tweets_given_words(["Gagner", "follow"], lang='fr', count=20, result_type='recent')
    tweets_to_rt += mv_twitter.get_all_tweets_given_words(["Gagner", "follow"], lang='fr', count=20, result_type='popular')
    #tweets_to_rt += mv_twitter.get_all_tweets_given_words(["win", "follow"], lang='en', count=100, result_type='popular')
    #tweets_to_rt += mv_twitter.get_all_tweets_given_words(["win", "follow"], lang='en', count=100, result_type='recent')

    logger.info("Length Tweets to RT: %d", len(tweets_to_rt))
    for index, tweet in enumerate(tweets_to_rt):
        # Exclude fordidden words
        logger.info('%d tweet index', index)
        text = tweet.text.lower()
        if not any(word for word in FORBIDDEN_WORDS if word in text) \
           and not (text.startswith('rt ') or text.startswith('rt@')):
            if tweet.retweeted_status:
                # the current tweet is a RT
                rt_dict = json.loads(str(tweet.retweeted_status))
                tweet_id = rt_dict.get('id', tweet.id)
                user_id = rt_dict['user'].get('id')
            else:
                # it's an original tweet
                tweet_id = tweet.id
                tweet_user = json.loads(str(tweet.GetUser()))
                user_id = tweet_user['id']

            logger.info('%s: %s', tweet_id, tweet.text[:25])

            if user_id not in BLACKLIST_ID:
                try:
                # RT
                    time_to_wait = random.randint(10, 30)
                    print 'wait: %d' % time_to_wait
                    time.sleep(time_to_wait)
                    mv_twitter.instance.PostRetweet(tweet_id)
                except twitter.TwitterError as msg:
                    logger.error(msg)
                except Exception as msg:
                    raise msg
                # Follow
                logger.info('Try to follow:%s' % str(user_id))
                if user_id not in mv_twitter.friendIDs:
                    try:
                        mv_twitter.instance.CreateFriendship(int(user_id))
                    except twitter.TwitterError as msg:
                        logger.error(msg)
                    except Exception as msg:
                        raise msg
                else:
                    logger.info('user id already in friends list : %d', user_id)
            else:
                logger.warning('user is in blacklist: %d',  user_id)
        else:
            logger.info('%d find a forbidden word in %s', index, tweet.text)



