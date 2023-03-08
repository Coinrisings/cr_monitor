from cr_monitor.mr.Mr_DTO import MrDTO

class MrSSFO(MrDTO):
    """SSFO means spot and usdt_swap in okex.

    """
    def __init__(self, amount_u: int, amount_c: float, amount_fund: float, price_u: float, now_price: float, coin="BTC"):
        """amount_u: the amount of USDT swap contracts(not coins) in holding position
        amount_c: the amount of spot assest in holding position
        amount_fund: the amount of asset 
        price_u: the average price of USDT swap in holding position
        now_price: the price of coin, now
        coin: the assest and position currency"""
        