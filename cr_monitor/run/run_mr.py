from cr_assis.account.accountOkex import AccountOkex
from cr_monitor.daily.dailyOkex import DailyOkex
from cr_monitor.mr.mrOkex import MrOkex
import pandas as pd
import numpy as np
import copy
add = {
    "okx_spot-okx_usdt_swap": {'blur':0.15,'ltc':0.1,'dydx':0.1,'cfx':0.1,'fil':0.1,'arb':0.1},
    "okx_spot-okx_usd_swap":{},
    "okx_usdc_swap-okx_spot":{},
    "okx_usd_swap-okx_usdt_swap":{'xrp':0.1},
    "okx_usd_swap-okx_usdc_swap":{},
    "okx_usdc_swap-okx_usdt_swap":{}
}
# m = MrOkex()
# m.btc_num = [0.1]
# m.price_range = [1]
# result = m.assumed_open(add)
# result

m = MrOkex()
account = AccountOkex("colin_001@pt_okex_btc")
# m.price_range = [1]
ret = m.run_account_mr(account, add = add)
ret
