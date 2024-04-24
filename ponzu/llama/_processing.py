


# -- standard imports 
import pandas as pd
import aiohttp
import asyncio
import time

# -- local imports
from ._api import getProtocols_api, getProtocol_api, getProtocol_async_api, getProtocolsData_, getChains_api
from ._api import getFundamentalsByChain_api, getFundamentalsByProtocol_api
from ._helpers import remapCategories, aggTVLtypes, parseTVLtype, getSubprotocolCategory, getExcludedTVLsubtypes, unpackProtocols, getMetricTypeDefaults


# ==================================================
# -- TVL 
# ==================================================

def filterProtocols_(df = '', tvl_cutoff = 0, chains = [], protocols = [], includeMultiChain = True, categories = [], exclude_categories = ['CEX', 'Chain']):

  if len(df) < 1:
    df = getProtocols_api()

  # -- filter by tvl
  df = df[df['tvl'] >= tvl_cutoff]

  # -- remap categories 
  df = remapCategories(df)

  # -- filter by protocol
  if len(protocols) > 0:
    #df['parentProtocol'] = df['parentProtocol'].apply(lambda x: str(x))
    df['parentProtocol'] = df['parentProtocol'].apply(lambda x: str(x).split('#')[-1])
    df['parentProtocol'] = df['parentProtocol'].apply(lambda x: x.lower())
    protocols = [protocol.lower() for protocol in protocols]
    df = df[(df['parentProtocol'].isin(protocols)) | (df['slug'].isin(protocols))]

  # -- filter by category
  if len(categories) > 0:
    df = df[df['category'].isin(categories)]

  # -- filter by exclude category
  if len(exclude_categories) > 0:
    df = df[~df['category'].isin(exclude_categories)]

  # -- print chains where the type is not a string
  #print('Length of chains: ', len(df['chain'].unique())) if len(df['chain'].unique()) > 0 else None
  #print('Length of nan chains: ', len(df[df['chain'].isna()])) if len(df[df['chain'].isna()]) > 0 else None

  # -- convert chains to string
  df['chain'] = df['chain'].apply(lambda x: str(x))


  bad_chains = []
  for chain in df['chain'].unique():
    if type(chain) != str:
      bad_chains.append({chain: type(chain)})
  
  print(bad_chains) if len(bad_chains) > 0 else None

  #  -- make chains lower case
  chains = [chain.lower() for chain in chains]
  df['chain'] = df['chain'].apply(lambda x: x.lower())

  # -- filter by chain
  if len(chains) > 0:
    # -- print warning if chain is not in df
    for chain in chains:
      if chain not in df['chain'].unique():
        #print(f'Warning: {chain} not in df')
        None 
    
    # -- filter df by chains
        
    # ... old code: added multi-chain back to chains. resulted in long code execution thats not necessary
    #chains.append('multi-chain') if includeMultiChain else None
    #df = df[df['chain'].isin(chains)]
        
    # -- make lowercase all chains 
    df['chains'] = df['chains'].apply(lambda x: [item.lower() for item in x])

    # -- filter protocol df if any of the included chains are in the chains column
    df = df[df['chains'].apply(lambda x: any(item in x for item in chains))]

  return df

