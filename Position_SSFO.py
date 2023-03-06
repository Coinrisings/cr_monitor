import ccxt, requests
import pandas as pd

class PositionSSFO(object):
    """Define the position information of SSFO"""
    
    def __init__(self, amount_master: dict, amount_slave: dict, price_slave: dict) -> None:
        self.master = "spot"
        self.slave = "usdt_swap"
        self.markets = ccxt.okex().load_markets()
        self.amount_master = amount_master # the amount of spot assets. A positive number means long while negative number means short.
        self.amount_slave = amount_slave # the amount of contracts
        self.price_slave = price_slave # the average price of slave in holding position
        self.coins = list(self.amount_master.keys())
        self.ccy = "BTC" # the principal
        self.api_url = 'https://www.okex.com/api/v5/public/position-tiers'
    
    def get_contractsize_slave(self):
        contract_slave = {}
        for coin in self.coins:
            contract_slave[coin] = self.markets[f"{coin}/USDT:USDT"]["contractSize"]
        self.contract_slave = contract_slave
    
    def get_tier(self, instType, tdMode, instFamily=None, instId=None, tier=None, ccy = None):
        params = {k:v  for k, v in locals().items() if k != 'self' and v is not None}
        url = self.parse_params_to_str(params)
        ret = requests.get(self.api_url+url)
        return ret.json()
    
    def parse_params_to_str(self, params):
        url = '?'
        for key, value in params.items():
            url = url + str(key) + '=' + str(value) + '&'
        return url[0:-1]
    
    def handle_origin_tier(self, data: list) -> pd.DataFrame:
        """"data" is the origin data return from okex api"""
        tiers = pd.DataFrame(columns = ["minSz", "maxSz", "mmr", "imr", "maxLever"])
        for i in range(len(data)):
            for col in tiers.columns:
                tiers.loc[i, col] = eval(data[i][col])
        return tiers
    
    def get_tier_slave(self):
        tier_slave = {}
        for coin in self.coins:
            name = f"{coin}-USDT"
            data = self.get_tier(instType = "SWAP", 
                    tdMode = "cross",
                    instFamily= name,
                    instId= name,
                    tier="")["data"]
            tier = self.handle_origin_tier(data)
            tier_slave[coin] = tier.copy()
        self.tier_slave = tier_slave