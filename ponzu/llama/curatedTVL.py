class TVLData(Llama):
    def __init__(self):
        super().__init__()  # call Llama's __init__ method
        self.raw_tvl_data = None
        self.curated_raw_tvl_data = None

    def raw_tvl(self, chains):
        df = self.getChainTVL(chains)  # use self to call getChainTVL 
method synchronously
        self.raw_tvl_data = df
        return df

    def recategorize_protocols(self):
        self.raw_tvl_data.loc[self.raw_tvl_data['protocol'] == 'eos-rex', 
'category'] = 'Liquid Staking'
        self.raw_tvl_data.loc[self.raw_tvl_data['protocol'] == 
'atomichub', 'category'] = 'NFT Marketplace'

    def filter_by_type(self):
        return self.raw_tvl_data[(self.raw_tvl_data['type'] == 'tvl') | 
(self.raw_tvl_data['type'] == 'borrowed')]

    def filter_by_category_and_protocol(self, df):
        exclude_categories = ['CEX', 'Chain', 'Yield', 'Bridge', 'Liquid 
Staking', 'Liquidity manager', 'RWA', 'Gaming', 'NFT Marketplace', 
'Leveraged Farming', 'Prediction Market']
        df = df[~df['category'].isin(exclude_categories)]
        exclude_protocols = 
['ribbon','frax','unslashed','sturdy','alongside','illuminate','instadapp','defisaver','pooltogether','cian','ubiquity-dao','sandclock','templedao','unbound','axia-protocol','tornado-cash','aztec','tronnrg','garble.money','sperax-demeter','volta-finance','uniwswap-unia-farms','mm-stableswap-polygon','zkbob','brokkr-finance','defrost','sherpa-cash','sturdy','shadecash','zeta']
        df = df[~df['protocol'].isin(exclude_protocols)]
        return df

    def curated_raw_tvl(self, chains):
        curated_chains = 
['ethereum','tron','binance','arbitrum','polygon','optimism','avalanche','fantom','solana','cardano','eos','tezos','aptos','near','stacks','sui','hedera','aurora','eos 
evm','wax','europa']
        for chain in chains:
            if chain not in curated_chains:
                return f"Error: {chain} is not in the curated list of 
chains." 
        if self.raw_tvl_data is None:
            self.raw_tvl(chains)
        
        self.recategorize_protocols()
        df_tvl = self.filter_by_type()
        df_tvl = self.filter_by_category_and_protocol(df_tvl)
        self.curated_raw_tvl_data = df_tvl
        return df_tvl 



