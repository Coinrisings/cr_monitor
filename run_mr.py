from Mr_DTF import MrDTF
from Mr_DTO import MrDTO
from MrFso_UC import FsoUC
import os, yaml, sys
import pandas as pd
sys.path.append("/Users/ssh/Documents/GitHub/cr_assis")
from accountBase import AccountBase

from comboCompare import ComboCompare
compare = ComboCompare()
compare.get_spread_profit()

account = AccountBase(deploy_id = "ljw_001@dt_okex_uswap_okex_cfuture_btc")
now_position = account.get_now_position()
account.get_equity()
now_price = account.get_coin_price(coin = "btc")
#初始化账户
mr_dto = FsoUC(amount_c = now_position.loc["btc", "slave_number"],
                amount_u = round(now_position.loc["btc", "master_number"] * 100, 0),
                amount_fund = account.adjEq / now_price,
                price_u = now_position.loc["btc", "master_open_price"], 
                price_c = now_position.loc["btc", "slave_open_price"],
                now_price = now_price, 
                suffix = "230331")
mr_dto.run_mmr(play = False)

add = 2.5
with open(f"{os.environ['HOME']}/.cryptobridge/private_key.yml", "rb") as f:
    data = yaml.load(f, Loader= yaml.SafeLoader)
for info in data:
    if "mongo" in info.keys():
        os.environ["MONGO_URI"] = info['mongo']
        os.environ["INFLUX_URI"] = info['influx']
bg003 = AccountBase(deploy_id = "bg_bg003@dt_okex_uswap_okex_cfuture_btc")
account = bg003

# now_price = account.get_coin_price(coin = "btc")
# account.get_equity()
# now_position = pd.DataFrame()
# mul = 2.2
# amount_fund = 100
# coin = "btc"
# now_position.loc[coin, "master_open_price"] = now_price
# now_position.loc[coin, "slave_open_price"] = now_price
# now_position.loc["btc", "slave_number"] = amount_fund * mul
# now_position.loc["btc", "master_number"] = round(account.adjEq * mul / 100, 0)
now_position = account.get_now_position()
now_price = account.get_coin_price(coin = "btc")
account.get_equity()
add_value = add * account.adjEq
add_coin = add_value / now_price
now_position.loc["btc", "master_number"] += add_coin
now_position.loc["btc", "slave_number"] += int(add_value / 100)
now_position.loc["btc", "slave_MV"] += add_value
now_position.loc["btc", "master_MV"] += add_value
now_position.loc["btc", "slave_open_price"] = now_position.loc["btc", "slave_MV"] / now_position.loc["btc", "master_number"]
now_position.loc["btc", "master_open_price"] = now_position.loc["btc", "master_MV"] / now_position.loc["btc", "master_number"]
mr = FsoUC(amount_c = now_position.loc["btc", "slave_number"],
                amount_u = round(now_position.loc["btc", "master_number"] * 100, 0),
                amount_fund = account.adjEq / now_price,
                price_u = now_position.loc["btc", "master_open_price"], 
                price_c = now_position.loc["btc", "slave_open_price"],
                now_price = now_price, 
                suffix = "230331")
mr.get_contractsize()
mr.run_mmr(play = False)
print(f"现在账户的有效保证金为：{mr.amount_fund * mr.now_price}")
print(f"现在账户的维持保证金为：{sum(mr.mainten_swap.values()) + sum(mr.mainten_spot.values())}")
print(f"现在账户的mr为：{mr.mr}")
print(f"{account.parameter_name} finished!")