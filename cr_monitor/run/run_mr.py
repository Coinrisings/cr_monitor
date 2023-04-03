from cr_monitor.position.Position_SSFO import PositionSSFO
from cr_monitor.mr.Mr_SSFO import MrSSFO
import pandas as pd
import copy


ssfo = MrSSFO(position = PositionSSFO())
ret = ssfo.run_account_mr(client = "bm", username = "bm001")
print(ret)

position = PositionSSFO(client = "ljw", username = "001")
mr = position.cal_mr()
print(mr)
