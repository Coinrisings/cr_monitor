from cr_monitor.position.Position_SSFO import PositionSSFO
from cr_monitor.position.Position_DTC import PositionDTC
from cr_monitor.position.Position_DT import PositionDT
from cr_monitor.mr.Mr_SSFO import MrSSFO
from cr_monitor.mr.Mr_DTC import MrDTC
import pandas as pd
import copy


p = PositionDT(client = "cr", username = "cr003")
mr = p.cal_mr()
print(mr)

dt = MrDTC(position = PositionDT())
ret = dt.run_assumed_open()
ret = dt.run_account_mr(client = "anta", username = "anta001")
print(ret)

