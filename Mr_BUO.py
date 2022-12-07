from Mr_DTO import MrDTO
import ccxt, os
from research.utils import readData
import numpy as np
os.environ["MONGO_URI"] = 'mongodb://read_only:Abcd1234@10.1.1.254:3717/?authSource=admin'
os.environ["INFLUX_URI"] = 'program:Coinrising1234@www.tooook.com:28086'
class MrBUO(MrDTO):
    """MrBUO: calucate MarginRatio for BU in okex, which means master is okex-usdc-swap and slave is okex-usdt-swap。
    position and assest coin have to be the same.

    Args:
        MrDTO (_type_): calucate MarginRatio for DT-O.
    """
    
    def __init__(self, amount_u: int, amount_c: int, amount_fund: float, price_u: float, price_c: float, now_price: float, coin="BTC", is_long=True):
        """
        Args:
            amount_u (int): the amount of USDT swap contracts(not coins) in holding position
            amount_c (int): the amount of USDC swap contracts(not coins) in holding position
            amount_fund (float): the amount of asset 
            price_u (float): the average price of USDT swap in holding position
            price_c (float): the average price of USDC swap in holding position
            now_price (float): the price of coin, now
            coin (str, optional): the assest and position currency. Defaults to "BTC".
            is_long (bool, optional): the direction of position. "long" means long usdc_swap and short usdt_swap, while "short" means short usdc_swap and long usdt_swap. Defaults to True.
        """
        self.amount = {"usdt": amount_u, "usdc": amount_c}
        self.api_url = 'https://www.okex.com/api/v5/public/position-tiers'
        self.holding_price = {"usdt": price_u, "usdc": price_c}
        self.now_price = now_price
        self.amount_fund = amount_fund
        self.is_long = is_long
        self.coin = coin.upper()
        self.contract = self.get_contractsize() # the contractSize of coin
        self.coin_u = self.contract["usdt"] * self.amount["usdt"] # the amount of USDT swap coins in holding position
        self.coin_c = self.contract["usdc"] * self.amount["usdc"] # the market value of USD swap in holding position
    
    def get_contractsize(self) -> dict:
        """get contractsize of master and slave pair
        Returns:
            dict: the contractsize of coin, including master and slave, like {"usdt": 1, "usdc": 1}
        """
        exchange = ccxt.okex()
        markets = exchange.load_markets()
        contract = {}
        contract["usdt"] = markets[f"{self.coin}/USDT:USDT"]["contractSize"]
        contract["usdc"] = markets[f"{self.coin}/USD:USDC"]["contractSize"]
        return contract
    
    def get_swap_tier(self) -> dict:
        swap_tier = {}
        for suffix in ["usdt", "usdc"]:
            name = f"{self.coin}-{suffix.upper()}"
            data = self.get_tier(instType = "SWAP", 
                    tdMode = "cross",
                    instFamily= name,
                    instId= name,
                    tier="")["data"]
            tier = self.handle_origin_tier(data)
            swap_tier[suffix] = tier.copy()
        return swap_tier
    
    def get_spot_tier(self) -> dict:
        spot_tier = {}
        for ccy in ["USDC", "USDT"]:
            data = self.get_tier(instType = "MARGIN", 
                tdMode = "cross",
                ccy = ccy)["data"]
            tier = self.handle_origin_tier(data)
            spot_tier[ccy] = tier.copy()
        return spot_tier
    
    def get_mmr_swap(self) -> dict:
        """get swap maintenance margin ratio

        Returns:
            dict: pair to tiers, like {"usdc": pd.DataFrame()}
        """
        mmr_swap = {}
        for contract in ["usdt", "usdc"]:
            tier = self.swap_tier[contract]
            amount = self.amount[contract]
            for i in tier.index:
                if amount >= tier.loc[i, "minSz"] and amount <= tier.loc[i, "maxSz"]:
                    mmr_swap[contract] = tier.loc[i, "mmr"]
                    break
                else:
                    pass
        return mmr_swap
    
    def get_upnl(self, now_price: float) -> dict:
        """now_price: now price of coin, or a assumed price
        """
        upnl = {"USDT": 0, "USDC": 0} #the amount of coin, not dollars
        if self.is_long:
            upnl["USDC"] = (now_price - self.holding_price["usdc"]) * self.coin_c
            upnl["USDT"] = (self.holding_price["usdt"] - now_price) * self.coin_u
        else:
            upnl[self.coin] = (self.holding_price["usdc"] - now_price) * self.coin_c
            upnl["USDT"] = (now_price - self.holding_price["usdt"]) * self.coin_u
        return upnl
    
    def get_maintenance(self, now_price: float, spread = None) -> tuple([dict, dict]):
        """get maintenance margin value, including swap and spot
        Args:
            now_price(float): now price of coin, or a assumed price
        """
        mainten_swap = {"usdt": 0, "usdc": 0}
        mainten_swap["usdc"] = self.coin_c * self.mmr_swap["usdc"] * now_price
        mainten_swap["usdt"] = self.coin_u * now_price * self.mmr_swap["usdt"]
        mainten_spot = {"USDC": 0, "USDT": 0}
        price = {"USDC": 1, "USDT": 1}
        if spread  == None:
            upnl = self.get_upnl(now_price = now_price)
        else:
            upnl = self.get_upnl_spread(spread = spread)
        for ccy in ["USDC", "USDT"]:
            mmr = self.get_mmr_spot(amount = -upnl[ccy], ccy = ccy)
            mainten_spot[ccy] = mmr * abs(upnl[ccy]) * price[ccy]
        return mainten_swap, mainten_spot
    
    def get_mr(self, now_price: float) -> float:
        """calcuate mr

        Args:
            now_price (float):now price of coin, or a assumed price

        Returns:
            float: mr
        """
        fund_value = self.amount_fund * now_price
        mainten_swap, mainten_spot = self.get_maintenance(now_price = now_price)
        total_mainten = sum(mainten_swap.values()) + sum(mainten_spot.values()) + (self.coin_c * self.now_price + self.coin_u * self.now_price) * 0.0008
        mr = fund_value / total_mainten
        return mr
    
coin = "btc"
key = f"okexv5/{coin}-usdt"
key = bytes(key, encoding = "utf8")
r = readData.read_redis()
data = r.hgetall(key)
now_price = eval(data[b'bid0_price'])
amount_fund = 30
mul = 2
amount_u = amount_fund * mul * 100
amount_c = amount_fund * mul * 10000
m = MrBUO(amount_u = amount_u,
            amount_c = amount_c,
            amount_fund = amount_fund,
            price_u =  now_price, 
            price_c =  now_price,
            now_price = now_price)
m.initialize()
print(m.mr)
print(m.amount)
print(m.mmr_swap)
print(1)