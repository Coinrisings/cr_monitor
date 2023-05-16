from cr_assis.account.accountOkex import AccountOkex
from cr_monitor.daily.dailyOkex import DailyOkex
from cr_monitor.mr.mrOkex import MrOkex
import pandas as pd
import numpy as np
import copy

daily = DailyOkex()
ret = daily.get_account_mr(is_color=False)

m = MrOkex()
# add = {"okx_usd_swap-okx_usdc_swap": {"BTC": -0.5}}
add = {}
all_ret = {}
for deploy_id in ["bg_bg003@dt_okex_cswap_okex_uswap_btc"]:
    account = AccountOkex(deploy_id=deploy_id)
    # m.price_range = np.arange(1, 1.1, 0.1)
    ret = m.run_account_mr(account = account, add = add)
    all_ret[account.parameter_name] = copy.deepcopy(ret)
data = pd.DataFrame.from_dict(all_ret)
data