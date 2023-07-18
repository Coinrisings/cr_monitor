from cr_assis.account.accountOkex import AccountOkex
from cr_monitor.daily.dailyOkex import DailyOkex
from cr_monitor.mr.mrOkex import MrOkex
import pandas as pd
import numpy as np
import copy

m = MrOkex()
m.btc_num = [0.09]
# m.price_range = [1]
add = {
    "okx_spot-okx_usdt_swap": {'ltc':0.5,'beth':0.5}
}
result = m.assumed_open(add)
result
m = MrOkex()
account = AccountOkex("test_otest8@pt_okex_btc")
# m.price_range = [1]
ret = m.run_account_mr(account)
ret
