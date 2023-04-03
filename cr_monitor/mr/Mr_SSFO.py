from cr_monitor.position.Position_SSFO import PositionSSFO
import copy
import numpy as np
import pandas as pd

class MrSSFO(object):
    """SSFO means spot and usdt_swap in okex."""
    
    def __init__(self, position: PositionSSFO):
        self.position = position
        self.ccy = "BTC"
        self.assumed_coins = {"BLUR", "AR", "GFT", "FIL", "ARB", "PEOPLE", "ETH", "SUSHI", "ICP", "THETA"}
    
    def run_price_influence(self) -> dict[float, float]:
        result: dict[float, float] = {}
        adjEq0 = copy.deepcopy(self.position.start_adjEq)
        now_price_master = copy.deepcopy(self.position.now_price_master)
        now_price_slave = copy.deepcopy(self.position.now_price_slave)
        for change in np.arange(0.3, 2, 0.1):
            change = round(change, 2)
            self.position.start_adjEq = adjEq0 * change
            self.position.adjEq = adjEq0 * change
            for coin in now_price_master.keys():
                self.position.now_price_master[coin] = now_price_master[coin] * change
            for coin in now_price_slave.keys():
                self.position.now_price_slave[coin] = now_price_slave[coin] * change
            result[change] = self.position.cal_mr()
        return result

    def run_assumed_open(self):
        self.position.amount_master = {coin: 0 for coin in self.assumed_coins}
        ccy_price = self.position.get_master_price(coin = self.ccy)
        now_price = self.position.get_now_price_master()
        self.position.price_master = now_price
        self.position.price_slave = copy.deepcopy(self.position.price_master)
        coins_number = len(self.assumed_coins)
        assumed_open:dict[float, dict[float, dict[float, float]]] = {}
        for num in range(30, 100, 10):
            ret = {}
            for mul in np.arange(0.5, 1.6, 0.1):
                mul = round(mul, 2)
                single_mv = mul / coins_number * num * ccy_price
                assumed_holding = {coin: single_mv / now_price[coin] for coin in self.assumed_coins}
                self.position.equity = {self.ccy: num}
                self.position.adjEq = num * ccy_price
                self.position.start_adjEq = num * ccy_price
                self.position.liability = num * ccy_price * mul
                self.position.amount_master = copy.deepcopy(assumed_holding)
                self.position.amount_slave = {coin : - amount for coin, amount in assumed_holding.items()}
                self.position.now_price_master = copy.deepcopy(self.position.price_master)
                self.position.now_price_slave = copy.deepcopy(self.position.price_slave)
                result = self.run_price_influence()
                ret[mul] = copy.deepcopy(result)
            assumed_open[num] = copy.deepcopy(ret)
        self.assumed_open = assumed_open
        return assumed_open
    
    def run_account_mr(self, client: str, username: str) -> dict[float, float]:
        self.position.client = client
        self.position.username = username
        self.position.cal_mr()
        ret = self.run_price_influence()
        self.account_mr = ret
        return ret