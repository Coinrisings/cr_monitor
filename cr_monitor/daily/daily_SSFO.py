from cr_monitor.daily.daily_monitor import set_color
from cr_monitor.daily.daily_DTFmonitor import DailyMonitorDTF
from cr_assis.connect.connectData import ConnectData
import copy, sys, os, datetime
from cr_assis.pnl.ssfoPnl import SsfoPnl
from cr_monitor.position.Position_SSFO import PositionSSFO
import pandas as pd
import numpy as np
from research.eva import eva
from cr_assis.account.accountBase import AccountBase

class DailySSFO(DailyMonitorDTF):
    def __init__(self, ignore_test=True):
        self.ignore_test = ignore_test
        self.database = ConnectData()
        self.strategy_name = "ssf_okexv5_spot_okexv5_uswap_btc"
        self.init_accounts()
        self.get_pnl_daily = SsfoPnl(accounts = list(self.accounts.values()))
    
    def get_now_mv_percent(self, account: AccountBase) -> float:
        account.get_equity()
        position = PositionSSFO() if not hasattr(account, "position_ssfo") else account.position_ssfo
        if not hasattr(position, "origin_slave"):
            position.get_origin_slave(client = account.client, username = account.username, start = "now() - 10m", end = "now()")
            position.get_slave_mv()
        for data in position.origin_slave.values():
            data.set_index("time", inplace = True)
            mv = sum(data[data.columns].values[-1])
            mv_precent = mv / account.adjEq
        return mv, mv_precent
    
    def get_now_situation(self) -> pd.DataFrame:
        """get account situation now, like MV%, capital, ccy, mr

        Returns:
            pd.DataFrame: columns = ["account", "capital", "ccy", "MV", "MV%", "mr", "week_profit"]
        """
        accounts = list(self.accounts.values())
        now_situation = pd.DataFrame(columns = ["account", "capital", "ccy", "MV", "MV%", "mr", "week_profit"], index = range(len(accounts)))
        start = "now() - 10m"
        end = "now()"
        for i in now_situation.index:
            account = accounts[i]
            mv, mv_precent = self.get_now_mv_percent(account)
            account.get_mgnRatio()
            capital_price = 1 if "USD" in account.principal_currency else account.get_coin_price(coin = account.principal_currency.lower())
            capital = account.get_mean_equity() / capital_price
            ccy = account.principal_currency
            mr = account.mr["okex"]
            profit = self.get_week_profit(account)
            now_situation.loc[i] = [account.parameter_name, capital, ccy, mv, mv_precent, mr, profit]
        self.now_situation = now_situation.copy()
        format_dict = { 'MV': '{0:.2f}', 
                        'MV%': '{0:.2f}', 
                        'mr': lambda x: format(round(x, 2), ","),
                        'week_profit': '{0:.4%}'}
        now_situation = now_situation.style.format(format_dict).background_gradient(cmap='Blues', subset = ["MV%", "mr", 'week_profit'])
        return now_situation
    
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
        all_position = self.get_all_position()
        for account in self.accounts.values():
            self.funding_summary[account.parameter_name] = 0
            for coin in all_position.index:
                self.funding_summary.loc[coin.upper(), account.parameter_name] = all_position.loc[coin, account.parameter_name] / 100
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
        fpnl = self.get_pnl_daily.get_fpnl()
        self.get_now_situation() if not hasattr(self, "now_situation") else None
        account_overall = self.now_situation.copy()
        for i in account_overall.index:
            parameter_name = account_overall.loc[i, "account"]
            account = self.accounts[parameter_name]
            for day in [1, 3, 7]:
                account_overall.loc[i, f"{day}d_rpnl%"] = rpnl[parameter_name][day]
                account_overall.loc[i, f"{day}d_fpnl%"] = fpnl[parameter_name][day]
        self.account_overall = account_overall.copy()
        format_dict = {'capital': lambda x: format(round(x, 4), ","), 
                        '1d_rpnl%': '{0:.4%}', 
                        '3d_rpnl%': '{0:.4%}', 
                        '7d_rpnl%': '{0:.4%}', 
                       '1d_fpnl%': '{0:.4%}', 
                        '3d_fpnl%': '{0:.4%}', 
                        '7d_fpnl%': '{0:.4%}', 
                        'MV%': '{0:.2f}', 
                        'mr': lambda x: format(round(x, 2), ","),
                        'week_profit': '{0:.4%}',
                        }
        account_overall = account_overall.style.format(format_dict).background_gradient(cmap='Blues', subset = ["MV%", "mr", 'week_profit','1d_rpnl%', '3d_rpnl%', '7d_rpnl%','1d_fpnl%', '3d_fpnl%', '7d_fpnl%'])
        return account_overall
    
    def get_mv_monitor(self, start = "now() - 1d", end = "now()") -> dict:
        mv_monitor = {}
        for name, account in self.accounts.items():
            account.position_ssfo = PositionSSFO() if not hasattr(account, "position_ssfo") else account.position_ssfo
            position = account.position_ssfo
            position.get_origin_slave(client = account.client, username = account.username, start = start, end = end)
            position.get_slave_mv()
            account.get_equity()
            for pair, data in position.origin_slave.items():
                data['mv%'] = round(data["mv"] / account.adjEq * 100, 4)
            mv_monitor[name] = position.origin_slave.copy()
        self.mv_monitor = mv_monitor
        return mv_monitor
    
    def get_all_position(self) -> pd.DataFrame:
        mv_monitor = self.get_mv_monitor(start = "now() - 5m")
        all_position = pd.DataFrame(columns = list(mv_monitor.keys()))
        for account in all_position.columns:
            account_position = mv_monitor[account].copy()
            for pair in account_position.keys():
                coin = pair.split("-")[0]
                all_position.loc[coin, account] = account_position[pair].fillna(method='ffill')["mv%"].values[-1]
        all_position.loc["total"] = all_position.sum(axis = 0)
        return all_position