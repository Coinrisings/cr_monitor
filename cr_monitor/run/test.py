from cr_assis.load import *
from cr_assis.draw import draw_ssh
from cr_monitor.daily.daily_SSFO import DailySSFO
from cr_monitor.position.Position_SSFO import PositionSSFO
daily = DailySSFO()
print(f"running time: {datetime.datetime.now()}")

position_change = daily.get_position_change(start = "now() - 30m", end = "now()")
position_change