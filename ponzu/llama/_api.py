
# -- standard imports 
import requests
import pandas as pd 
from datetime import datetime
import time 

import asyncio
import aiohttp

from retry import retry

#sem = asyncio.Semaphore(8)

# -- local imports
from ._helpers import getMetricTypeDefaults

# ==================================================
# -- Protocols + Chains 
# ==================================================

@retry(ValueError, tries=3, delay=3)
def getProtocols_api():
  url = 'https://api.llama.fi/protocols' 

  resp = requests.get(url)
  data = resp.json()

  if type(data) != list:
    raise ValueError('Protocols API did not return list.')
  
  if 'id' not in data[0].keys():
    raise ValueError('Protocols API did not return list.')

  df = pd.DataFrame(data)

  return df 

@retry(ValueError, tries=3, delay=3)
def getChains_api():
  url = 'https://api.llama.fi/v2/chains'

  resp = requests.get(url)
  data = resp.json()

  if type(data) != list:
    raise ValueError('Chains API did not return list.')
  
  if 'tvl' not in data[0].keys():
    raise ValueError('Chains API did not return correct values.')

  df = pd.DataFrame(data)

  return df


# ==================================================
# -- TVLs
# ==================================================

def getProtocol_api(protocol):
  url = f'https://api.llama.fi/protocol/{protocol}'
  resp = requests.get(url)
  data = resp.json()

  return data


async def getProtocol_async_api(session, sem , protocol):
  url = f'https://api.llama.fi/protocol/{protocol}'
  async with sem:
    async with session.get(url) as resp:
      data = await resp.json()

  data = {'protocol': protocol, 'data': data}

  return data

async def getProtocolsData_(protocols): 
  sem = asyncio.Semaphore(8)

  async with aiohttp.ClientSession() as session:
    data = []
    for protocol in protocols:
      # -- used to have a try, except here but trying to avoid that
      data.append(
        asyncio.ensure_future(getProtocol_async_api(session, sem, protocol))
      )
    
    protocol_data = await asyncio.gather(*data)

  return protocol_data

# ==================================================
# -- Fundamental Metrics
# ==================================================

def getFundamentalsByChain_api(chain, metric = 'fees'):
  # -- get metric and metric type
  metric, metric_type = getMetricTypeDefaults(metric)

  # -- build url
  url = f'https://api.llama.fi/overview/{metric_type}/{chain}?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=false&dataType={metric}'

  # -- call url
  resp = requests.get(url)
  data = resp.json()

  return data 

def getFundamentalsByProtocol_api(protocol, metric = 'fees'):
  # -- get metric and metric type
  metric, metric_type = getMetricTypeDefaults(metric)

  vol_url_filters = 'excludeTotalDataChart=true&excludeTotalDataChartBreakdown=false&' if metric_type == 'dexs' else ''

  # -- build url
  url = f'https://api.llama.fi/summary/{metric_type}/{protocol}?{vol_url_filters}dataType={metric}'

  # -- call url
  resp = requests.get(url)
  data = resp.json()

  return data


# ==================================================
# -- Stables
# ==================================================


def getStablecoinPrices_api(): 
  url = 'https://stablecoins.llama.fi/stablecoinprices'
  resp = requests.get(url)
  data = resp.json()

  return data

def getStablesList_api(): 
  url = f'https://stablecoins.llama.fi/stablecoins?includePrices=true'
  resp = requests.get(url)
  data = resp.json()

  return data

def getStablecoinHistory_api_(stable_id):
  url = f'https://stablecoins.llama.fi/stablecoin/{stable_id}'

  resp = requests.get(url)
  data = resp.json()

  return data

@retry(ValueError, tries=3, delay=5)
async def getStablecoinHistory_api(session, sem, stable_id):
  url = f'https://stablecoins.llama.fi/stablecoin/{stable_id}'

  async with sem:
    async with session.get(url) as resp:
      data = await resp.json()

  data_ = {'stable_id': stable_id, 'data': data}

  if type(data_['data']['chainBalances']) != dict:
    raise ValueError('Stablecoins API returned an error. Please check your inputs and try again.')

  return data_

async def getStablecoinsHistory_(stables): 
  sem = asyncio.Semaphore(8)

  async with aiohttp.ClientSession() as session:
    data = []
    for stable in stables:
      stable_id = stable['id']

      data.append(
        asyncio.ensure_future(getStablecoinHistory_api(session, sem, stable_id))
      )
    
    stablecoin_data = await asyncio.gather(*data)

    if type(stablecoin_data) != list:
      raise ValueError('Stablecoin History API did not return list.')

  return stablecoin_data


# ==================================================
# -- Yields
# ==================================================

@retry(ValueError, tries=3, delay=3)
def getYieldPools_api(): 
  url = 'https://yields.llama.fi/pools'

  resp = requests.get(url)
  data = resp.json()

  if 'data' not in data.keys():
    raise ValueError('Yields API returned an error. Please check your inputs and try again.')

  return data

@retry(ValueError, tries=3, delay=5)
async def getYieldHistorical_async(session, sem, pool_id): 
  url = f'https://yields.llama.fi/chart/{pool_id}'

  async with sem:
    #await asyncio.sleep(1)  # -- TODO set the semaphore to the amount of requests per second and always sleep 1 second
    #print(f" sdsdsd {len(asyncio.all_tasks())}")}")
    async with session.get(url) as resp:
      data = await resp.json()

  data = {'pool_id': pool_id, 'data': data}

  if type(data['data']['data']) != list :
    print('data type not list: ' + url)
    raise ValueError('Yields API returned an error. Please check your inputs and try again.')

  return data

async def getPoolsHistoricalYields_api(pool_ids, sleep = 0.128): 
  sem = asyncio.Semaphore(8)

  async with aiohttp.ClientSession() as session:
    data = []
    for pool_id in pool_ids:
      data.append(asyncio.ensure_future(getYieldHistorical_async(session, sem, pool_id)))
      time.sleep(sleep)
    
    pool_data = await asyncio.gather(*data, return_exceptions=True)

  if type(pool_data) != list:
    raise ValueError('Pools API did not return list.')

  return pool_data

# ==================================================
# -- Raises
# ==================================================



# ==================================================
# -- NFTs
# ==================================================



# ==================================================
# -- Treasury
# ==================================================



# ==================================================
# -- Costs 
# ==================================================