def processProtocolData_(protocol_data, chains, protocols_df, aggregateTVLtypes = False, token_level = False): 
  # -- initialize data store 
  data_ = []

  for protocol_ in protocol_data:
    protocol = protocol_['protocol']
    data = protocol_['data']

    # -- remove sub tvl types
    if 'currentChainTvls' in data.keys():
      exlcuded_subtypes = getExcludedTVLsubtypes(data) # unpack tvl sub types to exclude (e.g. total borrowed. we want chain specific borrowed for example)
    else:
      exlcuded_subtypes = []
      print(f'Warning: {protocol} does not have currentChainTvls')

    # -- get category if not already set
    if 'category' not in data.keys() and 'otherProtocols' in data.keys():
      data['category'] = getSubprotocolCategory(data, protocols_df)

    if 'parentProtocol' not in data.keys():
      data['parentProtocol'] = protocol
    else:
      data['parentProtocol'] = data['parentProtocol'].split('#')[-1]

    for type_, tvl_data in data['chainTvls'].items():
      # -- parse type and chain 
      tvl_type, chain_ = parseTVLtype(type_)

      # -- unpack data if not an excluded subtype
      if chain_ not in exlcuded_subtypes:
        if token_level:
          if 'tokensInUsd' in tvl_data.keys():
            for dailyData in tvl_data['tokensInUsd']:
              for token, value in dailyData['tokens'].items():
                data_.append({
                  'date': dailyData['date'],
                  'chain': chain_,
                  'protocol': protocol,
                  'parentProtocol': data['parentProtocol'],
                  'category': data['category'],
                  'type': tvl_type,
                  'token': token,
                  'tvl': value
                  })
          else:  
            for dailyData in tvl_data['tvl']:
              data_.append({
                'date': dailyData['date'],
                'chain': chain_,
                'protocol': protocol,
                'parentProtocol': data['parentProtocol'],
                'category': data['category'],
                'type': tvl_type,
                'token': 'none',
                'tvl': dailyData['totalLiquidityUSD']
                })
        else:
          for dailyData in tvl_data['tvl']:
            data_.append({
              'date': dailyData['date'],
              'chain': chain_,
              'protocol': protocol,
              'parentProtocol': data['parentProtocol'],
              'category': data['category'],
              'type': tvl_type,
              'tvl': dailyData['totalLiquidityUSD']
              })
          
  # -- convert to dataframe
  df = pd.DataFrame(data_)

  # -- filter by chain 
  if len(chains) > 0:
    chains = [chain.lower() for chain in chains]
    df = df[df['chain'].isin(chains)]

  df['date'] = pd.to_datetime(df['date'], unit='s', utc=True)

  # -- drop rows with date with hour and mintues greater than 0 
  df = df[df['date'].dt.hour == 0]
  df = df[df['date'].dt.minute == 0]

  df = remapCategories(df)

  if aggregateTVLtypes:
    df = aggTVLtypes(df)

  return df 


# ==================================================
# -- Fundamental Metrics
# ==================================================

def getFundamentalsByChain_(chain, metric = 'fees'):
  # -- make chain lower case
  chain = chain.lower()

  # -- call api
  data = getFundamentalsByChain_api(chain, metric)

  return data

def processFundamentalsByChain_(data, chain, metric = 'fees'):
  # -- convert to df 
  df = pd.DataFrame(data['totalDataChartBreakdown'])

  # -- format df columns
  df.columns = ['date', metric]
  df['date'] = pd.to_datetime(df['date'], unit='s', utc=True)
  df['date'] = pd.to_datetime(df['date'])

  # -- unpack protocols
  data_ = []
  df.apply(lambda row: data_.extend(unpackProtocols(row['date'], row[metric], chain, metric)), axis=1)

  df_ = pd.DataFrame(data_)

  # -- exit if no data
  if df_.empty: 
    print(f'warning: no data for {chain} {metric}')
    print(data)
    # -- add columns ['date', 'chain', 'protocol', 'parentProtocol', 'category', 'metric', 'value']
    df_ = pd.DataFrame(columns = ['date', 'chain', 'protocol', 'parentProtocol', 'category', 'metric', 'value'])
    return df_

  # -- add category column and parent column 
  protocol_data = {}
  for protocol in data['protocols']: 
    key = protocol['displayName']
    parent = protocol['parentProtocol'].split('#')[-1] if 'parentProtocol' in protocol.keys() else protocol['module']

    protocol_data[key] = {'category': protocol['category'], 'parentProtocol': parent}

    # -- ghetto clean bsc data 
    if chain == 'bsc' and metric == 'volume':
      key = protocol['module']
      protocol_data[key] = {'category': protocol['category'], 'parentProtocol': parent}


  df_['category'] = df_['protocol'].apply(lambda protocol: protocol_data[protocol]['category'] if protocol in protocol_data.keys() else 'unknown')
  df_['parentProtocol'] = df_['protocol'].apply(lambda protocol: protocol_data[protocol]['parentProtocol'] if protocol in protocol_data.keys() else 'unknown')


  # -- reorder columns
  df_ = df_[['date', 'chain', 'protocol', 'parentProtocol', 'category', 'metric', 'value']]

  return df_


