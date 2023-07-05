from cr_assis.account.accountOkex import AccountOkex
from cr_monitor.daily.dailyOkex import DailyOkex
from cr_monitor.mr.mrOkex import MrOkex
import pandas as pd
import numpy as np
import copy

m = MrOkex()
m.price_range = [1]
# m.run_account_mr(account = AccountOkex(deploy_id="bm_bm001@pt_okex_btc"), add = {"okex_spot-okex_usdt_swap":{"btc":0.1}})
# m.price_range = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 2, 3, 4, 5, 6, 7, 8]
m.btc_num = [50]
# add = {"okx_usdt_swap-okx_usd_swap": {"BTC": -2.5, "DOGE": 0.5, "LTC": 0.5}}
add = {"okx_spot-okx_usdt_swap": {"BTC": -2.5}}
# now_price = pd.DataFrame(columns = ["usdt", "usdt-swap", "usdt-future", "usd-swap", "usd-future", "usdc-swap"])
# now_price.loc["FIL"] = 22.62
# now_price.loc["BTC"] = 29185
result = m.assumed_open(add)
result