from cr_monitor.position.Position_SSFO import PositionSSFO
from cr_monitor.position.Position_DTC import PositionDTC
from cr_monitor.mr.Mr_SSFO import MrSSFO
from cr_monitor.mr.Mr_DTC import MrDTC
import pandas as pd
import copy


dtc = MrDTC(position = PositionDTC())
ret = dtc.run_assumed_open()
ret = dtc.run_account_mr(client = "anta", username = "anta001")
print(ret)

p = PositionDTC(client = "ch", username = "ch005")
mr = p.cal_mr()
print(mr)