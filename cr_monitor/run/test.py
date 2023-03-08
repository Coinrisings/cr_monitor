import sys, os, datetime, glob, time, math, configparser, json, yaml
from cr_assis.draw import draw_ssh
from cr_assis.load import *
from cr_monitor.daily.daily_SSFO import DailySSFO
from cr_monitor.position.Position_SSFO import PositionSSFO
from cr_assis.account.accountBase import AccountBase
daily = DailySSFO()
print(f"running time: {datetime.datetime.now()}")

account_overall = daily.run_daily()
account_overall