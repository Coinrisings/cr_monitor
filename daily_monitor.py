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
        """初始化所有DTO账户"""
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
            if len(now_position) >0:
                for coin in now_position.index:
                    if account.contract_slave != "-usd-swap":
                        number = now_position.loc[coin, "slave_number"]
                    else:
                        number = now_position.loc[coin, "master_number"]
                    price = account.get_coin_price(coin = coin)
                    upnl = abs(price - now_position.loc[coin, "slave_open_price"]) * number
                    now_position.loc[coin, "upnl"] = upnl
            else:
                now_position.loc[coin, "upnl"] = 0
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
        self.account_overall = account_overall.copy()
        format_dict = {'capital': lambda x: format(round(x, 4), ","), 
               'daily_pnl': '{0:.4f}', 
               'daily_pnl%': '{0:.4%}', 
               #'规模对应日期':lambda x: "{}".format(x.strftime('%Y%m%d')),
               'combo_avg': '{0:.4%}', 
               'MV%': '{0:.2f}', 
               'mr': lambda x: format(round(x, 2), ","),
               'upnl': lambda x: format(round(x, 2), ",")
                }
        account_overall = account_overall.style.format(format_dict).background_gradient(cmap='Blues', subset = ["daily_pnl", "daily_pnl%", "MV%", "mr", 'upnl'])
        return account_overall
    
    def get_change(self):
        result, funding = eva.observe_dt_trend()
        self.funding_summary = copy.deepcopy(result)
        self.funding = copy.deepcopy(funding)
        format_dict = {}
        for col in result.columns:
            if col != "vol_24h":
                result[col] = result[col].apply(lambda x: float(x.split("%")[0])/100)
                format_dict[col] = '{0:.3%}'
            else:
                result[col] = result[col].apply(lambda x: float(x.replace(",", "")) if type(x) == str else np.nan)
                format_dict[col] = lambda x: format(round(x, 0), ",")
        funding_summary = result.style.format(format_dict).background_gradient(cmap='Blues')
        return funding_summary
    
    def get_btc_parameter(self):
        data = pd.DataFrame(columns = ["open", "close_maker","position", "close_taker",
                               "open2", "close_maker2", "position2", "close_taker2",
                              "fragment", "fragment_min", "funding_fee_loss_stop_open", "funding_fee_profit_stop_close", "timestamp"])
        contract = "btc-usd-swap"
        for name, account in self.accounts.items():
            origin_data = account.get_now_parameter()
            side = account.get_now_position().loc["btc", "side"]
            parameter = origin_data.loc[0, "spreads"][contract]
            timestamp = origin_data.loc[0, "_comments"]["timestamp"]
            for col in ["open", "close_maker","position", "close_taker"]:
                data.loc[name, col] = parameter[side][0][col]
            for col in ["open2", "close_maker2","position2", "close_taker2"]:
                data.loc[name, col] = parameter[side][1][col.split("2")[0]]
            for col in ["fragment", "fragment_min", "funding_fee_loss_stop_open", "funding_fee_profit_stop_close"]:
                data.loc[name, col] = parameter["ctrl"][col]
            data.loc[name, "timestamp"] = timestamp
        self.btc_parameter = data.copy()
    
    def run_mr(self):
        #推算每个账户的mr情况
        self.mgnRatio = {}
        tabs = []
        self.picture_value = pd.DataFrame()
        self.picture_spread = pd.DataFrame()
        now_price = list(self.accounts.values())[0].get_coin_price(coin = "btc")
        cols = []
        for name, account in self.accounts.items():
            if not hasattr(account, "now_position"):
                now_position = account.get_now_position()
            else:
                now_position = account.now_position
            if "btc" in now_position.index:
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
                self.picture_value = pd.concat([mr_dto.value_influence, self.picture_value], axis = 1, join = 'outer')
                self.picture_spread = pd.concat([mr_dto.spread_influence, self.picture_spread], axis = 1, join = 'outer')
                self.picture_value.rename({"mr": name}, inplace = True, axis = 1)
                self.picture_spread.rename({"mr": name}, inplace = True, axis = 1)
        value = copy.deepcopy(self.picture_value)
        spread = copy.deepcopy(self.picture_spread)
        value = value.style.applymap(set_color)
        spread = spread.style.applymap(set_color)
        return value, spread
        #画图
        # p1 = draw_ssh.line(self.picture_value, x_axis_type = "linear", play = False, title = "value influence",
        #                 x_axis_label = "coin price", y_axis_label = "mr")
        # if type(p1) == list:
        #     tab1 = p1
        #     tabs = tabs + tab1
        # else:
        #     tab1 = Panel(child=p1, title="value influence")
        #     tabs.append(tab1)
        # p2 = draw_ssh.line(self.picture_spread, x_axis_type = "linear", play = False, title = "spread influence",
        #                 x_axis_label = "spread", y_axis_label = "mr")
        # if type(p2) == list:
        #     tab2 = p2
        #     tabs = tabs + tab2
        # else:
        #     tab2 = Panel(child=p2, title="value influence")
        #     tabs.append(tab2)
        # tabs_play = Tabs(tabs= tabs)
        # show(tabs_play)
def set_color(val):
    #set mr color
    if val <=3:
        color = 'red'
    elif val <=6:
        color = 'orange'
    else:
        color = 'green'
    return 'background-color: %s' % color