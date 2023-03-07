from cr_monitor.daily_monitor import set_color
from cr_monitor.daily_DTFmonitor import DailyMonitorDTF
import copy, sys, os, datetime
from cr_assis.ssfoPnl import SsfoPnl
import pandas as pd
import numpy as np
from research.eva import eva

class DailySSFO(DailyMonitorDTF):
    def __init__(self, ignore_test=True):
        self.ignore_test = ignore_test
        self.strategy_name = "ssf_okexv5_spot_okexv5_uswap_btc"
        self.init_accounts()
        self.get_pnl_daily = SsfoPnl(accounts = list(self.accounts.values()))
    
    def get_change(self):
        self.funding_summary, self.funding, _ = eva.run_funding("okex", "spot", "okex", "usdt", datetime.date.today() + datetime.timedelta(days = -31), datetime.date.today(), play = False)
        self.funding_summary.drop("last_dt", inplace = True, axis = 1)
        self.funding_summary.drop("1t", inplace = True, axis = 1)
        self.funding_summary.dropna(subset = ["1d"], inplace = True)
        self.funding_summary.rename(columns = {"volume_U_24h": "vol_24h"}, inplace = True)
        for col in ["1d", "3d", "7d", "15d", "30d"]:
            num = int(col.split("d")[0]) * 3
            self.funding_summary[col + "_avg"] = self.funding_summary[col] / num
        self.funding = self.funding.T
        self.get_now_situation() if not hasattr(self, "now_situation") else None
        rate = pd.DataFrame(columns = ["next", "current"])
        for coin in self.funding_summary.index:
            data = eva.get_last_influx_funding(exchange_name="okex", pair_name=f"{coin.lower()}-usdt-swap")
            data.rename(columns = {"rate": "current", "next_fee": "next"}, inplace = True)
            data.drop("dt", inplace = True, axis = 1)
            data.drop("time", inplace = True, axis = 1)
            rate.loc[coin] = data.loc[0]
        for account in self.accounts.values():
            account.get_account_position() if not hasattr(account, "position") else None
            if hasattr(account, "position"):
                self.funding_summary[account.parameter_name] = 0
                for coin in account.position.coin.values:
                    self.funding_summary.loc[coin.upper(), account.parameter_name] = float(account.position[account.position["coin"] == coin.lower()]["MV%"].values) / 100
        self.funding_summary = pd.concat([rate, self.funding_summary], axis = 1)
        result = copy.deepcopy(self.funding_summary)
        format_dict = {}
        for col in result.columns:
            if col != "vol_24h":
                format_dict[col] = '{0:.3%}'
            else:
                format_dict[col] = lambda x: format(round(x, 0), ",")
        funding_summary = result.style.format(format_dict)
        return funding_summary
    
    def run_daily(self) -> pd.DataFrame:
        rpnl = self.get_pnl_daily.get_rpnl()
        self.get_now_situation() if not hasattr(self, "now_situation") else None
        account_overall = self.now_situation.copy()
        for i in account_overall.index:
            parameter_name = account_overall.loc[i, "account"]
            account = self.accounts[parameter_name]
            for day in [1, 3, 7]:
                account_overall.loc[i, f"{day}d_rpnl%"] = rpnl[parameter_name][day]
        self.account_overall = account_overall.copy()
        format_dict = {'capital': lambda x: format(round(x, 4), ","), 
                        'rpnl%': '{0:.4%}', 
                        'MV%': '{0:.2f}', 
                        'mr': lambda x: format(round(x, 2), ","),
                        'week_profit': '{0:.4%}',
                        }
        account_overall = account_overall.style.format(format_dict)
        return account_overall