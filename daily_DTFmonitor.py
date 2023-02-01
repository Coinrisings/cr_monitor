from daily_monitor import DailyMonitorDTO
from daily_monitor import set_color
import research.utils.pnlDaily as pnl_daily
import copy, datetime
from Mr_DTF import MrDTF
import pandas as pd
from research.eva import eva

class DailyMonitorDTF(DailyMonitorDTO):
    def __init__(self, delivery = "230331",ignore_test = True):
        self.delivery = delivery
        self.ignore_test = ignore_test
        self.strategy_name = "dt_okex_cfuture_okex_uswap"
        self.init_accounts()
        self.get_pnl_daily = pnl_daily
    
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
                mr_dto = MrDTF(amount_u = now_position.loc["btc", "slave_number"] * 100,
                            amount_c = now_position.loc["btc", "master_number"],
                            amount_fund = account.adjEq / now_price,
                            price_u = now_position.loc["btc", "slave_open_price"], 
                            price_c = now_position.loc["btc", "master_open_price"],
                            now_price = now_price, 
                            suffix= self.delivery)
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
    
    def get_btc_parameter(self):
        data = self.get_coin_parameter(coin = "btc", suffix=f"-usd-{self.delivery}")
        self.btc_parameter = data.copy()
    
    def get_eth_parameter(self):
        data = self.get_coin_parameter(coin = "eth", suffix=f"-usd-{self.delivery}")
        self.eth_parameter = data.copy()
    
    def get_change(self):
        coins = ["BTC", "ETH"]
        self.funding_summary, self.funding, _ = eva.run_funding("okex", "spot", "okex", "usdt", datetime.date(2021,1,1), datetime.date.today(), input_coins=coins, play = True)
        self.funding_summary.drop("last_dt", inplace = True, axis = 1)
        self.funding_summary.rename(columns = {"volume_U_24h": "vol_24h"}, inplace = True)
        self.funding = self.funding.T
        rate = pd.DataFrame(columns = ["current", "next"])
        for coin in coins:
            data = eva.get_last_influx_funding(exchange_name="okex", pair_name=f"{coin.lower()}-usdt-swap")
            data.rename(columns = {"rate": "current", "next_fee": "next"}, inplace = True)
            data.drop("dt", inplace = True, axis = 1)
            data.drop("time", inplace = True, axis = 1)
            rate.loc[coin] = data.loc[0]
        self.funding_summary = pd.concat([rate, self.funding_summary], axis = 1)
        result = copy.deepcopy(self.funding_summary)
        format_dict = {}
        for col in result.columns:
            if col != "vol_24h":
                format_dict[col] = '{0:.3%}'
            else:
                format_dict[col] = lambda x: format(round(x, 0), ",")
        funding_summary = result.style.format(format_dict).background_gradient(cmap='Blues')
        return funding_summary