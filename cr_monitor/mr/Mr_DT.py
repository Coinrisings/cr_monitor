from cr_monitor.mr.Mr_DTC import MrDTC
from cr_monitor.position.Position_DT import PositionDT

class MrDT(MrDTC):
    
    def __init__(self, position: PositionDT):
        self.position = position
        self.ccy = "BTC"
        self.assumed_coins = {"BTC"}