from cr_assis.account.accountOkex import AccountOkex
from cr_monitor.daily.dailyOkex import DailyOkex
from cr_monitor.mr.mrOkex import MrOkex
import pandas as pd
import numpy as np
import copy

m = MrOkex()
account = AccountOkex("test_otest5@pt_okex_btc")
# m.price_range = [1]
ret = m.run_account_mr(account)
ret
