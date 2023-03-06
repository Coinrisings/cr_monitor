import sys, os, datetime, glob, time, math, configparser, json, yaml
sys.path.append(f"/Users/ssh/Documents/GitHub/cr_monitor")
sys.path.append(f"/Users/ssh/Documents/GitHub/cr_assis")
from load import *
from daily_FsoUC import DailyFsoUC
from bokeh.io import output_notebook
from comboCompare import ComboCompare
from daily_FsoUC import DailyFsoUC
daily = DailyFsoUC(delivery="230331",ignore_test= True)
account_overall = daily.run_daily()
account_overall