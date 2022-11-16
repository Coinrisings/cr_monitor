import research, os, datetime, copy
import pandas as pd
import numpy as np
import research.utils.pnlDaily as pnl_daily
from pymongo import MongoClient
from research.utils.ObjectDataType import AccountData
from research.eva import eva
from Mr_DTO import MrDTO
from research.utils import draw_ssh
from bokeh.plotting import figure, show
from bokeh.models.widgets import Panel, Tabs

class DailyMonitorDTO(object):
    def __init__(self):
        self.init_accounts()
        self.get_pnl_daily = pnl_daily
    
    def get_now_parameter(self, deploy_id: str) -> pd.DataFrame:
        #获得mongo里面相应账户的信息
        client = deploy_id.split("_")[0]
        mongo_clt = MongoClient(os.environ["MONGO_URI"])
        a = mongo_clt["Strategy_deploy"][client].find({"_id": deploy_id})
        data = pd.DataFrame(a)
        data = data[data["_id"] == deploy_id].copy()
        data.index = range(len(data))
        return data
    
    def get_all_deploys(self) -> list:
        #获得所有启动的账户deploy_id
        mongo_clt = MongoClient(os.environ["MONGO_URI"])
        collections = mongo_clt["Strategy_orch"].list_collection_names()
        deploy_ids = []
        for key in collections:
            a = mongo_clt["Strategy_orch"][key].find()
            data = pd.DataFrame(a)
            data = data[(data["orch"]) & (data["version"] != "0") & (data["version"] != None) & (data["version"] != "0")].copy()
            deploy_ids += list(data["_id"].values)
        deploy_ids.sort()
        return deploy_ids
    
    def get_strategy_info(self, strategy: str):
        #解析deployd_id的信息
        words = strategy.split("_")
        master = (words[1] + "_" + words[2]).replace("okex", "okx")
        master = master.replace("uswap", "usdt_swap")
        master = master.replace("cswap", "usd_swap")
        slave = (words[3] + "_" + words[4]).replace("okex", "okx")
        slave = slave.replace("uswap", "usdt_swap")
        slave = slave.replace("cswap", "usd_swap")
        ccy = words[-1].upper()
        if ccy == "U":
            ccy = "USDT"
        elif ccy == "C":
            ccy = "BTC"
        else:
            pass
        return master, slave, ccy
    
    def get_bbu_info(self, strategy: str):
        #解析bbu线的deploy_id信息
        master = "binance_busd_swap"
        slave = "binance_usdt_swap"
        ccy = strategy.split("_")[-1].upper()
        if ccy in ["U", "BUSD"]:
            ccy = "USDT"
        else:
            pass
        return master, slave, ccy
    
    def init_accounts(self) -> None:
        #初始化所有DTO账户
        deploy_ids = self.get_all_deploys()
        accounts = {}
        for deploy_id in deploy_ids:
            parameter_name, strategy = deploy_id.split("@")
            client, username = parameter_name.split("_")
            if client not in ["test", "lxy"] and "dt_okex_cswap_okex_uswap" in strategy:
                #只监控dt-o的实盘账户
                master, slave, ccy = self.get_strategy_info(strategy)
                accounts[parameter_name] = AccountData(
                    username = username,
                    client = client,
                    parameter_name = parameter_name,
                    master = master,
                    slave = slave,
                    principal_currency = ccy,
                    strategy = "funding", 
                    deploy_id = deploy_id)
                parameter = self.get_now_parameter(deploy_id)
                path1 = parameter.loc[0, "secret_master"].replace("/", "__")
                path1 = path1.replace(":", "_")
                path2 = parameter.loc[0, "secret_slave"].replace("/", "__")
                path2 = path2.replace(":", "_")
                paths = [path1, path2]
                accounts[parameter_name].path_orders = paths
                accounts[parameter_name].path_ledgers = paths
            else:
                pass
        self.accounts = accounts.copy()
    
    def get_account_upnl(self) -> dict:
        #获得各个账户的upnl，用现在的现货价格减去开仓价格来计算
        position = {}
        for account in self.accounts.values():
            if not hasattr(account, "now_position"):
                now_position = account.get_now_position()
            else:
                now_position = account.now_position
            for coin in now_position.index:
                if account.contract_slave != "-usd-swap":
                    number = now_position.loc[coin, "slave_number"]
                else:
                    number = now_position.loc[coin, "master_number"]
                price = account.get_coin_price(coin = coin)
                upnl = abs(price - now_position.loc[coin, "slave_open_price"]) * number
                now_position.loc[coin, "upnl"] = upnl
            position[account.parameter_name] = now_position.copy()
        return position
    
    def run_daily(self) -> pd.DataFrame:
        result, account_overall = self.get_pnl_daily.run_daily_pnl(accounts = list(self.accounts.values()), save_excel = False)
        position = self.get_account_upnl()
        for i in account_overall.index:
            parameter_name = account_overall.loc[i, "account"]
            #total MV%
            self.accounts[parameter_name].get_account_position()
            account_overall.loc[i, "MV%"] = sum(self.accounts[parameter_name].position["MV%"].values)
            #mr
            self.accounts[parameter_name].get_mgnRatio()
            account_overall.loc[i, "mr"] = self.accounts[parameter_name].mr["okex"]
            #upnl
            upnl = sum(position[parameter_name]["upnl"].values)
            account_overall.loc[i, "upnl"] = upnl
        self.account_overall = account_overall
        return account_overall
    
    def get_change(self):
        result, funding = eva.observe_dt_trend()
        for col in funding.columns:
            funding[col] = funding[col].apply(lambda x: format(x, ".3%"))
        self.funding_summary = result
        self.funding = funding
    
    def run_mr(self):
        #推算每个账户的mr情况
        self.mgnRatio = {}
        tabs_value = []
        tabs_spread = []
        for name, account in self.accounts.items():
            if not hasattr(account, "now_position"):
                now_position = account.get_now_position()
            else:
                now_position = account.now_position
            now_price = account.get_coin_price(coin = "btc")
            account.get_equity()
            #初始化账户
            mr_dto = MrDTO(amount_u = now_position.loc["btc", "slave_number"] * 100,
                        amount_c = now_position.loc["btc", "master_number"],
                        amount_fund = account.adjEq / now_price,
                        price_u = now_position.loc["btc", "slave_open_price"], 
                        price_c = now_position.loc["btc", "master_open_price"],
                        now_price = now_price)
            mr_dto.run_mmr(play = False)
            #保留数据
            self.mgnRatio[name] = copy.deepcopy(mr_dto)
            #画图
            result = mr_dto.value_influence.copy()
            result["MarginCall"] = 3
            result["LimitClose"] = 6
            p1 = draw_ssh.line(result, x_axis_type = "linear", play = False, title = "value influence",
                            x_axis_label = "coin price", y_axis_label = "mr")
            tab1 = Panel(child=p1, title=name)
            result = mr_dto.spread_influence.copy()
            result["MarginCall"] = 3
            result["LimitClose"] = 6
            p2 = draw_ssh.line(result, x_axis_type = "linear", play = False, title = "spread influence",
                            x_axis_label = "spread", y_axis_label = "mr")
            tab2 = Panel(child=p2, title=name)
            tabs_value.append(tab1)
            tabs_spread.append(tab2)
        tabs_value_play = Tabs(tabs= tabs_value)
        tabs_spread_play = Tabs(tabs= tabs_spread)
        show(tabs_value_play)
        show(tabs_spread_play)