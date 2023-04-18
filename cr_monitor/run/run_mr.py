from cr_monitor.position.Position_SSFO import PositionSSFO
from cr_monitor.position.Position_DTC import PositionDTC
from cr_monitor.position.Position_DT import PositionDT
from cr_monitor.mr.Mr_DT import MrDT
from cr_monitor.mr.Mr_SSFO import MrSSFO
from cr_monitor.mr.Mr_DTC import MrDTC
import pandas as pd
import numpy as np
import copy
mr = MrDT(position = PositionDT())
mr.assumed_coins = {"ETC", "XLM"}
mr.num_range = np.arange(0.05, 0.1, 0.01)
mr.mul_range = np.arange(2, 5, 0.2)
ret = mr.run_assumed_open()


mr = MrDTC(position = PositionDTC())
# mr.mul_range = np.arange(0.5, 2, 0.1)
# mr.price_range = np.arange(1, 5, 0.1)
# mr.assumed_coins = {"FITFI"}
ret = mr.run_assumed_open()
# result = pd.DataFrame()
# for num in ret.keys():
#     for mul in ret[num].keys():
#         result.loc[mul, num] = ret[num][mul][1]
mr_ = MrDT(position = PositionDT())
mr_.mul_range = np.arange(0.1, 1.1, 0.1)
mr_.assumed_coins = ["ETC"]
ret_ = mr_.run_assumed_open()
1111111