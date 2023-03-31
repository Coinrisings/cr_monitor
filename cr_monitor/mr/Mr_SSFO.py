from cr_monitor.position.Position_SSFO import PositionSSFO

class MrSSFO(object):
    """SSFO means spot and usdt_swap in okex."""
    
    def __init__(self, position: PositionSSFO):
        self.position = position