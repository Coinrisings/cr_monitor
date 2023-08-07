from cr_assis.account.accountOkex import AccountOkex
from cr_monitor.daily.dailyOkex import DailyOkex
from cr_monitor.mr.mrOkex import MrOkex
import pandas as pd
import numpy as np
import copy

add = {
    "okx_spot-okx_usd_swap": {'xrp':0.1},
    "okx_spot-okx_usdt_swap":{'beth': 0.5},
    "okx_spot-okx_usdc_swap":{'eth': 0},
    "okx_usd_swap-okx_usdt_swap":{},
    "okx_usd_swap-okx_usdc_swap":{},
    "okx_usdc_swap-okx_usdt_swap":{}
}
# m = MrOkex()
# m.btc_num = [60]
# m.price_range = [1]
# result = m.assumed_open(add)
# result

m = MrOkex()
account = AccountOkex("wzok_002@pt_okex_btc")
m.price_range = [1]
ret = m.run_account_mr(account, add = add)
ret