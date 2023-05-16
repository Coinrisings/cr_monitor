from cr_monitor.position.positionOkex import PositionOkex
from cr_assis.account.accountOkex import AccountOkex
from cr_assis.connect.connectData import ConnectData
import pandas as pd
import numpy as np
import copy

class MrOkex(object):
    
    def __init__(self) -> None:
        self.position = PositionOkex()
        self.price_range = np.arange(0.3, 3, 0.1)
    
    def run_price_influence(self, now_price: pd.DataFrame, equity: dict[str, float]) -> dict[float, float]:
        price_influence = {}
        for change in self.price_range:
            change = round(change, 2)
            self.position.now_price = now_price * change
            self.position.equity = copy.deepcopy(equity)
            price_influence[change] = self.position.cal_mr()
        return price_influence
    
    def change_position(self, account: AccountOkex, contract: str, coin: str,mv: float):
        account.get_equity()
        if contract.split("-")[0] != "usd":
            amount = account.adjEq * mv / self.position.get_coin_price(coin)
            if coin.upper() in account.now_position.index:
                account.now_position.loc[coin.upper(), contract] += amount
            else:
                account.now_position.loc[coin.upper(), contract] = amount
        else:
            amount = account.adjEq * mv / self.position.data_okex.get_contractsize_cswap(coin)
            if coin.upper() in account.usd_position.index and contract in account.usd_position.columns:
                account.usd_position.loc[coin.upper(), contract] += amount
            else:
                account.usd_position.loc[coin.upper(), contract] = amount
    
    def add_account_position(self, account: AccountOkex, combo: str, add_coin: dict[str, float]):
        master, slave = combo.split("-")
        master = master.replace("okx_", "").replace("spot", "usdt").replace("_", "-")
        slave = slave.replace("okx_", "").replace("spot", "usdt").replace("_", "-")
        for coin, mv in add_coin.items():
            self.change_position(account, master, coin, mv)
            self.change_position(account, slave, coin, -mv)
        account.now_position.fillna(0, inplace= True)
    
    def run_account_mr(self, account: AccountOkex, add: dict[str, dict[str, float]] = {}) -> pd.DataFrame:
        account.get_now_position() if not hasattr(account, "now_position") else None
        account.get_open_price() if not hasattr(account, "open_price") or len(account.open_price) < len(account.now_position) else None
        account.get_now_price() if not hasattr(account, "now_price") or len(account.now_price) < len(account.now_position) else None
        account.get_cashBal(account.ccy)
        for combo in add.keys():
            self.add_account_position(account, combo, add[combo])
        self.position.now_position = account.now_position[self.position.contracts].copy()
        self.position.now_position.loc[account.usd_position.index, account.usd_position.columns] = account.usd_position
        self.position.open_price = account.open_price
        ret = self.run_price_influence(now_price=account.now_price.copy(), equity=account.cashBal)
        self.account_mr = copy.deepcopy(ret)
        return ret