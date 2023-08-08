from cr_assis.account.accountOkex import AccountOkex
from cr_monitor.daily.dailyOkex import DailyOkex
from cr_monitor.mr.mrOkex import MrOkex
import pandas as pd
import numpy as np
add = {
    "okx_spot-okx_usd_swap": {},
    "okx_spot-okx_usdt_swap":{'beth': 5},
    "okx_spot-okx_usdc_swap":{},
    "okx_usd_swap-okx_usdt_swap":{},
    "okx_usd_swap-okx_usdc_swap":{},
    "okx_usdc_swap-okx_usdt_swap":{}
}
m = MrOkex()
m.btc_num = [0.2]
# m.price_range = [1]
result = m.assumed_open(add)
result

m = MrOkex()
account = AccountOkex("wzok_002@pt_okex_btc")
m.btc_num = [0.2]
m.price_range = [1]
ret = m.run_account_mr(account, add = add)
ret