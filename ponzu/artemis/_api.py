import requests
import pandas as pd


# ==================================================
# -- Chain Metrics
# ==================================================
def getChainMetrics_api(chains, metric, start_date, end_date):
  url = f'https://api.artemisxyz.com/asset/{chains}/metric/{metric}/?startDate={start_date}&endDate={end_date}'

  # -- get data from artemis
  response = requests.get(url)
  data = response.json()

  # -- check for errors TODO: make this more meainingful 
  if response.status_code != 200:
    print(url)
    raise ValueError('Artemis API returned an error: ' + str(response.status_code) + '. Please check your inputs and try again. ')
  
  if 'data' not in data.keys():
    raise ValueError('Artemis API returned an error. Please check your inputs and try again.')
  
  return data['data']


# ==================================================
# -- Applications 
# ==================================================
def getAppSummaryTable(timeframe = 'daily'):
  valid_timeframes = ['daily', 'weekly', 'monthly']

  if timeframe not in valid_timeframes:
    print('Warning -- Invalid timeframe, using daily')
    timeframe = 'daily'

  app_url = f'https://api.artemisxyz.com/bam/table/all/applications/{timeframe}'

  # -- get data from artemis
  response = requests.get(app_url)
  data = response.json()

  # -- check for errors TODO: make this more meainingful 
  if response.status_code != 200:
    raise ValueError('Artemis API returned an error. Please check your inputs and try again.')

  # -- convert to dataframe
  df = pd.DataFrame(data)

  return df 

# ==================================================
# -- Blockchain Acitivity (BAM) 
# ==================================================

def getChainActivityByCategory_api(chain, metric, start_date, category_filter = ''): 
  url = f'https://api.artemisxyz.com/bam/chart_v2/{chain}/{metric}/daily?date={start_date}{category_filter}&breakdown=category'

  # -- get data from artemis
  response = requests.get(url)
  data = response.json()

  # -- check for errors TODO: make this more meainingful 
  if response.status_code != 200:
    raise ValueError('Artemis API returned an error. Please check your inputs and try again.')

  # -- convert to dataframe
  df = pd.DataFrame(data)

  return df 


def getChainActivityByApp_api(chain, metric, start_date, category_filter = '', app_filter = ''):

  url = f'https://api.artemisxyz.com/bam/chart_v2/{chain}/{metric}/monthly?date={start_date}{category_filter}{app_filter}&breakdown=application'

  # -- get data from artemis
  response = requests.get(url)
  data = response.json()

  # -- check for errors TODO: make this more meainingful 
  if response.status_code != 200:
    raise ValueError('Artemis API returned an error. Please check your inputs and try again.')

  # -- convert to dataframe
  df = pd.DataFrame(data)

  return df


