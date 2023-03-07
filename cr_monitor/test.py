import sys, os, datetime, glob, time, math, configparser, json, yaml
from research.utils import draw_ssh
from cr_assis.load import *
from cr_monitor.daily_SSFO import DailySSFO
from cr_monitor.Position_SSFO import PositionSSFO
from cr_assis.accountBase import AccountBase
daily = DailySSFO()
print(f"running time: {datetime.datetime.now()}")

account_overall = daily.run_daily()
account_overall