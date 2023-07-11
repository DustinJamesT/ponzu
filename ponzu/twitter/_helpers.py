
# -- standard imports 
import requests
import pandas as pd
import re 
from bs4 import BeautifulSoup


# ==================================================
# -- API Helpers 
# ==================================================

def buildTweetURL(tweet_id):
  tweet_fields = "tweet.fields=lang,author_id,conversation_id,text,public_metrics,attachments,created_at"
  # Tweet fields are adjustable.
  # Options include:
  # attachments, author_id, context_annotations,
  # conversation_id, created_at, entities, geo, id,
  # in_reply_to_user_id, lang, non_public_metrics, organic_metrics,
  # possibly_sensitive, promoted_metrics, public_metrics, referenced_tweets,
  # source, text, and withheld

  params = {
        'tweet.fields':'author_id,created_at,conversation_id,attachments',
        'expansions':'author_id',
        'user.fields':'username',
    }

  if type(tweet_id) == list:
    ids = "ids=" + ",".join(tweet_id)
  else:
    ids = "ids=" + str(tweet_id)
    
  # You can adjust ids to include a single Tweets.
  # Or you can add to up to 100 comma-separated IDs
  url = "https://api.twitter.com/2/tweets?{}&{}".format(ids, tweet_fields)

  return url

def extractTweetId(tweet_url):
  tweet_id = tweet_url.split('status/')[-1].split('/')[0].split('?')[0]

  return tweet_id

# ==================================================
# -- Thread Helpers
# ==================================================






