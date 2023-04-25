from cr_monitor.position.Position_SSFO import PositionSSFO
from cr_monitor.position.Position_DTC import PositionDTC
from cr_monitor.position.Position_DT import PositionDT
from cr_monitor.mr.Mr_DT import MrDT
from cr_monitor.mr.Mr_SSFO import MrSSFO
from cr_monitor.mr.Mr_DTC import MrDTC
from cr_assis.account.accountBase import AccountBase
import pandas as pd
import numpy as np
import copy

des = 1
mr_dtc = MrDTC(position = PositionDTC(client = "ht", username="ht001"))
# mr_dtc.mul_range = np.arange(0.5, 2.1, 0.1)
# mr_dtc.num_range = np.arange(15, 55, 5)
# ret = mr_dtc.run_assumed_open()
mr_dtc.position.get_now_position()
mr_dtc.position.amount_master["BTC"] = mr_dtc.position.amount_master["BTC"] * des
mr_dtc.position.amount_slave["BTC"] = mr_dtc.position.amount_slave["BTC"] * des
mr_dtc.run_account_mr(client = "ht", username= "ht001")

mr_dt = MrDT(position = PositionDT())
mr_dt.mul_range = np.arange(0.1, 1.1, 0.1)
mr_dt.num_range = np.arange(15, 20, 5)
mr_dt.assumed_coins = ["ETC"]
ret = mr_dt.run_assumed_open()

num = 15
mr_dt.detail_mr = mr_dt.detail_open[num]
result = {}
for mul in mr_dt.detail_open[num].keys():
    change_ret = {}
    for change in set(mr_dtc.detail_mr.keys()) & set(mr_dt.detail_open[num][mul].keys()):
        dict1 = mr_dtc.detail_mr[change]
        dict2 = mr_dt.detail_open[num][mul][change]
        adjEq = min(dict1["adjEq"], dict2["adjEq"])
        mm = sum(dict1["mm_master"].values()) + sum(dict1["mm_slave"].values()) + sum(dict1["mm_upnl"].values()) + dict1["fee_mm"]+ sum(dict2["mm_master"].values()) + sum(dict2["mm_slave"].values()) + sum(dict2["mm_upnl"].values()) + dict2["fee_mm"]
        change_ret[change] = adjEq / mm
    result[mul] = copy.deepcopy(change_ret)

summary = pd.DataFrame()
for mul in result.keys():
    for change in result[mul].keys():
        summary.loc[change, mul] = result[mul][change]
summary.sort_index(inplace = True)

result = {}
for num in set(mr_dtc.detail_open.keys()) & set(mr_dt.detail_open.keys()):
    dtc_ret = {}
    for mul_dtc in mr_dtc.detail_open[num].keys():
        dt_ret = {}
        for mul_dt in mr_dt.detail_open[num].keys():
            change_ret = {}
            for change in set(mr_dtc.detail_open[num][mul_dtc].keys()) & set(mr_dt.detail_open[num][mul_dt].keys()):
                dict1 = mr_dtc.detail_open[num][mul_dtc][change]
                dict2 = mr_dt.detail_open[num][mul_dt][change]
                adjEq = min(dict1["adjEq"], dict2["adjEq"])
                mm = sum(dict1["mm_master"].values()) + sum(dict1["mm_slave"].values()) + sum(dict1["mm_upnl"].values()) + dict1["fee_mm"]+ sum(dict2["mm_master"].values()) + sum(dict2["mm_slave"].values()) + sum(dict2["mm_upnl"].values()) + dict2["fee_mm"]
                change_ret[change] = adjEq / mm
            dt_ret[mul_dt] = copy.deepcopy(change_ret)
        dtc_ret[mul_dtc] = copy.deepcopy(dt_ret)
    result[num] = copy.deepcopy(dtc_ret)
result
summary = pd.DataFrame()
num = 50
data = result[num]
for mul_dtc in data.keys():
    for mul_dt in data[mul_dtc].keys():
        summary.loc[mul_dtc, mul_dt] = data[mul_dtc][mul_dt][1]
summary