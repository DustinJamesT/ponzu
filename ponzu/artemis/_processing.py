
# -- standard imports 
import pandas as pd
import time

# -- local imports
from ._api import getChainMetrics_api, getChainActivityByCategory_api, getChainActivityByApp_api
from ._helpers import getCategoryMap, stringifyList

def getChainMetricsOld_(chains = [], metrics = [], start_date = '', end_date = '', api_key = ''): 
  dfs = []
  chains = stringifyList(chains)

  for metric in metrics:
    # -- call api
    data = getChainMetrics_api(chains, metric, start_date, end_date, api_key)

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

def getChainMetrics_(chains = [], metrics = [], start_date = '', end_date = '', api_key = ''): 
  dfs = []
  chains = stringifyList(chains)

  for metric in metrics:
    # -- call api
    data = getChainMetrics_api(chains, metric, start_date, end_date, api_key)
    data = data['artemis_ids'] if 'artemis_ids' in data.keys() else data

    # -- convert to dataframe
    for chain, data_list in data.items():
      # -- handle artemis errors (they return a string instead of a list with the error message)
      if type(data_list) == dict and type(data_list[metric]) == str:
        print(chain + ' ' + metric + ' is empty: ' + data_list[metric])
        continue

      df = pd.DataFrame(data_list[metric])
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

# ==================================================
# -- Developer Acitivity 
# ==================================================

def processEcosystems(ecosystem_resp): 
  
  ecosystems = []

  for ecosystem in ecosystem_resp:
    ecosystems.append(ecosystem['label'])

  return ecosystems

def processDevActivity(dev_activity_resp, metric = 'commits'): 

  metric = 'weeklycommits' if metric == 'commits' else metric
  
  dev_activity = []

  for ecosystem in dev_activity_resp:
    # -- get protocol name 
    for key in ecosystem.keys():
      if key not in ['date', 'Sub-Ecosystems']:
        protocol = key.split('Core')[0] if 'Core' in key else key
        core_key = key

        protocol = 'All Protocols' if protocol == 'All Commits' else protocol
        protocol = 'All Protocols' if protocol == 'All Devs' else protocol

    # -- add to data list
    data = {
      'date': ecosystem['date'], 
      'protocol': protocol.strip(),
      'metric': metric,
      'core_value': ecosystem[core_key],
    }

    if 'Sub-Ecosystems' in ecosystem.keys(): 
      data['sub_ecosystems_value'] = ecosystem['Sub-Ecosystems']

    dev_activity.append(data)

  if len(dev_activity) == 0:
    return pd.DataFrame()
  
  else:
    df = pd.DataFrame(dev_activity)
    df['date'] = pd.to_datetime(df['date'])
    return df
  
def getApplicationDict(): 

  app_df = pd.read_csv('https://storage.googleapis.com/open_chain_data/artemis/apps.csv')

  # make a json list of the apps with app as the key 
  app_df_temp = app_df.drop_duplicates(subset=['chain', 'application'])
  app_dict = app_df_temp.to_dict('records')

  apps = {}

  for app in app_dict:

    # -- add new app to dict
    if app['application'] not in apps.keys():
      apps[app['application']] = {
        'chains': [app['chain']],
        'category': app['category'],
      }

    # -- add chain to existing app
    else:
      apps[app['application']]['chains'].append(app['chain'])

  return apps

def addAppCategory(protocol, apps, chains):

  if protocol.lower() in chains:
    return 'Network'
  
  else:
    if protocol in apps.keys():
      return apps[protocol]['category']

  return 'Not Available'

def addAppChains(protocol, apps, chains):

  protocol_chains = []

  if protocol.lower() in chains:
    protocol_chains.append(protocol.lower())
  
  if protocol in apps.keys():
    if protocol.lower() not in protocol_chains:
      protocol_chains.extend(apps[protocol]['chains'])

  return protocol_chains

def appendAppInfo(dev_df, chains = []): 

  apps = getApplicationDict()

  # -- add category column
  #dev_df['category'] = dev_df['protocol'].apply(lambda x: apps[x]['category'] if x in apps.keys() else 'Not Available')
  dev_df['category'] = dev_df['protocol'].apply(lambda x: addAppCategory(x, apps, chains))

  # -- add chains column
  #dev_df['chains'] = dev_df['protocol'].apply(lambda x: apps[x]['chains'] if x in apps.keys() else [])
  dev_df['chains'] = dev_df['protocol'].apply(lambda x: addAppChains(x, apps, chains))


  return dev_df