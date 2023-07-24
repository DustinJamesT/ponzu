from llama.llama import Llama
import pandas as pd

class CuratedTVL(Llama):
    def __init__(self):
        super().__init__()  # call Llama's __init__ method
        self.tvl = None
        self.raw_tvl = None
        self.curated_tvl = None

    def fetch_tvl(self, chains):
        if self.raw_tvl is None:
            self.raw_tvl = self.getChainTVL(chains)
            self._reclassify_tvl()
        return self.raw_tvl

    def _reclassify_tvl(self):
        self.raw_tvl.loc[self.raw_tvl['protocol'] == 'eos-rex', 'category'] = 'Liquid Staking'
        self.raw_tvl.loc[self.raw_tvl['protocol'] == 'atomichub', 'category'] = 'NFT Marketplace'

    def curate_tvl(self, chains):
        curated_chains = ['ethereum','tron','binance','arbitrum','polygon','optimism','avalanche','fantom','solana','cardano','eos','tezos','aptos','near','stacks','sui','hedera','aurora','eos evm','wax','europa']
        for chain in chains:
            if chain not in curated_chains:
                return f"Error: {chain} is not in the curated list of chains." 
        if self.raw_tvl is None:
            self.fetch_tvl(chains)

        self._filter_tvl()
        return self.curated_tvl

    def _filter_tvl(self):
        df = self.raw_tvl[(self.raw_tvl['type'] == 'tvl') | (self.raw_tvl['type'] == 'borrowed')]
        exclude_categories = ['CEX', 'Chain', 'Yield', 'Bridge', 'Liquid Staking', 'Liquidity manager', 'RWA', 'Gaming', 'NFT Marketplace', 'Leveraged Farming', 'Prediction Market']
        df = df[~df['category'].isin(exclude_categories)]
        exclude_protocols = ['ribbon','frax','unslashed','sturdy','alongside','illuminate','instadapp','defisaver','pooltogether','cian','ubiquity-dao','sandclock','templedao','unbound','axia-protocol','tornado-cash','aztec','tronnrg','garble.money','sperax-demeter','volta-finance','uniwswap-unia-farms','mm-stableswap-polygon','zkbob','brokkr-finance','defrost','sherpa-cash','sturdy','shadecash','zeta']
        df = df[~df['protocol'].isin(exclude_protocols)]
        self.curated_tvl = df
        return df
    
    def _prepare_tvl(self, chains, curated):
        if curated:
            self.tvl = self.curate_tvl(chains)
        else:
            self.tvl = self.fetch_tvl(chains)

    def _get_pivot_table(self, values, index, columns, aggfunc, tvl=None):
        if tvl is None:
            tvl = self.tvl
        return pd.pivot_table(tvl, values=values, index=index, columns=columns, aggfunc=aggfunc)

    def chain_tvl(self, chains, curated=False):
        self._prepare_tvl(chains, curated)
        return self._get_pivot_table('tvl', 'date', 'chain', sum)

    def chain_protocols_tvl(self, chains, curated=False):
        self._prepare_tvl(chains, curated)
        tvl_protocols = {}
        for chain in chains:
            tvl_protocols_chain = self.tvl[self.tvl['chain'] == chain]
            tvl_protocols[f'tvl_protocols_{chain}'] = pd.pivot_table(tvl_protocols_chain, values='tvl', index='date', columns='protocol', aggfunc=sum)

        return tvl_protocols

    def chain_tvb(self, chains, curated=False):
        self._prepare_tvl(chains, curated)
        df_borrows = self.tvl[self.tvl['type'] == 'borrowed']
        return self._get_pivot_table('tvl', 'date', 'chain', sum, df_borrows)

    def chain_protocols_tvb(self, chains, curated=False):
        self._prepare_tvl(chains, curated)
        tvb_protocols = {}
        for chain in chains:
            tvb_protocols_chain = self.tvl.loc[(self.tvl['type'] == 'borrowed') & (self.tvl['chain'] == chain)]
            tvb_protocols[f'tvb_protocols_{chain}'] = pd.pivot_table(tvb_protocols_chain, values='tvl', index='date', columns='protocol', aggfunc=sum)
        return tvb_protocols

    def chain_liquid_staking(self, chains):
        self._prepare_tvl(chains, False) 
        df_liquid_staking = self.tvl[self.tvl['category'] == 'Liquid Staking']
        return self._get_pivot_table('tvl', 'date', 'chain', sum, df_liquid_staking)
    
    def chain_protocols_liquid_staking(self, chains):
        self._prepare_tvl(chains, False)
        df_liquid_staking = self.tvl[self.tvl['category'] == 'Liquid Staking']
        ls_protocols = {}
        for chain in chains:
            ls_chain = df_liquid_staking[df_liquid_staking['chain'] == chain]
            ls_protocols[f'ls_protocols_{chain}'] = pd.pivot_table(ls_chain, values='tvl', index='date', columns='protocol', aggfunc=sum)
        return ls_protocols
    
    def defi_diversity(self, chains, curated=False, threshold=0.9):
        tvl_protocols = self.chain_protocols_tvl(chains, curated)
        defi_diversity_chains = pd.DataFrame()
        for chain in chains:
            df = tvl_protocols[f'tvl_protocols_{chain}']
            df = df.fillna(0)
            df['total'] = df.sum(axis=1)
            diversity = []
            for index, row in df.iterrows():
                row_values = row.values[:-1]
                sorted_row = sorted(row_values, reverse=True)
                cumsum = pd.Series(sorted_row).cumsum()
                div_index = (cumsum <= threshold * row['total']).sum()
                diversity_value = div_index + 1
                diversity.append(diversity_value)

            defi_diversity_protocol = pd.DataFrame({f'defi_diversity_{chain.lower()}': diversity}, index=df.index)

            if defi_diversity_chains.empty:
                defi_diversity_chains = defi_diversity_protocol
            else:
                defi_diversity_chains = pd.merge(defi_diversity_chains, defi_diversity_protocol, how='outer', on='date')

        defi_diversity_chains.sort_index(ascending=True, inplace=True)

        return defi_diversity_chains

    
    def chain_dex_volume(self, chain):
        df = self.getFundamentalsByChains(chain, ['volume']) 
        df = df[df['type'] == 'volume']
        df_total = pd.pivot_table(df, values='value', index='date', columns='chain', aggfunc=sum)
        df_total.index.name = 'DATE'
        df_protocol = pd.pivot_table(df, values='value', index='date', columns='protocol', aggfunc=sum)
        df_protocol.index.name = 'DATE'
        return df_total, df_protocol

    def llama_unique_chain(self):
        return self.llama.getProtocols().chain.unique()