def processFundamentalsByProtocol_(data, metric = 'fees'):
  # -- convert to df
  df = data['totalDataChart']

  # -- format df columns
  df.columns = ['date', metric]
  df['date'] = pd.to_datetime(df['date'], unit='s', utc=True)
  df['date'] = pd.to_datetime(df['date'])

  return df

def getChainMetrics_(chains, metrics, sleep = 1): 
  # -- initialize 
  dfs = []

  # -- loop through chains
  for metric in metrics:
    for chain in chains:
      # -- call api
      df = getFundamentalsByChain_(chain, metric)

      # -- process api data 
      df = processFundamentalsByChain_(df, chain, metric)

      # -- add chain column
      df['chain'] = chain

      # -- add metric column
      df['type'] = metric

      dfs.append(df)

      # -- sleep
      time.sleep(sleep)

  # -- concat all dataframes
  df = pd.concat(dfs)

  # -- reorder and rename columns 
  df.columns = ['date', 'chain', 'protocol', 'value', 'type']
  df = df[['date', 'chain', 'protocol', 'type', 'value']]

  return df

def combineTVLandMetrics_(tvl_df, metrics_df, metrics): 
  # -- check if tvl_df is empty
  if len(tvl_df) < 1:
    return metrics_df
  
  # -- check if metrics_df is empty
  if len(metrics_df) < 1:
    return tvl_df
  
  # -- rework tvl df to match metrics df columns
  #tvl_df = tvl_df.drop(columns = ['category'])
  tvl_df = tvl_df.rename(columns = {'tvl': 'value'}) 

  # -- filter tvl types to only include metrics 
  tvl_df = tvl_df[tvl_df.type.isin(metrics)]

  # -- concat dataframes
  df = pd.concat([tvl_df, metrics_df])

  return df 

# ==================================================
# -- Yields
# ==================================================

def getYieldsDataframe(data):
  df = pd.DataFrame(data['data'])

  return df 

def filterYieldPools_(pools_df_, tvl_cutoff = 1000000, chains = [], tokens = [], protocols = []): 
  pools_df = pools_df_.copy()
  # -- filter pools by chains, symbol, and tvl if specified
  pools_df = pools_df[pools_df.tvlUsd >= tvl_cutoff]

  #  -- make chains lower case
  chains = [chain.lower() for chain in chains]
  pools_df.loc[:, 'chain'] = pools_df.chain.apply(lambda x: x.lower())

  #  -- make protocols lower case
  protocols = [protocol.lower() for protocol in protocols]
  pools_df.loc[:, 'project'] = pools_df['project'].apply(lambda x: x.lower())

  # -- filter by chains, tokens, and projects if specified
  if len(chains) > 0:
    pools_df = pools_df[pools_df.chain.isin(chains)]

  if len(tokens) > 0:
    pools_df = pools_df[pools_df.symbol.str.contains('|'.join(tokens))]

  if len(protocols) > 0:
    pools_df = pools_df[pools_df.project.str.contains('|'.join(protocols))]

  return pools_df

def removePoolDataErrors(pools_list): 
  good_pools = []
  for pool_data_ in pools_list:
    if type(pool_data_) == dict:
      good_pools.append(pool_data_)
  
  return good_pools

def getBadPoolIds(pools_list):
  bad_ids = []

  for pool_data_ in pools_list:
    if type(pool_data_) != dict:
      bad_ids.append(pool_data_)

    elif 'data' in pool_data_.keys(): 
      if pool_data_['data'] is None:
        bad_ids.append(pool_data_['pool_id'])

  return bad_ids

