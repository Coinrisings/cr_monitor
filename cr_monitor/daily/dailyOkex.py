from cr_monitor.mr.mrOkex import MrOkex
from cr_monitor.position.positionOkex import PositionOkex
from cr_monitor.daily.daily_monitor import set_color, set_funding_color, set_mv_color
from cr_assis.account.initAccounts import InitAccounts
from cr_assis.account.accountOkex import AccountOkex
from cr_assis.connect.connectData import ConnectData
import pandas as pd
from pandas.io.formats.style import Styler

class DailyOkex(object):
    
    def __init__(self):
        self.ignore_test = True
        self.database = ConnectData()
        self.mr_okex = MrOkex()
        self.position_okex = PositionOkex()
        self.accounts: dict[str, AccountOkex]
        self.all_position: pd.DataFrame = pd.DataFrame()
        self.position_change: pd.DataFrame = pd.DataFrame()
        self.mv_color = {
            "okx_usd_swap-okx_usdc_swap" : "red",
            "okx_usd_swap-okx_usdt_swap" : "orange",
            "okx_spot-okx_usdt_swap": "springgreen",
            "okx_usd_swap-okx_spot": "royalblue",
            "okx_spot-okx_usdt_future": "violet",
            "okx_usd_future-okx_spot": "grey",
            "okx_usdc_swap-okx_usdt_swap" : "pink",
        }
        self.init_accounts()
    
    def init_accounts(self) -> None:
        """init okex accounts"""
        self.init = InitAccounts(ignore_test= self.ignore_test)
        self.accounts = self.init.init_accounts_okex()
    
    def get_all_position(self, is_color = True) -> pd.DataFrame | Styler:
        self.color = pd.DataFrame()
        for name, account in self.accounts.items():
            position = account.get_account_position()
            for i in position.index:
                coin = position.loc[i, "coin"].upper()
                self.all_position.loc[coin, name] = position.loc[i, "MV%"] / 100
                self.color.loc[coin, name] = "background-color: " + self.mv_color[position.loc[i, "combo"]] if position.loc[i, "combo"] in self.mv_color.keys() else "white"
        self.all_position = self.all_position.fillna(0).sort_index(axis=0).sort_index(axis = 1)
        self.color.fillna("background-color: black", inplace = True)
        format_dict = {col: '{0:.4%}' for col in self.all_position.columns}
        ret = self.all_position.copy() if not is_color else self.all_position.style.apply(set_mv_color, axis=None, color = self.color).format(format_dict)
        return ret
    
    def get_position_change(self, start: str, end: str, is_color = False) -> pd.DataFrame | Styler:
        for name, account in self.accounts.items():
            old_position = account.get_account_position(the_time=start).set_index("coin")
            new_position = account.get_account_position(the_time=end).set_index("coin")
            for coin in new_position.index:
                change = new_position.loc[coin, "MV%"] - old_position.loc[coin, "MV%"] if coin in old_position.index and old_position.loc[coin, "combo"] == new_position.loc[coin, "combo"] else \
                    new_position.loc[coin, "MV%"]
                self.position_change.loc[coin.upper(), name] = change / 100
        self.position_change = self.position_change.fillna(0).sort_index(axis=0).sort_index(axis = 1)
        format_dict = {col: '{0:.4%}' for col in self.position_change.columns}
        ret = self.position_change.copy() if not is_color else self.position_change.style.background_gradient(cmap='Blues', subset = list(self.position_change.columns), vmax = 0.15, vmin = -0.15).format(format_dict)
        return ret
    
    def get_account_mr(self, is_color = True) -> pd.DataFrame | Styler:
        self.account_mr: dict[str, dict[str, float]] = {}
        for name, account in self.accounts.items():
            self.account_mr[name] = self.mr_okex.run_account_mr(account = account)
        ret = pd.DataFrame.from_dict(self.account_mr)
        ret = ret.style.applymap(set_color) if is_color else ret
        return ret