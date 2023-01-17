from Mr_DTF import MrDTF
from Mr_DTO import MrDTO
from research.utils.ObjectDataType import AccountData
import os, yaml
import pandas as pd

add = 1
with open(f"{os.environ['HOME']}/.cryptobridge/private_key.yml", "rb") as f:
    data = yaml.load(f, Loader= yaml.SafeLoader)
for info in data:
    if "mongo" in info.keys():
        os.environ["MONGO_URI"] = info['mongo']
        os.environ["INFLUX_URI"] = info['influx']
anta001 = AccountData(
	username = "anta001",
	client = "anta",
	parameter_name = "anta_anta1001",
	master = "okx_usd_swap",
	slave = "okx_usdt_swap",
	principal_currency = "BTC",
	strategy = "funding",
    deploy_id = "anta_anta001@dt_okex_cswap_okex_uswap_btc")

now_price = anta001.get_coin_price(coin = "btc")
anta001.get_equity()
now_position = pd.DataFrame()
mul = 2.5
amount_fund = 60
coin = "btc"
now_position.loc[coin, "master_open_price"] = now_price
now_position.loc[coin, "slave_open_price"] = now_price
now_position.loc["btc", "slave_number"] = amount_fund * mul
now_position.loc["btc", "master_number"] = round(anta001.adjEq * mul / 100,0)
mr_dtf = MrDTF(amount_u = now_position.loc["btc", "slave_number"] * 100,
                amount_c = now_position.loc["btc", "master_number"],
                amount_fund = anta001.adjEq / now_price,
                price_u = now_position.loc["btc", "slave_open_price"], 
                price_c = now_position.loc["btc", "master_open_price"],
                now_price = now_price, 
                suffix = "230331")
mr_dtf.get_contractsize()
mr_dtf.run_mmr(play = False)
print(f"现在账户的有效保证金为：{mr_dtf.amount_fund * mr_dtf.now_price}")
print(f"现在账户的维持保证金为：{sum(mr_dtf.mainten_swap.values()) + sum(mr_dtf.mainten_spot.values())}")
print(f"现在账户的mr为：{mr_dtf.mr}")

for account in [anta001]:
    now_position = account.get_now_position()
    now_price = account.get_coin_price(coin = "btc")
    account.get_equity()
    add_value = add * account.adjEq
    add_coin = add_value / now_price
    now_position.loc["btc", "slave_number"] += add_coin
    now_position.loc["btc", "master_number"] += int(add_value / 100)
    now_position.loc["btc", "slave_MV"] += add_value
    now_position.loc["btc", "master_MV"] += add_value
    now_position.loc["btc", "slave_open_price"] = now_position.loc["btc", "slave_MV"] / now_position.loc["btc", "slave_number"]
    now_position.loc["btc", "master_open_price"] = now_position.loc["btc", "master_MV"] / now_position.loc["btc", "slave_number"]
    
    mr_dto = MrDTO(amount_u = now_position.loc["btc", "slave_number"] * 100,
                amount_c = now_position.loc["btc", "master_number"],
                amount_fund = account.adjEq / now_price,
                price_u = now_position.loc["btc", "slave_open_price"], 
                price_c = now_position.loc["btc", "master_open_price"],
                now_price = now_price)
    mr_dto.run_mmr(title = f"{account.parameter_name} add {add}")
    print(f"{account.parameter_name} finished!")