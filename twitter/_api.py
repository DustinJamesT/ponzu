
# -- standard library imports
import requests
import os
from retry import retry




# -- local imports
from ._helpers import buildTweetURL

# -- load env variables
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

TWITTER_BEARER = os.getenv('TWITTER_BEARER')


# ==================================================
# -- Get Tweets
# ==================================================

@retry(ValueError, tries=3, delay=3)
def getTweet_api(tweet_id): 
  TWITTER_BEARER = os.getenv('TWITTER_BEARER')

  if TWITTER_BEARER == '' or TWITTER_BEARER == None:
    raise ValueError('Twitter Bearer token not found. Please check your environment variables and try again.')
  
  url = buildTweetURL(tweet_id)
  headers = {'Authorization': f'Bearer {TWITTER_BEARER}', "User-Agent": "v2TweetLookupPython"}

  response = requests.request("GET", url, headers=headers)

  if response.status_code != 200:
    raise ValueError('Twitter getTweet API returned an error. Please check your inputs and try again. Tweet ID: {}, Url: {}, response: {}'.format(tweet_id, url, response.text))
  
  if response.status_code == 200:
    if 'data' not in response.json().keys():
      raise ValueError('Twitter getTweet API successful but no data. Please check your inputs and try again. Tweet ID: {}, Url: {}, response: {}'.format(tweet_id, url, response.text))
    
  return response.json()


@retry(ValueError, tries=3, delay=3)
def getThread_api(author_id, conversation_id): 
  TWITTER_BEARER = os.getenv('TWITTER_BEARER')

  # -- get thread. returns a list of tweet objects (dicts) of the thread 
  url = f"https://api.twitter.com/2/tweets/search/recent?query=conversation_id:{conversation_id} from: {author_id} to: {author_id}"
  
  headers = {"Authorization": f"Bearer {TWITTER_BEARER}"}
  
  params = {
      'tweet.fields':'author_id,created_at,conversation_id,attachments',
      'expansions':'author_id',
      'user.fields':'username',
  }

  response = requests.get(url, headers=headers, params=params)

  if response.status_code != 200:
    raise ValueError('Twitter getTweet API returned an error. Please check your inputs and try again.')

  return response.json()


@retry(ValueError, tries=3, delay=3)
def getUserTweets_api(user_id, pagination_token = ''): 
  TWITTER_BEARER = os.getenv('TWITTER_BEARER')

  url = f'https://api.twitter.com/2/users/{user_id}/tweets'

  headers = {'Authorization': f'Bearer {TWITTER_BEARER}'}

  params = {
          'tweet.fields':'author_id,created_at,conversation_id,attachments',
          'user.fields':'username,profile_image_url',
          'exclude': 'retweets,replies'
      }
  
  if pagination_token != '':
    params['pagination_token'] = pagination_token

  response = requests.request("GET", url, headers=headers, params=params)

  if response.status_code != 200:
    raise ValueError('Twitter getUserTweets API returned an error. Please check your inputs and try again. Status Code: {}, Resp Text: {}'.format(response.status_code, response.text))
  
  if response.status_code == 200:
    if 'data' not in response.json().keys():
      raise ValueError('Twitter getUserTweets API successful but no data. Please check your inputs and try again. Status Code: {}, Resp Text: {}'.format(response.status_code, response.text))
    
  return response.json()


# ==================================================
# -- Users
# ==================================================

@retry(ValueError, tries=3, delay=3)
def getTwitterUserID_api(username, idtype = 'username'):
  TWITTER_BEARER = os.getenv('TWITTER_BEARER')

  url ="https://api.twitter.com/2/users/by/{}/{}".format(idtype, username)
  headers = {'Authorization': f'Bearer {TWITTER_BEARER}'}

  response = requests.request("GET", url, headers=headers)

  if response.status_code != 200:
    raise ValueError('Twitter getTwitterUserID_api API returned an error. Please check your inputs and try again.')
  
  if response.status_code == 200:
    if 'data' not in response.json().keys():
      raise ValueError('Twitter getTwitterUserID_api API successful but no data. Please check your inputs and try again.')

  return response.json()


@retry(ValueError, tries=3, delay=3)
def getUserbyID_api(user_id):
  TWITTER_BEARER = os.getenv('TWITTER_BEARER')

  url = f"https://api.twitter.com/2/users/{user_id}"

  headers = {'Authorization': f'Bearer {TWITTER_BEARER}'}
  params = {
        'user.fields':'username,profile_image_url',
    }

  response = requests.request("GET", url, headers=headers, params=params)

  if response.status_code != 200:
    raise ValueError('Twitter getUserbyID_api API returned an error. Please check your inputs and try again.')
  
  if response.status_code == 200:
    if 'data' not in response.json().keys():
      raise ValueError('Twitter getUserbyID_api API successful but no data. Please check your inputs and try again.')

  return response.json()


# ==================================================
# -- General Api 
# ==================================================

@retry(ValueError, tries=3, delay=3)
def callUrl_api(link):
  headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36'}
  page = requests.get(link, headers=headers)
  
  return page