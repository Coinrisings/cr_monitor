from cr_assis.connect.connectData import ConnectData
from cr_assis.connect.connectOkex import ConnectOkex
import pandas as pd
import numpy as np
import datetime

class PositionOkex(object):
    
    def __init__(self) -> None:
        self.database = ConnectData()
        self.data_okex = ConnectOkex()
        self.fee_rate = 0.001
        self.equity:dict[str, float] = {"BTC": 50} # the asset
        self.contracts = ["usdt", "usdt-swap", "usdt-future", "usd-swap", "usd-future", "usdc-swap"]
        self.now_position = pd.DataFrame(columns = self.contracts)
        self.open_price = pd.DataFrame(columns = self.contracts)
        self.now_price = pd.DataFrame(columns = self.contracts)
        self.mmr_contract = pd.DataFrame(columns = self.contracts)
        self.mmr_liability: dict[str, float] = {}
        self.mm_liability: dict[str, float] = {}
        self.position_value = pd.DataFrame(columns = self.contracts)
        self.mm_contract = pd.DataFrame(columns = self.contracts)
        self.disacount_equity: dict[str, float] = {}
        self.upnl: dict[str, float] = {}
        self.mmr_upnl :dict[str, float] = {}
        self.mm_upnl :dict[str, float] = {}
        self.coin_price: dict[str, float] = {"USDT":1, "USD": 1, "USDC": 1, "USDK": 1, "BUSD": 1}
        self.adjEq: float
        self.mm: float
        self.mr: float
    
    def update_equity(self):
        self.equity["USDT"] = 0 if "USDT" not in self.equity.keys() else self.equity["USDT"]
        for coin in self.now_position[self.now_position["usdt"] != 0].index:
            self.equity[coin] = self.equity[coin] + self.now_position.loc[coin, "usdt"] if coin in self.equity.keys() else self.now_position.loc[coin, "usdt"]
            open_price = self.open_price.loc[coin, "usdt"] if coin in self.open_price.index else np.nan
            self.equity["USDT"] -= self.now_position.loc[coin, "usdt"] * open_price
        self.get_upnl()
        
    def get_discount_asset(self, coin: str, asset: float) ->float:
        """
        Args:
            coin (str): coin name, str.upper()
            asset (float): the dollar value of coin
        """
        discount_info = self.data_okex.get_discount_info(coin) if coin.upper() not in self.data_okex.discount_info.keys() else self.data_okex.discount_info[coin.upper()]
        if discount_info == []:
            real_asset = np.nan
        else:
            real_asset = 0.0
        for info in discount_info:
            minAmt = float(info["minAmt"]) if info["minAmt"] != "" else 0
            maxAmt = float(info["maxAmt"]) if info["maxAmt"] != "" else np.inf
            discountRate = float(info["discountRate"])
            if asset > minAmt and asset <= maxAmt:
                real_asset += (asset - minAmt) * discountRate
            elif asset > maxAmt:
                real_asset += (maxAmt - minAmt) * discountRate
            else:
                break
        return real_asset
    
    def get_coin_price(self, coin: str) -> float:
        coin = coin.upper()
        if coin in self.coin_price.keys():
            price = self.coin_price[coin]
        else:
            price = self.database.get_redis_okex_price(coin, "usdt")
            self.coin_price[coin] = price
        return price
    
    def check_position_price(self):
        for coin in self.now_position.index:
            if coin not in self.open_price.index:
                self.open_price.loc[coin, self.contracts] = self.get_coin_price(coin)
            elif self.open_price.loc[coin].isnull().sum() > 0:
                self.open_price.loc[coin].fillna(self.get_coin_price(coin), inplace = True)
            if coin not in self.now_price.index:
                self.now_price.loc[coin, self.contracts] = self.get_coin_price(coin)
            elif self.now_price.loc[coin].isnull().sum() > 0:
                self.now_price.loc[coin].fillna(self.get_coin_price(coin), inplace = True)
                
    def get_disacount_equity(self):
        self.disacount_equity = {}
        for coin in self.equity.keys():
            if coin not in ["USDC", "USD", "USDT", "USDK", "BUSD", "DAI"]:
                self.disacount_equity[coin]= self.get_discount_asset(coin = coin, asset = self.equity[coin] * self.now_price.loc[coin, "usdt"]) if self.equity[coin] >0 else self.equity[coin] * self.now_price.loc[coin, "usdt"]
            else:
                self.disacount_equity[coin] = self.equity[coin]
        self.adjEq = sum(self.disacount_equity.values())
    
    def get_upnl(self):
        for coin in self.now_position.index:
            for contract in self.now_position.columns.drop("usdt"):
                if self.now_position.loc[coin, contract] != 0 and self.open_price.loc[coin, contract] > 0:
                    if contract.split("-")[0] == "usd":
                        upnl = self.now_position.loc[coin, contract] * self.data_okex.get_contractsize_cswap(coin) * (1/self.open_price.loc[coin, contract] - 1/ self.now_price.loc[coin, contract])
                        self.equity[coin] = upnl if coin not in self.equity.keys() else self.equity[coin] + upnl
                    else:
                        upnl = self.now_position.loc[coin, contract] * (self.now_price.loc[coin, contract] - self.open_price.loc[coin, contract])
                        stable_coin = contract.split("-")[0].upper()
                        self.equity[stable_coin] = upnl if stable_coin not in self.equity.keys() else self.equity[stable_coin] + upnl
    
    def get_adjEq(self):
        self.check_position_price()
        self.update_equity()
        self.get_disacount_equity()
    
    def get_mmr_contract(self):
        self.mmr_liability = pd.DataFrame(index = self.now_position.index, columns = self.now_position.columns)
        for coin in self.now_position.index:
            for contract in self.now_position.columns.drop("usdt"):
                self.mmr_contract.loc[coin, contract] = self.data_okex.get_mmr(coin, self.now_position.loc[coin, contract], contract)
    
    def get_position_value(self):
        self.position_value = pd.DataFrame(index = self.now_position.index, columns = self.now_position.columns)
        for coin in self.now_position.index:
            for contract in self.now_position.columns:
                self.position_value.loc[coin, contract] = abs(self.now_position.loc[coin, contract]) * self.now_price.loc[coin, contract] if contract.split("-")[0] != "usd" else\
                    abs(self.now_position.loc[coin, contract]) * self.data_okex.get_contractsize_cswap(coin)
    
    def get_mm_liability(self):
        self.mm_liability, self.mmr_liability = {}, {}
        for coin, amount in self.equity.items():
            self.mmr_liability[coin] = self.data_okex.get_mmr(coin, amount, contract = "spot")
            self.mm_liability[coin] = self.mmr_liability[coin] * abs(amount) * self.get_coin_price(coin)
    
    def get_mm(self):
        self.get_mmr_contract()
        self.get_position_value()
        self.mm_contract = (self.mmr_contract * self.position_value).fillna(0)
        self.get_mm_liability()
        self.mm = self.mm_contract.values.sum() + sum(self.mm_liability.values()) + self.fee_rate * self.position_value.fillna(0).values.sum()
    
    def cal_mr(self) -> float:
        self.get_adjEq()
        self.get_mm()
        self.mr = self.adjEq / self.mm
        return self.mr