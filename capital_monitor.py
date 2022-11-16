from research.utils import readData
from research.utils.ObjectDataType import AccountData
from daily_monitor import DailyMonitorDTO
import yaml, os, json, requests, datetime, copy

class CapitalMonitor(DailyMonitorDTO):
    def __init__(self):
        super().__init__()
        self.load_dingding()
        self.warning_hedge = 0
        self.warning_rebalance = 0
        self.warning_account = {"ssh": [],
                                "brad": [],
                                "yyz": [],
                                "scq": []}
    
    def load_dingding(self) -> None:
        user_path = os.path.expanduser('~')
        cfg_path = os.path.join(user_path, '.dingding')
        with open(os.path.join(cfg_path, 'key.yml')) as f:
            key = yaml.load(f, Loader = yaml.SafeLoader)
        self.dingding_config = key[1]
        combo_people = {
            "okx_usd_swap-okx_usdt_swap": "ssh",
            "gate_spot-gate_usdt_swap": "brad",
            "gate_usdt_swap-okx_usdt_swap": "yyz",
            "binance_busd_swap-binance_usdt_swap": "scq"
        }
        self.combo_people = combo_people
    
    def init_accounts(self) -> None:
        #初始化账户
        deploy_ids = self.get_all_deploys()
        accounts = {}
        for deploy_id in deploy_ids:
            parameter_name, strategy = deploy_id.split("@")
            client, username = parameter_name.split("_")
            if client not in ["test", "lxy"]:
                #只监控实盘账户
                if "h3f_binance_uswap_binance_uswap" not in strategy:
                    master, slave, ccy = self.get_strategy_info(strategy)
                else:
                    master, slave, ccy = self.get_bbu_info(strategy)
                accounts[parameter_name] = AccountData(
                    username = username,
                    client = client,
                    parameter_name = parameter_name,
                    master = master,
                    slave = slave,
                    principal_currency = ccy,
                    strategy = "funding", 
                    deploy_id = deploy_id)
            else:
                pass
        self.accounts = accounts.copy()
    
    def get_coins(self) -> None:
        #获得数据库里面所有需要对冲币种的名称
        a = """SHOW FIELD KEYS FROM "pnl_hedge" """
        data = readData.read_influx(a, db = "ephemeral")
        coins = list(data["fieldKey"].values)
        self.coins = coins
    
    def get_coins_str(self) -> None:
        if not hasattr(self, "coins"):
            self.get_coins()
        else:
            pass
        coins_str = ''
        for coin in self.coins:
            coins_str = coins_str + '"' + coin + '"' +","
        self.coins_str = coins_str[:-1]
    
    def get_cashbalance(self, account):
        a = f"""select {self.coins_str} from "pnl_hedge" where deploy_id = '{account.deploy_id}' and time > now() - 1d """
        data = readData.read_influx(a, db = "ephemeral", transfer= False)
        data.dropna(how = "all", axis = 1, inplace= True)
        data.fillna(0, inplace= True)
        cols = set(self.coins) & set(data.columns)
        for coin in cols:
            if coin not in ["usdt", "usd", "busd", "usdc"]:
                price = account.get_coin_price(coin = coin)
            else:
                price = 1
            data[coin] = data[coin] * price
        account.cashbalance = data.copy()
    
    def send_dingding(self, data: dict):
        url = self.dingding_config["url"]
        header = {
            "Content-Type": "application/json",
            "Charset": "UTF-8"
        }
        send_data = json.dumps(data)
        send_data = send_data.encode("utf-8")
        ret = requests.post(url = url, data = send_data, headers= header)
    
    def run_monitor_pnl(self):
        self.get_coins_str()
        warning_account = copy.deepcopy(self.warning_account)
        for name, account in self.accounts.items():
            self.get_cashbalance(account)
            if len(account.cashbalance) > self.warning_hedge:
                warning_people = self.combo_people[account.combo]
                warning_account[warning_people].append(name)
            else:
                pass
        #发送警告
        for people in warning_account.keys():
            number = len(warning_account[people])
            if number > 0:
                data = {
                    "msgtype": "text",
                    "text": {"content": f"""[AM]-[CashBalanceWarning] \n {warning_account[people]} CashBalance 过去1h对冲超过{self.warning_hedge}达到{number}次\n时间：{datetime.datetime.now()}"""},
                    "at": {
                        "atMobiles": [cm.dingding_config[people]],
                        "isAtAll": False}
                }
                self.send_dingding(data)
            else:
                pass
    
    def find_af_accounts(self) -> None:
        #找到跨所账户
        af_accounts = {}
        for name, account in self.accounts.items():
            if account.exchange_master != account.exchange_slave:
                af_accounts[name] = account
            else:
                pass
        self.af_accounts = af_accounts
    
    def load_af_config(self) -> None:
        #读取转账config
        with open("/home/tx/archive/yyz/automation/auto_transfer_config.json", "rb") as f:
            data = json.load(f)
        self.af_config = data
    
    def get_bilateral_assets(self, account) -> None:
        #获得两边的资产
        names = {"master": account.exchange_master, "slave": account.exchange_slave}
        assets = {}
        
        for key, exchange in names.items():
            if exchange in ["okex", "okx", "ok", "okex5", "o"]:
                exchange_name = "okexv5"
            else:
                exchange_name = exchange
            a = f"""
            SELECT last(usdt) as adjEq FROM "balance_v2" WHERE time > now() - 10m and username = '{account.username}' and client = '{account.client}' and exchange = '{exchange_name}' and balance_id != '{account.balance_id}'
            """
            data = readData.read_influx(a, transfer = False)
            assets[key] = float(data["adjEq"].values)
        account.assets = assets
    
    def run_monitor_assets(self):
        self.load_af_config()
        self.find_af_accounts()
        self.balance_limit = self.af_config["balance_limit"]
        warning_account = copy.deepcopy(self.warning_account)
        for name, account in self.af_accounts.items():
            self.get_bilateral_assets(account)
            balance_ratio = self.af_config["balance"][account.combo]
            if abs(account.assets["master"] / (balance_ratio * account.assets["slave"]) - 1) > self.warning_rebalance * self.balance_limit:
                warning_people = self.combo_people[account.combo]
                warning_account[warning_people].append(name)
            else:
                pass
        #发送警告
        for people in warning_account.keys():
            number = len(warning_account[people])
            if number > 0:
                data = {
                    "msgtype": "text",
                    "text": {"content": f"""[AM]-[RebalanceWarning] \n {warning_account[people]} 两边资金相差过大！\n时间：{datetime.datetime.now()}"""},
                    "at": {
                        "atMobiles": [cm.dingding_config[people]],
                        "isAtAll": False}
                }
                self.send_dingding(data)
            else:
                pass
            
    
cm  = CapitalMonitor()
cm.run_monitor_assets()
cm.run_monitor_pnl()
# cm.run_monitor_pnl()
