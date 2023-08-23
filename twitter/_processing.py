# -- standard library imports
from bs4 import BeautifulSoup
import re 

# -- local imports 


from ._api import callUrl_api

# ==================================================
# -- Users 
# ==================================================

def processUserId_(user_data):
  # -- TODO: Add error handling and logic 
  id = user_data['data']['id']

  return id

def processUserData_(user_data):
  # -- TODO: Add error handling and logic 
  user_data = user_data['data']

  return user_data


# ==================================================
# -- Tweets
# ==================================================

def processTweetData_(tweet_data):

  tweets = tweet_data['data']

  # -- TODO: add any post processing here or error handling

  return tweets

def processPaginatedTweetData_(tweet_data, convsersation_ids=list(), tweets=list()):

  tweets_ = processTweetData_(tweet_data)

  for tweet in tweets_:
    if tweet['conversation_id'] not in convsersation_ids:
      tweets.append(tweet)
      convsersation_ids.append(tweet['conversation_id'])

  return convsersation_ids, tweets



# ==================================================
# -- Threads
# ==================================================

def unpackThreadData_(thread_data):
  # -- NOTE: no thread data is returned for tweets older than 7 days 
  thread_data = thread_data.get('data', [])

  return thread_data

def stitchThreadText_(tweet, thread_data):
  text = tweet['text']
  thread_data = unpackThreadData_(thread_data)

  # text = text + ' \n ' + ' \n '.join([tweet['text'] for tweet in reversed(thread_data)])
  
  if len(thread_data) > 0:
    for tweet in thread_data[::-1]:
      text += ' /n '
      text += tweet['text']

  return text

# ==================================================
# -- Tweet Text Processing
# ==================================================
def extractLinkText_(page):
  #page = callUrl_api(url) 
  soup = BeautifulSoup(page.content, 'html.parser')
  text = soup.text

  return text

def extractUrlsInTweet_(tweet_text):
  urls = []

  # -- extract all urls from tweet text
  urls_ = re.findall(r'(https?://[^\s]+)', tweet_text)

  # -- call urls to get final url (the url in tweet usually is https://t.co/blahblahblah and i want to know destination url)
  for url in urls_:
    page = callUrl_api(url)

    if page.status_code == 200:
      if '//t.co' in page.url:
        soup = BeautifulSoup(page.content, 'html.parser')
        text = soup.text
        redirect_urls = re.findall(r'(https?://[^\s]+)', text)

        if len(redirect_urls) > 0:
          urls.extend(redirect_urls)

      else:
        urls.append(page.url)

  return urls

def appendTweetsLinkText_(tweets):

  for tweet in tweets: 
    urls = extractUrlsInTweet_(tweet['text'])

    if len(urls) > 0: 
      # -- replace tweet text 
      tweet['text'] = "Tweet Text: " + tweet['text'] + "\n\n --- end tweet --- \n\n Link Text: "

      for url in urls:
        # -- skip twitter links TODO: add logic to get twitter link text
        if 'twitter.com' not in url: 
          page = callUrl_api(url)
          link_text = extractLinkText_(page)
          header = " \n\n --- URL Text --- \n URL: " + url + "\n\n " + 'Text: '
          tweet['text'] = tweet['text'] + header + link_text + "\n\n"

  return tweets