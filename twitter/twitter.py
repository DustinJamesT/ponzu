

# -- local imports
from ._api import getTwitterUserID_api, getUserbyID_api
from ._api import getTweet_api, getThread_api, getUserTweets_api
from ._api import callUrl_api

from ._processing import processUserId_, processUserData_
from ._processing import processTweetData_, stitchThreadText_, appendTweetsLinkText_, extractLinkText_, processPaginatedTweetData_

from ._helpers import extractTweetId

class Twitter: 
    
  def __init__(self):
    
    self.TWITTER_BEARER = ''

  
  # ==================================================
  # -- Tweets Interface
  # ==================================================

  def getTweet(self, tweet_id, unroll=False, extractLinkText=False):
    # -- check if url or id
    if 'twitter.com' in tweet_id:
      tweet_id = extractTweetId(tweet_id)

    tweet_data = getTweet_api(tweet_id)

    tweets = processTweetData_(tweet_data)

    # -- unroll threads
    tweets = self.unrollThreads(tweets) if unroll else tweets

    # -- extract link text
    tweets = self.appendTweetsLinkText(tweets) if extractLinkText else tweets

    return tweets
  
  def unrollThreads(self, tweets): 
    # -- check if list or single tweet
    if type(tweets) != list:
      tweets = [tweets]

    # -- loop tweets and get thread data
    for tweet in tweets:
      thread_data = getThread_api(tweet['author_id'], tweet['conversation_id'])
      tweet['text'] = stitchThreadText_(tweet, thread_data)

    return tweets
  
  def getThread(self, tweet):
    thread_data = getThread_api(tweet['author_id'], tweet['conversation_id'])

    return thread_data
  
  def appendTweetsLinkText(self, tweets):
    tweets = appendTweetsLinkText_(tweets)

    return tweets
  

  # ==================================================
  # -- Users Interface
  # ==================================================

  def getUserId(self, handle):
    user_data = getTwitterUserID_api(handle)
    user_id = processUserId_(user_data)

    return user_id
  
  def getUser(self, user_id):
    user_data = getUserbyID_api(user_id)
    user_data = processUserData_(user_data)

    return user_data
  
  def getUserTweets(self, handle, tweet_count=10, unroll=False, extractLinkText=False):
    tweets = []
    conv_ids = []

    user_id = self.getUserId(handle)

    # -- get initial tweets 
    tweet_data = getUserTweets_api(user_id)
    tweets += processTweetData_(tweet_data)

    # -- initial processing to initialize conv_ids and tweets lists
    conv_ids, tweets = processPaginatedTweetData_(tweet_data_, conv_ids, tweets)

    # -- check if we need to paginate
    while len(tweets) < tweet_count and 'next_token' in tweet_data['meta'].keys():
      tweet_data_ = getUserTweets_api(user_id, tweet_data['meta']['next_token'])
      conv_ids_, tweets_ = processPaginatedTweetData_(tweet_data_, conv_ids, tweets)

      conv_ids += conv_ids_
      tweets += tweets_

      tweet_data = tweet_data_

    # -- trim to tweet_count
    tweets = tweets[:tweet_count] if len(tweets) > tweet_count else tweets

    # -- unroll threads
    tweets = self.unrollThreads(tweets) if unroll else tweets

    # -- extract link text
    tweets = self.appendTweetsLinkText(tweets) if extractLinkText else tweets

    return tweets

  # ==================================================
  # -- General Helpers 
  # ==================================================

  def getUrlText(self, url): 
    # -- TODO: Customize for frequent link types like Github, Medium, etc. to extract more meaningful text

    if 'http' not in url:
      raise ValueError('Invalid URL passed to Twitter getUrlText. Please check your inputs and try again.')

    if 'twitter.com' in url:
      tweet = self.getTweet(url, unroll=True, extractLinkText=True)
      text = tweet[0]['text']
    else:
      page = callUrl_api(url) 
      text = extractLinkText_(page) 

    return text
