import ccxt, requests, copy
import pandas as pd
import numpy as np
from cr_assis.connect.connectData import ConnectData

class PositionSSFO(object):
    """Define the position information of SSFO"""
    
    def __init__(self, amount_master={}, amount_slave={}, price_master={},price_slave={}, equity={"USDT": 10000}, client = "", username = "") -> None:
        self.master = "spot"
        self.slave = "usdt_swap"
        self.markets = ccxt.okex().load_markets()
        self.database = ConnectData()
        self.amount_master = amount_master # the amount of spot assets. A positive number means long while negative number means short.
        self.amount_slave = amount_slave # the amount of contracts
        self.price_master = self.get_now_price() if price_master == {} else price_master # now price or assumed price of master asset
        self.price_slave = self.get_now_price_slave() if price_slave == {} else price_slave # the average price of slave in holding position
        self.username = username
        self.client = client
        self.equity = equity # the asset
        self.tiers_url = 'https://www.okex.com/api/v5/public/position-tiers'
        self.discount_url = "https://www.okex.com/api/v5/public/discount-rate-interest-free-quota"
        self.discount_info = {}
        self.tier_slave = {}
        self.tier_master = {}
        self.contract_slave = {}
        self.get_start_adjEq()
        self.get_upnl()
    
    def get_contractsize_slave(self, coin: str) -> float:
        coin = coin.upper()
        contractsize = self.markets[f"{coin}/USDT:USDT"]["contractSize"]
        self.contract_slave[coin] = contractsize
        return contractsize
    
    def get_discount_info(self, coin:str) -> list:
        """get discount information of special coin through api

        Args:
            coin (str): str.upper()

        Returns:
            list: list of dict
        """
        response = requests.get(self.discount_url + f"?ccy={coin.upper()}")
        if response.status_code == 200:
            ret = response.json()['data'][0]['discountInfo']
        else:
            ret = []
        self.discount_info[coin.upper()] = ret.copy()
        return ret
    
    def get_discount_asset(self, coin: str, asset: float) ->float:
        """
        Args:
            coin (str): coin name, str.upper()
            asset (float): the dollar value of coin
        """
        discount_info = self.get_discount_info(coin) if coin.upper() not in self.discount_info.keys() else self.discount_info[coin.upper()]
        real_asset = 0.0
        for info in discount_info:
            minAmt = float(info["minAmt"]) if info["minAmt"] != "" else 0
            maxAmt = float(info["maxAmt"]) if info["maxAmt"] != "" else np.inf
            discountRate = float(info["discountRate"])
            if asset > minAmt and asset <= maxAmt:
                real_asset += (asset - minAmt) * discountRate
            elif asset > maxAmt:
                real_asset += maxAmt * discountRate
            else:
                break
        return real_asset
    
    def get_tier(self, instType, tdMode, instFamily=None, instId=None, tier=None, ccy = None):
        params = {k:v  for k, v in locals().items() if k != 'self' and v is not None}
        url = self.parse_params_to_str(params)
        ret = requests.get(self.tiers_url+url)
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
    
    def get_tier_slave(self, coin: str) -> pd.DataFrame:
        name = f"{coin.upper()}-USDT"
        data = self.get_tier(instType = "SWAP", 
                tdMode = "cross",
                instFamily= name,
                instId= name,
                tier="")["data"]
        tier = self.handle_origin_tier(data)
        self.tier_slave[coin.upper()] = tier
        return tier
    
    def get_tier_master(self, coin: str) -> pd.DataFrame:
        ret = self.get_tier(instType = "MARGIN", 
            tdMode = "cross",
            ccy = coin.upper())
        tier = self.handle_origin_tier(ret["data"])
        self.tier_master[coin.upper()] = tier
        return tier
    
    def find_mmr(self, amount: float, tier: pd.DataFrame) -> float:
        """
        Args:
            amount (float): the amount of spot asset or swap contract
            tier (pd.DataFrame): the position tier information
        """
        mmr = np.nan
        for i in tier.index:
            if amount > tier.loc[i, "minSz"] and amount <= tier.loc[i, "maxSz"]:
                mmr = tier.loc[i, "mmr"]
                break
        return mmr
    
    def get_mmr_master(self, coin: str, amount: float) -> float:
        """get mmr of master, which is spot

        Args:
            coin (str): the name of coin, str.upper()
            amount (float): the number of spot asset, not dollar value
        """
        coin = coin.upper()
        tier = self.tier_master[coin] if coin in self.tier_master.keys() else self.get_tier_master(coin)
        mmr = self.find_mmr(amount = amount, tier = tier)
        return mmr
    
    def get_mmr_slave(self, coin: str, amount: float) -> float:
        """get mmr of slave, which is usdt_swap

        Args:
            coin (str): the name of coin, str.upper()
            amount (float): the coin number of usdt_swap asset, not dollar value, not contract number
        """
        coin = coin.upper()
        tier = self.tier_slave[coin] if coin in self.tier_slave.keys() else self.get_tier_slave(coin)
        contractsize = self.get_contractsize_slave(coin) if not coin in self.contract_slave.keys() else self.contract_slave[coin]
        num = amount / contractsize
        mmr = self.find_mmr(amount = num, tier = tier)
        return mmr
    
    def get_start_adjEq(self):
        ccy = list(self.equity.keys())[0].upper()
        price = 1 if ccy in ["USDT", "USDC", "BUSD", "USDC", "USDK", "DAI"] else self.get_spot_price(ccy)
        start_adjEq = price * self.equity[ccy]
        liability = 0
        coins = set(self.amount_slave.keys()) & set(self.price_slave.keys())
        for coin in coins:
            liability += self.amount_slave[coin] * self.price_slave[coin]
        self.start_adjEq = start_adjEq
        self.liability = liability
        
    def get_upnl(self) -> dict:
        upnl = {}
        self.get_now_price_slave() if not hasattr(self, "now_price_slave") else None
        for coin in set(self.amount_slave.keys()) & set(self.price_slave.keys()):
            upnl[coin] = max(0, self.now_price_slave[coin] - self.price_slave[coin]) * self.amount_slave[coin]
        self.upnl = upnl
        return upnl
    
    def get_disacount_adjEq(self) -> float:
        coins = set(self.amount_master.keys()) & set(self.amount_slave.keys() & set(self.price_slave.keys()) & set(self.price_master.keys()))
        adjEq = 0
        for coin in coins:
            adjEq += self.get_discount_asset(coin = coin, asset = self.amount_master[coin] * self.price_master[coin])
        adjEq += (self.start_adjEq - self.liability)
        return adjEq
    
    def get_now_price(self) -> dict:
        now_price = {}
        for coin in set(self.amount_master.keys()):
            now_price[coin] = self.get_spot_price(coin)
        return now_price

    def get_mmr(self) -> tuple[dict[str, float], dict[str, float]]:
        mmr_master = {"USDT": self.get_mmr_master(coin = "USDT", amount = self.liability + sum(self.upnl.values()))}
        mmr_slave = {}
        for coin, amount in self.amount_slave.items():
            mmr_slave[coin] = self.get_mmr_slave(coin = coin, amount = amount)
        self.mmr_master, self.mmr_slave = mmr_master, mmr_slave
        return mmr_master, mmr_slave
    
    def get_now_price_slave(self) -> dict[str, float]:
        now_price_slave = {}
        for coin in set(self.amount_slave.keys()):
            now_price_slave[coin] = self.get_slave_price(coin)
        self.now_price_slave = now_price_slave
        return now_price_slave

    def cal_mm(self) -> tuple[dict[str, float], dict[str, float]]:
        mmr_master, mmr_slave = self.get_mmr()
        mm_master = {"USDT": self.liability * mmr_master["USDT"]}
        mm_slave = {}
        for coin, mmr in mmr_slave.items():
            mm_slave[coin] = mmr * self.amount_slave[coin] * self.now_price_slave[coin]
        self.mm_master, self.mm_slave = mm_master, mm_slave
        return mm_master, mm_slave
        
    def cal_mr(self) -> float:
        adjEq = self.get_disacount_adjEq()
        mm_master, mm_slave = self.cal_mm()
        mr = adjEq / (sum(mm_master.values()) + sum(mm_slave.values()))
        self.mr = mr
        return mr
    
    def get_origin_slave(self, start: str, end: str) -> dict:
        sql = f"""
        select ex_field, time, exchange, long, long_open_price, settlement, last(short) as short, short_open_price, pair from position
        where client = '{self.client}' and username = '{self.username}' and time > {start} and time < {end} and (long >0 or short >0)
        and ex_field = 'swap'
        group by time(1m), pair ORDER BY time
        """
        ret = self.database._send_influx_query(sql = sql, database = "account_data", is_dataFrame= False)
        result = {}
        for info in ret.keys():
            result[info[1]['pair']] = pd.DataFrame(ret[info])
        self.origin_slave = result
        return result
    
    def load_redis_price(self):
        self.database.load_redis()
        self.redis_clt = self.database.redis_clt
    
    def get_redis_price(self, coin: str, suffix: str) -> float:
        self.load_redis_price() if not hasattr(self, "redis_clt") else None
        key = bytes(f"okexv5/{coin.lower()}-{suffix}", encoding="utf8")
        price = float(self.redis_clt.hgetall(key)[b'bid0_price'])
        return price
    
    def get_spot_price(self, coin: str) -> float:
        price = self.get_redis_price(coin = coin, suffix = "usdt")
        return price

    def get_slave_price(self, coin: str) -> float:
        price = self.get_redis_price(coin = coin, suffix = "usdt-swap")
        return price
    
    def get_slave_mv(self):
        for pair, data in self.origin_slave.items():
            coin = pair.split('-')[0]
            price = self.get_spot_price(coin)
            data["mv"] = (data['short'] + data['long']) * price
    
    def get_now_position(self):
        ret = self.get_origin_slave(start = "now() - 5m", end = "now()")
        for pair, data in ret.items():
            coin = pair.split("-")[0].upper()
            data = data.dropna(subset = ["short"])
            amount = data["short"].values[-1]
            price = data["short_open_price"].values[-1]
            self.amount_slave[coin] = amount
            self.price_slave[coin] = price
        self.amount_master = copy.deepcopy(self.amount_slave)
        self.price_master = self.get_now_price()