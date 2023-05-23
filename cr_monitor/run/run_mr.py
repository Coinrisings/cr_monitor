from cr_assis.account.accountOkex import AccountOkex
from cr_monitor.daily.dailyOkex import DailyOkex
from cr_monitor.mr.mrOkex import MrOkex
import pandas as pd
import numpy as np
import copy


m = MrOkex()
m.price_range = [0.3, 0.5, 0.7, 1, 2, 3, 4, 5, 6, 7, 8]
m.btc_num = [50]
# add = {"okx_usdt_swap-okx_usd_swap": {"BTC": -2.5, "DOGE": 0.5, "LTC": 0.5}}
add = {"okx_spot-okx_usdt_swap": {"AIDOGE": 1}}
result = m.assumed_open(add)
# add = {}
all_ret = {}
for deploy_id in ["bg_bg003@dt_okex_cswap_okex_uswap_btc"]:
    account = AccountOkex(deploy_id=deploy_id)
    # m.price_range = np.arange(1, 1.1, 0.1)
    ret = m.run_account_mr(account = account, add = add)
    all_ret[account.parameter_name] = copy.deepcopy(ret)
data = pd.DataFrame.from_dict(all_ret)
data