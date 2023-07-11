from ponzu.llama.llama import Llama



def test_llama_chain_df():
  # -- initialize object 
  llama = Llama()
  # -- get chain df 
  chains = ['optimism'] # limit run time 
  df = llama.getChainTVL(chains=chains)
  assert len(df) > 0


def test_llama_fundamentals(): 
  # -- initialize object 
  llama = Llama()

  # -- define params
  chains = ['Optimism'] 
  metrics = ['fees', 'tvl', 'borrowed']

  df = llama.getChainFundamentals(chains = chains, metrics = metrics)

  assert len(df) > 0


def test_llama_yields():
  # -- initialize object 
  llama = Llama()

  # -- define params
  projects = ['aave']
  chains = ['Ethereum']
  tokens = ['STETH']

  df = llama.getHistoricalYields(protocols= projects, chains = chains, tokens = tokens)

  assert len(df) > 0

def test_llama_stables():
  # -- initialize object 
  llama = Llama()

  df = llama.stablecoins()

  assert len(df) > 0

def test_llama_stables_history():
  # -- initialize object 
  llama = Llama()

  df = llama.stablecoinHistory(mcap_threshold = 500000000)

  assert len(df) > 0