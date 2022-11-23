from Mr_DTO import MrDTO
from research.utils.ObjectDataType import AccountData
import os
add = 0
ch005 = AccountData(
	username = "ch005",
	client = "ch",
	parameter_name = "ch_ch005",
	master = "okx_usd_swap",
	slave = "okx_usdt_swap",
	principal_currency = "BTC",
	strategy = "funding",
    deploy_id = "ch_ch005@dt_okex_cswap_okex_uswap_btc")
for account in [ch005]:
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