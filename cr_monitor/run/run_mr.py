from cr_assis.account.accountOkex import AccountOkex
from cr_monitor.daily.dailyOkex import DailyOkex
from cr_monitor.mr.mrOkex import MrOkex
import pandas as pd
import numpy as np
import copy

m = MrOkex()
# m.price_range = [1]
# m.run_account_mr(account = AccountOkex(deploy_id="bm_bm001@pt_okex_btc"))
# m.price_range = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 2, 3, 4, 5, 6, 7, 8]
# m.btc_num = [50]
# add = {"okx_usdt_swap-okx_usd_swap": {"BTC": -2.5, "DOGE": 0.5, "LTC": 0.5}}
account = AccountOkex("bm_bm001@pt_okex_btc")
account.get_now_position()
account.get_open_price()
account.get_now_price()
# account.get_cashBal(account.ccy)
m.change_position(account, "usdt", "ETH", -0.66, pd.DataFrame())
m.change_position(account, "usdt", "BETH", 0.66, pd.DataFrame())
account.now_position.fillna(0, inplace=True)
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