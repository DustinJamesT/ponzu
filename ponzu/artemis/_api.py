import requests
import pandas as pd


# ==================================================
# -- Chain Metrics
# ==================================================
def getChainMetrics_api(chains, metric, start_date, end_date, api_key = ''):
  #url = f'https://api.artemisxyz.com/asset/{chains}/metric/{metric}/?startDate={start_date}&endDate={end_date}'
  url = f'https://api.artemisxyz.com/data/{metric}/?artemisIds={chains}&startDate={start_date}&endDate={end_date}'

  url = url + '&APIKey=' + api_key

  # -- headers 
  headers = {
    'accept': 'application/json',
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*'
  }
  # -- get data from artemis
  response = requests.get(url, headers=headers)

  try:
    data = response.json()
  except:
    print(response)
    print(response.status_code)
    print(response.text)
    print(url)
    raise ValueError('Artemis API failed to return json.')

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


# ==================================================
# -- Developer Acitivity 
# ==================================================

def getDevEcosystems_api(api_key = ''): 
  url = 'https://api.artemisxyz.com/dev-ecosystems'

  params = {
    'APIKey': api_key
  }

  # -- get data from artemis
  response = requests.get(url, params=params)
  data = response.json()

  return data

# -- TODO implement retry 
def getDeveloperActivity_api(ecosystem = '', days_back = 365, include_forks = False, metric = 'commits', api_key = ''): 
  if metric not in ['commits', 'developers']:
    print('Warning -- Invalid metric. Valid metrics are "commits" and "developers". Using commits.')
    metric = 'commits'
  
  url = 'https://api.artemisxyz.com/weekly-commits' if metric == 'commits' else ''
  url = 'https://api.artemisxyz.com/weekly-active-devs' if metric == 'developers' else url
  url = 'https://api.artemisxyz.com/weekly-active-devs' if url == '' else url

  params = {
    'APIKey': api_key, 
    'daysBack': days_back,
    'ecosystem': ecosystem,
    'includeForks': include_forks
  }

  # -- get data from artemis
  response = requests.get(url, params=params)
  if response.status_code != 200:
    raise ValueError(f'Artemis API returned an error for {ecosystem}. status code: {response.status_code}.   text: {response.text}.')
  
  data = response.json()

  return data



