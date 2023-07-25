from cr_assis.account.accountOkex import AccountOkex
from cr_monitor.daily.dailyOkex import DailyOkex
from cr_monitor.mr.mrOkex import MrOkex
import pandas as pd
import numpy as np
import copy
add = {
    "okx_spot-okx_usdt_swap": {'eth':-1,'beth':1}
}
m = MrOkex()
m.btc_num = [0.1]
m.price_range = [1]
result = m.assumed_open(add)
result

m = MrOkex()
account = AccountOkex("test_otest7@pt_okex_btc")
# m.price_range = [1]
ret = m.run_account_mr(account)
ret
