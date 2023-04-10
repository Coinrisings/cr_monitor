from cr_monitor.position.Position_SSFO import PositionSSFO
from cr_monitor.position.Position_DTC import PositionDTC
from cr_monitor.position.Position_DT import PositionDT
from cr_monitor.mr.Mr_DT import MrDT
from cr_monitor.mr.Mr_SSFO import MrSSFO
from cr_monitor.mr.Mr_DTC import MrDTC
import pandas as pd
import copy

dt = MrDTC(position = PositionDTC())
ret = dt.run_assumed_open()
ret = dt.run_account_mr(client = "ch", username = "ch003")
print(ret)

p = PositionDT(client = "cr", username = "cr003")
mr = p.cal_mr()
print(mr)