def processPoolData_(pools_list, pools_df): 
  # -- initialize data store
  dfs = []

  # -- clean data
  pools_list = removePoolDataErrors(pools_list)

  # -- loop through pools
  for pool_data_ in pools_list:

    pool_id = pool_data_['pool_id']
    pool_data = pool_data_['data']

    # -- create df from pool data
    df = pd.DataFrame(pool_data['data'])

    # -- get pool info from pools_df
    pool_info = pools_df[pools_df.pool == pool_id].to_dict(orient='records')[0]

    # -- add pool info to df
    df['pool'] = pool_info['pool'] if 'pool' in pool_info.keys() else pool_id
    df['chain'] = pool_info['chain'] if 'chain' in pool_info.keys() else 'unknown'
    df['project'] = pool_info['project'] if 'project' in pool_info.keys() else 'unknown'
    df['symbol'] = pool_info['symbol'] if 'symbol' in pool_info.keys() else 'unknown'
    df['stablecoin'] = pool_info['stablecoin'] if 'stablecoin' in pool_info.keys() else 'unknown'
    df['rewardTokens'] = str(pool_info['rewardTokens']) if 'rewardTokens' in pool_info.keys() else 'unknown'
    df['underlyingTokens'] = str(pool_info['underlyingTokens']) if 'underlyingTokens' in pool_info.keys() else 'unknown'

    # -- convert timestamp to datetime
    df['date'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['date'].dt.date

    # -- move date, chain,	project, and	symbol columns to front of the df
    cols = df.columns.tolist()
    start_cols = ['date', 'chain', 'project', 'symbol']

    cols = start_cols + [col for col in cols if col not in start_cols]

    df = df[cols]

    # -- append to data store
    dfs.append(df)

  # -- concat dataframes
  df = pd.concat(dfs)

  return df

# ==================================================
# -- Stables 
# ==================================================

def buildStablecoinPriceDict_(data): 
  data_ = {}

  for dailyData in data:
    data_[dailyData['date']] = dailyData['prices']

  # -- return dict 
  return data_

def processStablesList_(data): 
  # -- unpack data
  data_ = []

  for stable in data['peggedAssets']:
    if 'peggedUSD' in stable['circulating'].keys() or 'peggedEUR' in stable['circulating'].keys():

      price = stable['price'] if stable['price'] is not None else 1
      #stable['chains'] = [chain.lower() for chain in stable['chains']]

      # -- get peg key 
      peg_key = stable['pegType'] if 'pegType' in stable.keys() else 'peggedUSD'

      data_.append({
        'id': stable['id'],
        'gecko_id': stable['gecko_id'],
        'symbol': stable['symbol'],
        'mcap': float(stable['circulating'][peg_key]) * float(price),
        'supply': stable['circulating'][peg_key] ,
        'pegMechanism': stable['pegMechanism'],
        'priceSource': stable['priceSource'],
        'pegType': stable['pegType'],
        'chains': stable['chains'],
        'price': stable['price'],
        })

  return data_

def processStablesHistory(stables, data, price_dict):
  data_store = []

  for stable in stables:
    for stable_data in data: 
      if stable_data['stable_id'] == stable['id']: 

        peg_key = stable_data['data']['pegType'] if 'pegType' in stable_data['data'].keys() else 'peggedUSD'

        for chain, timeseries in stable_data['data']['chainBalances'].items():
          for dailyData in timeseries['tokens']:
            if str(dailyData['date'])[-1] == '0' and dailyData['date'] in price_dict.keys():
              price = price_dict[dailyData['date']][stable['gecko_id']] if stable['gecko_id'] in price_dict[dailyData['date']].keys() else 1
              price = price if price is not None else 1

              # -- 

              data_store.append({
                'date': dailyData['date'],
                'symbol': stable['symbol'],
                'chain': chain,
                'supply': dailyData['circulating'][peg_key],
                'price': price,
                'mcap': float(dailyData['circulating'][peg_key]) * float(price),
                })

  # -- convert to df
  df = pd.DataFrame(data_store)

  # -- convert date to datetime
  df['date'] = pd.to_datetime(df['date'], unit='s')

  return df 

def processStablesChartHistory(stables, data, price_dict):
  data_store = []

  for stable in stables:
    for stable_data in data: 
      for daily_data in stable_data['data']:
        if stable_data['stable_id'] == stable['stable_id']: 

          # -- get peg key 
          peg_key = daily_data['pegType'] if 'pegType' in daily_data.keys() else 'peggedUSD'

          data_store.append({
            'date': daily_data['date'],
            'symbol': stable['symbol'],
            'chain': stable_data['chain'],
            'supply': daily_data['totalCirculating'][peg_key],
            'supplyUSD': daily_data['totalCirculatingUSD'][peg_key], 
            })


  df = pd.DataFrame(data_store)

  # -- convert date to datetime
  df['date'] = pd.to_datetime(df['date'], unit='s')

  return df 

