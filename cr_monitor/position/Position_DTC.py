from cr_monitor.position.Position_SSFO import PositionSSFO
import pandas as pd

class PositionDTC(PositionSSFO):
    
    def __init__(self, amount_master={}, amount_slave={}, price_master={},price_slave={}, equity={"USDT": 10000}, client = "", username = "") -> None:
        super().__init__(amount_master, amount_slave, price_master, price_slave, equity, client, username)
        self.master = "usd_swap"
        self.slave = "usdc_swap"
        
    def get_spot_price(self, coin: str) -> float:
        price = self.get_redis_price(coin = coin, suffix = "usd-swap")
        return price

    def get_slave_price(self, coin: str) -> float:
        price = self.get_redis_price(coin = coin, suffix = "usdc-swap")
        return price
    
    def get_origin_slave(self, start: str, end: str) -> dict:
        ret = super().get_origin_slave(start, end)
        pairs = list(ret.keys())
        for pair in pairs:
            if "usdc" != pair.split("-")[1]:
                del ret[pair]
        self.origin_slave = ret
        return ret