


# -- standard imports 
import pandas as pd
import requests

# -- local imports
from ._api import getAppSummaryTable
from ._processing import getChainMetrics_, getChainActivityByCategory_, getChainActivityByApp_


class Artemis: 
    
  def __init__(self):
    # -- TODO: turn this in a config 

    # -- define valid metrics and chains
    self.valid_metrics = ['DAU', 'DEX_VOLUMES', 'TVL', 'DAILY_TXNS', 'FEES', 'REVENUE', 'STABLECOIN_MC', 'STABLECOIN_GROWTH', 'NEW_TWITTER_FOLLOWERS', 'TWITTER_FOLLOWERS', 'MC', 'PRICE']
    self.valid_chains  = ['aptos','avalanche','ethereum','sui','polygon','solana','arbitrum', 'optimism', 'bsc', 'axelar','zksync','tron','starknet','stacks','polygon_zk','osmosis','near','multiversx','flow','fantom','cosmoshub','cardano','canto','bitcoin', 'base']

    self.valid_chains_bam  = ['arbitrum','avalanche','bsc','ethereum','polygon','optimism']
    self.valid_categories_bam  = ['Bridge','CeFi','DeFi','Gaming','Utility','Layer%202','Memecoin','NFT%20Apps','ERC_721','Social','Stablecoin','ERC_1155','ERC_20','EOA']
    self.valid_metrics_bam = ['activeAddresses', 'transactions', 'gasPaid']
    
    # -- set default chains and metrics 
    self.default_chains = ['avalanche','ethereum','polygon','solana', 'arbitrum', 'optimism', 'bsc', 'base']
    self.defualt_metrics = ['DAU', 'DEX_VOLUMES', 'TVL', 'DAILY_TXNS', 'FEES', 'REVENUE', 'MC', 'STABLECOIN_MC']

    self.default_chains_bam = self.valid_chains_bam
    self.default_categories_bam = self.valid_categories_bam
    self.default_metrics_bam = self.valid_metrics_bam

    # -- initialize api parameters
    self.chains = []
    self.metrics = []
    self.start_date = ''
    self.end_date = ''
    self.days = 180

    self.chains_bam = []
    self.categories = []
    self.metrics_bam = []
    self.apps = []

    self.url_categories = ''
    self.url_apps = ''

    # -- initialize dataframes
    self.chains_df = pd.DataFrame()
    self.categories_df = pd.DataFrame()
    self.apps_df = pd.DataFrame()

    # -- set general defaults
    self.verbose = False
    self.sleep = 0.335

  # ==================================================
  # -- Set Default Parameters
  # ==================================================
  def _setChainDefaults(self):
    # -- set default chains
    if len(self.chains) == 0:
      self.chains = self.default_chains
    else:
      # -- remove chains not in valid chains
      self.chains = [chain.lower() for chain in self.chains]
      self.chains = [chain for chain in self.chains if chain in self.valid_chains]
      # -- if no valid chains, use default chains
      if len(self.chains) == 0:
        print('Warning -- No valid chains provided, using default chains') if self.verbose else None
        self.chains = self.default_chains



  def _setMetricDefaults(self):
    # -- set default metrics 
    if len(self.metrics) == 0:
      self.metrics = self.defualt_metrics
    else:
      # -- remove metrics not in valid metrics
      self.metrics = [metric.upper() for metric in self.metrics]
      self.metrics = [metric for metric in self.metrics if metric in self.valid_metrics]
      # -- if no valid metrics, use default metrics
      if len(self.metrics) == 0:
        print('Warning -- No valid metrics provided, using default metrics') if self.verbose else None
        self.metrics = self.defualt_metrics



  def _setDateDefaults(self):
    # -- set start date to be X days before end date if not provided
    if self.start_date == '':
      self.start_date = (pd.Timestamp.today() - pd.Timedelta(days=self.days)).strftime('%Y-%m-%d')
    
    # -- set end date to be yesterday if not provided
    if self.end_date == '':
      self.end_date = (pd.Timestamp.today() - pd.Timedelta(days=1)).strftime('%Y-%m-%d')



  def _setChainDefaults_BAM(self):
    # -- set default chains
    if len(self.chains_bam) == 0:
      self.chains_bam = self.default_chains_bam
    else:
      # -- remove chains not in valid chains
      self.chains_bam = [chain.lower() for chain in self.chains_bam]
      self.chains_bam = [chain for chain in self.chains_bam if chain in self.valid_chains_bam]
      # -- if no valid chains, use default chains
      if len(self.chains_bam) == 0:
        print('Warning -- No valid chains provided, using default chains') if self.verbose else None
        self.chains_bam = self.default_chains_bam



  def _setCategoryDefaults_BAM(self):
    if len(self.categories) == 0:
      self.categories = self.valid_categories_bam
    else:
      # -- check if chains are valid
      self.categories = [category for category in self.categories if category in self.valid_categories_bam]

      if len(self.categories) == 0:
        print('Warning -- No valid categories provided, using default categories') if self.verbose else None
        self.categories = self.valid_categories_bam
    
    url_categories = str(self.categories).replace('[', '').replace(']', '').replace(' ', '').replace("'", "")

    # -- set url string for categories
    self.url_categories = '&categories=' + url_categories 



  def _setMetricDefaults_BAM(self):

    if len(self.metrics_bam) == 0:
      self.metrics_bam = self.default_metrics_bam
    else:
      # -- check if chains are valid
      self.metrics_bam = [metric for metric in self.metrics_bam if metric in self.valid_metrics_bam]

      if len(self.metrics_bam) == 0:
        print('Warning -- No valid metrics provided, using default metrics') if self.verbose else None
        self.metrics_bam = self.default_metrics_bam

  def _getValidApps(self):
    app_df = getAppSummaryTable()

    # -- filter for valid chains
    app_df = app_df[app_df['chainValue'].isin(self.chains_bam)]

    # -- filter for valid categories
    app_df = app_df[app_df['parentValue'].isin(self.categories)]

    valid_apps = list(app_df['value'].unique())

    return valid_apps
  
  def _buildAppUrl(self, apps):
    url_apps = str(apps).replace('[', '').replace(']', '').replace(' ', '').replace("'", "")

    # -- create filter 
    self.url_apps = '&applications=' + url_apps

    return self.url_apps

  def _setAppDefaults(self, app_limit = 25):
    app_df = getAppSummaryTable()

    # -- filter for valid chains
    app_df = app_df[app_df['chainValue'].isin(self.chains_bam)]

    # -- filter for valid categories
    app_df = app_df[app_df['parentValue'].isin(self.categories)]

    valid_apps = list(app_df['value'].unique())

    # -- get valid apps
    valid_apps = self._getValidApps()

    if len(self.apps) == 0:
      valid_apps = valid_apps[:app_limit]
      url_apps = str(valid_apps).replace('[', '').replace(']', '').replace(' ', '').replace("'", "")

    else:
      # -- check if chains are valid
      self.apps = [app for app in self.apps if app in valid_apps]

      if len(self.apps) == 0:
        print('Warning -- No valid app provided, using default apps') if self.verbose else None
        self.apps = valid_apps[:app_limit]
    
      url_apps = str(self.apps).replace('[', '').replace(']', '').replace(' ', '').replace("'", "")

    # -- create filter 
    self.url_apps = '&applications=' + url_apps 

  


  # ==================================================
  # -- Execute API Calls + Process Data (Core Functions)
  # ==================================================

  # -- TODO: change function name 
  def getChainMetrics(self, chains = list(), metrics = list(), start_date = '', end_date = '', days = 180): 
    # -- Returns df of chain metrics with columns: ['date', 'chain', 'metric', 'value']
    # ---- > Logic: 1) Set api params in object state. 2) edit params in state to be defaults if not provided. 3) call api. 4) process data. 5) return df
    
    # -- set api parameters 
    self.chains = chains
    self.metrics = metrics
    self.start_date = start_date
    self.end_date = end_date
    self.days = days

    # -- TODO: change names to 'check' and fuck off with state updates 
    # -- set api params defaults if not provided
    self._setChainDefaults()
    self._setMetricDefaults()
    self._setDateDefaults()

    # -- get data from artemis
    df = getChainMetrics_(self.chains, self.metrics, self.start_date, self.end_date)
    self.chains_df = df

    return df
  
  def getChainActivityByCategory(self, chains = list(), categories = list(), metrics = list(), start_date = '', days = 180, exclude_category = False): 
    # -- Returns df of chain metrics with columns: ['date', 'chain', 'metric', 'category', 'value']
    # ---- > Logic: 1) Set api params in object state. 2) edit params in state to be defaults if not provided. 3) call api. 4) process data. 5) return df

    # -- set api params defaults if not provided
    self.chains_bam = chains
    self.categories = categories
    self.metrics_bam = metrics

    self.start_date = start_date
    self.days = days

    # -- set defaults if not provided
    self._setChainDefaults_BAM()
    self._setCategoryDefaults_BAM() if exclude_category == False else None
    self._setMetricDefaults_BAM()
    self._setDateDefaults()

    # -- get data from artemis
    df = getChainActivityByCategory_(self.chains_bam, self.metrics_bam, self.start_date, self.url_categories, self.sleep)
    self.categories_df = df

    return df
  
  def getChainActivityByApp_(self, chains = [], categories = [], metrics = [], apps = [], start_date = '', days = 180, app_limit = 25, exclude_category = False): 
    # -- Returns df of chain metrics with columns: ['date', 'chain', 'metric', 'category', 'application', 'value']
    # ---- > Logic: 1) Set api params in object state. 2) edit params in state to be defaults if not provided. 3) call api. 4) process data. 5) return df

    # -- set api params defaults if not provided
    self.chains_bam = chains
    self.categories = categories
    self.metrics_bam = metrics
    self.apps = apps

    self.start_date = start_date
    self.days = days

    # -- set defaults if not provided
    self._setChainDefaults_BAM()
    self._setCategoryDefaults_BAM() if exclude_category == False else None
    self._setMetricDefaults_BAM()
    self._setDateDefaults()
    self._setAppDefaults(app_limit)

    # -- get data from artemis
    df = getChainActivityByApp_(self.chains_bam, self.metrics_bam, self.start_date, self.url_categories, self.url_apps, self.sleep)
    self.apps_df = df

    return df
  
  def getChainActivityByApp(self, chains = [], categories = [], metrics = [], apps = [], start_date = '', days = 180, app_limit = 25, exclude_category = False): 
    # -- Returns df of chain metrics with columns: ['date', 'chain', 'metric', 'category', 'application', 'value']
    # ---- > Logic: 1) Set api params in object state. 2) edit params in state to be defaults if not provided. 3) call api. 4) process data. 5) return df

    # -- set api params defaults if not provided
    self.chains_bam = chains
    self.categories = categories
    self.metrics_bam = metrics
    self.apps = apps

    self.start_date = start_date
    self.days = days

    # -- set defaults if not provided
    self._setChainDefaults_BAM()
    self._setCategoryDefaults_BAM() if exclude_category == False else None
    self._setMetricDefaults_BAM()
    self._setDateDefaults()
    
    # -- get valid apps
    valid_apps = self._getValidApps()

    # -- break up into chunks of 100
    chunks = [valid_apps[x:x+100] for x in range(0, len(valid_apps), 100)]

    # -- get app df for each chunk
    dfs = []

    for chunk in chunks:
      url_apps = self._buildAppUrl(chunk)
      df = getChainActivityByApp_(self.chains_bam, self.metrics_bam, self.start_date, self.url_categories, url_apps, self.sleep)

      dfs.append(df)

    # -- concat into one df
    df = pd.concat(dfs)
    self.apps_df = df

    return df
  

  


    