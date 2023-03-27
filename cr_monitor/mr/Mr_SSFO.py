from cr_monitor.mr.Mr_DTO import MrDTO
from cr_monitor.position.Position_SSFO import PositionSSFO

class MrSSFO(MrDTO):
    """SSFO means spot and usdt_swap in okex."""
    
    def __init__(self, position: PositionSSFO):
        """_summary_

        Args:
            position (PositionSSFO): _description_
        """