from daily_monitor import set_color
from daily_DTFmonitor import DailyMonitorDTF
from MrFso_UC import FsoUC
import copy, sys, os
from pathlib import Path
sys.path.append(os.path.dirname(f"{Path( __file__ ).parent.absolute()}") + "/cr_monitor")
from fsoPnl import FsoPnl
import pandas as pd
import numpy as np

class DailyFsoUC(DailyMonitorDTF):
    def __init__(self, delivery="230331", ignore_test=True):
        self.delivery = delivery
        self.ignore_test = ignore_test
        self.strategy_name = "dt_okex_uswap_okex_cfuture"
        self.init_accounts()
        self.get_pnl_daily = FsoPnl(accounts = list(self.accounts.values()))
    
    def get_btc_parameter(self):
        data = self.get_coin_parameter(coin = "btc", suffix=f"-usdt-swap")
        self.btc_parameter = data.copy()
    
    def get_eth_parameter(self):
        data = self.get_coin_parameter(coin = "eth", suffix=f"-usdt-swap")
        self.eth_parameter = data.copy()
    
    def run_mr(self):
        """推算每个账户的mr情况"""
        self.mgnRatio = {}
        self.picture_value = pd.DataFrame()
        self.picture_spread = pd.DataFrame()
        now_price = list(self.accounts.values())[0].get_coin_price(coin = "btc")
        for name, account in self.accounts.items():
            if not hasattr(account, "now_position"):
                now_position = account.get_now_position()
            else:
                now_position = account.now_position
            if "btc" in now_position.index:
                account.get_equity()
                #初始化账户
                mr_dto = FsoUC(amount_c = now_position.loc["btc", "slave_number"],
                                amount_u = round(now_position.loc["btc", "master_number"] * 100, 0),
                                amount_fund = account.adjEq / now_price,
                                price_u = now_position.loc["btc", "master_open_price"], 
                                price_c = now_position.loc["btc", "slave_open_price"],
                                now_price = now_price, 
                                suffix = self.delivery)
                mr_dto.run_mmr(play = False)
                #保留数据
                self.mgnRatio[name] = copy.deepcopy(mr_dto)
                self.picture_value = pd.concat([mr_dto.value_influence, self.picture_value], axis = 1, join = 'outer')
                self.picture_spread = pd.concat([mr_dto.spread_influence, self.picture_spread], axis = 1, join = 'outer')
                self.picture_value.rename({"mr": name}, inplace = True, axis = 1)
                self.picture_spread.rename({"mr": name}, inplace = True, axis = 1)
        value = copy.deepcopy(self.picture_value)
        spread = copy.deepcopy(self.picture_spread)
        value = value.style.applymap(set_color)
        spread = spread.style.applymap(set_color)
        return value, spread
    
    # def run_daily(self) -> pd.DataFrame:
    #     self.get_pnl_daily.get_pnl()
    #     self.get_now_situation() if not hasattr(self, "now_situation") else None
    #     account_overall = self.now_situation.copy()
    #     for i in account_overall.index:
    #         parameter_name = account_overall.loc[i, "account"]
    #         account = self.accounts[parameter_name]
    #         account_overall.loc[i, "locked_tpnl"] = account.locked_tpnl[account.principal_currency.lower()]
    #         account_overall.loc[i, "locked_tpnl%"] = account.locked_tpnl[account.principal_currency.lower()] / account_overall.loc[i, "capital"]
    #         account_overall.loc[i, "fpnl"] = account.third_pnl[account.principal_currency]
    #         account_overall.loc[i, "fpnl%"] = account.third_pnl[account.principal_currency] / account_overall.loc[i, "capital"]
    #     account_overall["tpnl_avg%"] = np.mean(account_overall["locked_tpnl%"])
    #     account_overall["fpnl_avg%"] = np.mean(account_overall["fpnl%"])
    #     self.account_overall = account_overall.copy()
    #     format_dict = {'capital': lambda x: format(round(x, 4), ","), 
    #                     'locked_tpnl': '{0:.4f}', 
    #                     'locked_tpnl%': '{0:.4%}', 
    #                     'fpnl': '{0:.4f}', 
    #                     'fpnl%': '{0:.4%}', 
    #                     'tpnl_avg%': '{0:.4f}', 
    #                     'fpnl_avg%': '{0:.4%}', 
    #                     'MV%': '{0:.2f}', 
    #                     'mr': lambda x: format(round(x, 2), ","),
    #                     'week_profit': '{0:.4%}'
    #                     }
    #     account_overall = account_overall.style.format(format_dict).background_gradient(cmap='Blues', subset = 
    #                     ['locked_tpnl', 'locked_tpnl%', "fpnl", "fpnl%", 'tpnl_avg%','fpnl_avg%', "MV%", "mr", 'week_profit'])
    #     return account_overall