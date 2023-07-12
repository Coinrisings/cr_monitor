from cr_assis.account.accountOkex import AccountOkex
from cr_monitor.daily.dailyOkex import DailyOkex
from cr_monitor.mr.mrOkex import MrOkex
import pandas as pd
import numpy as np
import copy

m = MrOkex()
account = AccountOkex("bg_001@pt_okex_btc")
# m.price_range = [1]
ret = m.run_account_mr(account)
ret
# account.get_now_position()
# account.get_open_price()
# # m.change_position(account, "usdt", "ETH", -0.3, pd.DataFrame())
# # m.change_position(account, "usdt", "BETH", 0.3, pd.DataFrame())
# m.add_account_position(account, 'okex_spot-okex_usdt_swap', {'ltc':0,'doge':0,'people':0,'op':0,'arb':0,'aidoge':0})
# # m.add_account_position(account, 'okex_usd_swap-okex_usdt_swap', {'ada':-0.05,'sol':-0.1})
# account.now_position.fillna(0, inplace=True)
# account.get_now_price()
# m.position.now_position = account.now_position[m.position.contracts].copy()
# m.position.now_position.loc[account.usd_position.index, account.usd_position.columns] = account.usd_position
# m.position.open_price = account.open_price
# m.price_range = [0.5,0.6,0.7,0.8,0.9,1,1.1,1.2,1.3,1.4,1.5]
# ret = m.run_price_influence(now_price=account.now_price.copy(), equity={})
# ret


m = MrOkex()
m.btc_num = [50]
account = AccountOkex(deploy_id="1_1")
account.get_now_position()
account.get_open_price()

# account.get_cashBal(account.ccy)
m.change_position(account, "usdt", "ETH", -0.66, pd.DataFrame())
m.change_position(account, "usdt", "BETH", 0.66, pd.DataFrame())
m.add_account_position(account, "okex_spot-okex_usdt_swap", {"ltc": 0.3})
account.now_position.fillna(0, inplace=True)
account.get_now_price()
m.position.now_position = account.now_position[m.position.contracts].copy()
m.position.now_position.loc[account.usd_position.index, account.usd_position.columns] = account.usd_position
m.position.open_price = account.open_price
ret = m.run_price_influence(now_price=account.now_price.copy(), equity={})
m.account_mr = copy.deepcopy(ret)
add = {"okx_spot-okx_usdt_swap": {"ETH": -0.85, "BETH": 0.85}}
# add = {"okx_spot-okx_usdt_swap": {"ETH": -0.5, "BETH": 0.5, "LTC": 1}}
# now_price = pd.DataFrame(columns = ["usdt", "usdt-swap", "usdt-future", "usd-swap", "usd-future", "usdc-swap"])
# now_price.loc["FIL"] = 22.62
# now_price.loc["BTC"] = 29185
result = m.assumed_open(add)
result