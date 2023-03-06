from daily_monitor import set_color
from daily_DTFmonitor import DailyMonitorDTF
import copy, sys, os, datetime
from pathlib import Path
sys.path.append(os.path.dirname(f"{Path( __file__ ).parent.absolute()}") + "/cr_assis")
from fsoPnl import FsoPnl
import pandas as pd
import numpy as np
from research.eva import eva

class DailySSFO(DailyMonitorDTF):
    def __init__(self, ignore_test=True):
        self.ignore_test = ignore_test
        self.strategy_name = "ssf_okexv5_spot_okexv5_uswap_btc"
        self.init_accounts()
        self.get_pnl_daily = FsoPnl(accounts = list(self.accounts.values()))
    
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