
# -- standard imports 
import pandas as pd
import time

# -- local imports
from ._api import getChainMetrics_api, getChainActivityByCategory_api, getChainActivityByApp_api
from ._helpers import getCategoryMap, stringifyList

def getChainMetrics_(chains = [], metrics = [], start_date = '', end_date = ''): 
  dfs = []
  chains = stringifyList(chains)

  for metric in metrics:
    # -- call api
    data = getChainMetrics_api(chains, metric, start_date, end_date)

    # -- convert to dataframe
    for chain, data_list in data.items():
      df = pd.DataFrame(data_list)
      df['chain'] = chain
      df['metric'] = metric

      # -- rename value column to metric
      df = df.rename(columns={'val': 'value'})

      dfs.append(df)

  # -- concat all dataframes
  df = pd.concat(dfs)

  # -- convert date to datetime
  df['date'] = pd.to_datetime(df['date'])

  # -- reorder columns
  df = df[['date', 'chain', 'metric', 'value']]

  return df

def getChainActivityByCategory_(chains = [], metrics = [], start_date = '', url_category = '', sleep = 0): 
  # -- initialize 
  dfs = []

  # -- loop through chains
  for metric in metrics:
    for chain in chains:
      # -- call api
      df = getChainActivityByCategory_api(chain, metric, start_date, url_category)

      # -- stack data
      df = df.set_index('date').stack().reset_index()

      # -- rename columns
      df = df.rename(columns={'level_1': 'category', 0: 'value'})

      # -- convert to datetime
      df['date'] = pd.to_datetime(df['date'])

      # -- add metric column
      df['metric'] = metric

      # -- add chain column
      df['chain'] = chain

      dfs.append(df)

      time.sleep(sleep)

  df = pd.concat(dfs)

  # -- reorder columns
  df = df[['date', 'chain', 'metric', 'category', 'value']]

  return df

def getChainActivityByApp_(chains = [], metrics = [], start_date = '', url_category = '', url_apps = '', sleep = 0): 
  # -- initialize 
  dfs = []
  category_map = getCategoryMap()

  # -- loop through chains
  for metric in metrics:
    for chain in chains:
      # -- call api
      df = getChainActivityByApp_api(chain, metric, start_date, url_category, url_apps)

      # -- stack data
      df = df.set_index('date').stack().reset_index()

      # -- rename columns
      df = df.rename(columns={'level_1': 'application', 0: 'value'})

      # -- convert to datetime
      df['date'] = pd.to_datetime(df['date'])

      # -- add metric column
      df['metric'] = metric

      # -- add chain column
      df['chain'] = chain

      dfs.append(df)

      time.sleep(sleep)

  df = pd.concat(dfs)

  
  # -- add category column
  df['category'] = df['application'].apply(lambda x: category_map[x] if x in category_map.keys() else 'Other')

  # -- reorder columns
  df = df[['date', 'chain', 'metric', 'category', 'application', 'value']]

  return df
