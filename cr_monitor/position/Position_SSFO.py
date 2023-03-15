import ccxt, requests, sys, os, influxdb
import pandas as pd
from cr_assis.connect.connectData import ConnectData

class PositionSSFO(object):
    """Define the position information of SSFO"""
    
    def __init__(self, amount_master={}, amount_slave={}, price_slave={}) -> None:
        self.master = "spot"
        self.slave = "usdt_swap"
        self.markets = ccxt.okex().load_markets()
        self.database = ConnectData()
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
    
    def get_origin_slave(self, client: str, username: str, start: str, end: str) -> dict:
        sql = f"""
        select ex_field, time, exchange, long, long_open_price, settlement, last(short) as short, short_open_price, pair from position
        where client = '{client}' and username = '{username}' and time > {start} and time < {end} and (long >0 or short >0)
        and ex_field = 'swap'
        group by time(1m), pair ORDER BY time
        """
        ret = self.database._send_influx_query(sql = sql, database = "account_data", is_dataFrame= False)
        result = {}
        for info in ret.keys():
            result[info[1]['pair']] = pd.DataFrame(ret[info])
        self.origin_slave = result
        return result
    
    def load_spot_price(self):
        self.database.load_redis()
        self.redis_clt = self.database.redis_clt
    
    def get_spot_price(self, coin: str) -> float:
        self.load_spot_price() if not hasattr(self, "redis_clt") else None
        key = bytes(f"okexv5/{coin}-usdt", encoding="utf8")
        price = float(self.redis_clt.hgetall(key)[b'bid0_price'])
        return price
    
    def get_slave_mv(self):
        for pair, data in self.origin_slave.items():
            coin = pair.split('-')[0]
            price = self.get_spot_price(coin)
            data["mv"] = (data['short'] + data['long']) * price
    