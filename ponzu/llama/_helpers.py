# -- standard imports
import pandas as pd 

import asyncio
import aiohttp
import threading

# -- local imports
#from ._api import getProtocol_api



# ==================================================
# -- Protocol TVL Helpers
# ==================================================

def remapCategories(df):
  # -- remap categories for protocols df
  remap_categories = {
    'CDP': 'Stables', 
    'Algo-Stables': 'Stables', 
    'Yield Aggregator': 'Yield',
    'Dexes': 'DEX'
  }

  df['category'] = df['category'].apply(lambda x: remap_categories[x] if x in remap_categories.keys() else x)

  return df


def parseTVLtype(type_):
  if '-' in type_:
    tvl_type = type_.split('-')[1].lower()
    chain_ = type_.split('-')[0].lower()
  else:
    tvl_type = 'tvl'
    chain_ = type_.lower()

  return tvl_type, chain_


def getSubprotocolCategory(protocol_data, protocols_df):
  #sub_protocol = protocol['otherProtocols'][-1]
  #sub_protocol_data = getProtocol_api(sub_protocol)
  #category = sub_protocol_data['category']

  #category = protocol_df[protocol_df.protocol == protocol]['category'].values[0]
  if protocol_data['id'] in protocols_df.parentProtocol.unique():
    categories = protocols_df[protocols_df.parentProtocol == protocol_data['id']].category.unique()

    if len(categories) == 1:
      category = categories[0]
    else:
      category = str(categories).replace('[', '').replace(']', '').replace(' ', '').replace("'", "")
  
  else:
    raise ValueError(f'No category found for {protocol_data["name"]}')

  return category


def getExcludedTVLsubtypes(protocol_data):
  exlcuded_subtypes = []
  for chain_ in protocol_data['currentChainTvls'].keys():
    if '-' in chain_:
      exlcuded_subtypes.append(chain_.split('-')[1].lower()) if chain_.split('-')[1].lower() not in exlcuded_subtypes else None

  return exlcuded_subtypes



def aggTVLtypes(df, include = ['borrowed']):
  dfs = []

  for protocol in df.protocol.unique():
    df_ = df[df.protocol == protocol]
    df_unstacked = df_.groupby(['date','type'])['tvl'].sum().unstack()
    df_unstacked = df_unstacked.fillna(0)

    # -- include or exclude types from tvl calculation
    if 'tvl' in df_unstacked.columns:
      for col in df_unstacked.columns:
        #if col != 'tvl' and col not in include:
          #df_unstacked['tvl'] = df_unstacked['tvl'] - df_unstacked[col] if col != 'borrowed' else df_unstacked['tvl']
          # -- don't need to substract borrow tvl from tvl because it is already substracted from total tvl

        if col != 'tvl' and col in include:
          df_unstacked['tvl'] = df_unstacked['tvl'] + df_unstacked[col]

      df_unstacked = df_unstacked.drop(columns = [col for col in df_unstacked.columns if col != 'tvl'])

      # -- get values for columns 
      df_unstacked['chain'] = df_.chain.unique()[0]
      df_unstacked['protocol']  = df_.protocol.unique()[0]
      df_unstacked['category']  = df_.category.unique()[0]
      df_unstacked['type']  = 'tvl'

      # -- reorder columns
      df_unstacked = df_unstacked.reset_index()[['date', 'chain', 'protocol', 'category', 'type', 'tvl']]

      dfs.append(df_unstacked)

  df = pd.concat(dfs)
  return df


# ==================================================
# -- Fundamental Metrics Helpers
# ==================================================


def getMetricTypeDefaults(metric):
  metrics = {
    'fees': ('dailyFees', 'fees'),
    'revenue': ('dailyRevenue', 'fees'),
    'volume': ('dailyVolume', 'dexs'),
  }

  metric = metrics[metric][0] if metric in metrics.keys() else 'dailyFees'
  metric_type = metrics[metric][1] if metric in metrics.keys() else 'fees'
  
  return metric, metric_type


def unpackProtocols(date_, protocols_, chain, metric):
  unpacked = []
  for protocol, value in protocols_.items():
    unpacked.append({
      'date': date_,
      'chain': chain,
      'protocol': protocol,
       metric: value
    })
    
  return unpacked

# ==================================================
# -- Stablecoin Helpers
# ==================================================

def getStablecoinDefaults(stable_objects, supply_cuttoff = 500000000):
  defualt_stables = []

  for stable in stable_objects:
    if stable['supply'] >= supply_cuttoff:
      defualt_stables.append(stable)

  return defualt_stables

def filterStablesbySymbol(stables, symbols):
  filtered_stables = []

  for stable in stables:
    if stable['symbol'] in symbols:
      filtered_stables.append(stable)

  return filtered_stables

def filterStablesbyChains(stables, chains):
  filtered_stables = []

  for stable in stables:
    inlcuded = False

    for chain in chains:
      if chain in stable['chains']:
        inlcuded = True

    if inlcuded:
      filtered_stables.append(stable)

  return filtered_stables

def filterValidStables(valid_stables, chains, stables, mcap_threshold):
  # -- filter valid stables for stables provided or use default stables
  if len(stables) > 0 and len(chains) > 0:
    stable_objects = filterStablesbySymbol(valid_stables, stables)
    stable_objects = filterStablesbyChains(stable_objects, chains)

  elif len(stables) > 0:
    stable_objects = filterStablesbySymbol(valid_stables, stables)
  
  elif len(chains) > 0:
    stable_objects = filterStablesbyChains(valid_stables, chains)

  else:
    stable_objects = getStablecoinDefaults(valid_stables, mcap_threshold)

  return stable_objects

def removeBadStables(stables):
  bad_stable_ids = ['67', '38'] # -- BEAN money has a bad history end point 

  filtered_stables = []

  for stable in stables:
    if stable['id'] not in bad_stable_ids:
      filtered_stables.append(stable)

  return filtered_stables

def buildStableHistoryAPIinputs(stables, chains): 
  inputs = []

  for stable in stables: 
    for chain in chains:
      if chain in stable['chains']:
        inputs.append({'chain': chain, 'stable_id': stable['id'], 'symbol': stable['symbol']})

  return inputs
  

# ==================================================
# -- Async Helpers (execute in thread if already in event loop i.e. jupyter notebook)
# ==================================================

class RunThread(threading.Thread):
    def __init__(self, func, args, kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.result = None
        super().__init__()

    def run(self):
        self.result = asyncio.run(self.func(*self.args, **self.kwargs))

def run_async(func, *args, **kwargs):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        thread = RunThread(func, args, kwargs)
        thread.start()
        thread.join()
        return thread.result
    else:
        return asyncio.run(func(*args, **kwargs))
