import sys, os, datetime, glob, time, math, configparser, json, yaml
import pandas as pd
sys.path.append(f"/Users/ssh/Documents/GitHub/cr_monitor")
sys.path.append(f"/Users/ssh/Documents/GitHub/cr_assis")
from load import *
from Position_SSFO import PositionSSFO
from accountBase import AccountBase
position_ssfo = PositionSSFO()
bg001 = AccountBase(deploy_id= "bg_001@ssf_okexv5_spot_okexv5_uswap_btc")
bg001.position_ssfo = position_ssfo
result = position_ssfo.get_origin_slave(client = "bg", username = "001", start = "now() - 1h", end = "now()")
position_ssfo.get_slave_mv()
# data = pd.DataFrame(result.get_points())
position = position_ssfo.origin_slave.copy()
bg001.get_equity()
for pair, data in position.items():
    data['mv%'] = round(data["mv"] / bg001.adjEq * 100, 4)
position