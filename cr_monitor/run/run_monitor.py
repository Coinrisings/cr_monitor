from cr_assis.load import *
from cr_monitor.daily.daily_DTC import DailyDTC

daily = DailyDTC()
position_change = daily.get_position_change(start = "now() - 3h", end = "now()")
now_situation = daily.get_now_situation()
account_overall = daily.run_daily()
daily.daily_run_chance()