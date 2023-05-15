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
    
    def run_price_influence(self, now_price: pd.DataFrame) -> dict[float, float]:
        price_influence = {}
        for change in self.price_range:
            self.position.now_price = now_price * change
            price_influence[change] = self.position.cal_mr()
        return price_influence
    
    def run_account_mr(self, account: AccountOkex) -> pd.DataFrame:
        account.get_now_position() if not hasattr(account, "now_position") else None
        account.get_open_price() if not hasattr(account, "open_price") or len(account.open_price) < len(account.now_position) else None
        account.get_now_price() if not hasattr(account, "now_price") or len(account.now_price) < len(account.now_position) else None
        account.get_cashBal(account.ccy)
        self.position.now_position = account.now_position[self.position.contracts]
        for coin in account.usd_position.index:
            for col in account.usd_position.columns:
                self.position.now_position.loc[coin, col] = account.usd_position.loc[coin, col]
        self.position.open_price = account.open_price
        self.position.equity = copy.deepcopy(account.cashBal)
        ret = self.run_price_influence(now_price=account.now_price)
        self.account_mr = copy.deepcopy(ret)
        return ret