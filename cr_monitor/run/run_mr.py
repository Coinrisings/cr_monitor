from cr_monitor.position.Position_SSFO import PositionSSFO
import pandas as pd
import copy

position = PositionSSFO(client = "cr", username = "cr001")
position.get_tier_slave(coin = "BTC")
mr = position.cal_mr()
print(mr)
now_price = copy.deepcopy(position.now_price_master)
for coin, price in now_price.items():
    now_price[coin] = now_price[coin] * 1.5
position.now_price_master = copy.deepcopy(now_price)
position.now_price_slave = copy.deepcopy(now_price)
mr1 = position.cal_mr()
print(mr1)


btc_price = 28214
btc_number = 0.07
fitfi_price = 0.0137
mul = 1.2
mv = btc_price * mul * btc_number
fitfi_number = mv / fitfi_price
amount_master = {"FITFI": fitfi_number}
amount_slave = {"FITFI": fitfi_number}