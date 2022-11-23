from capital_monitor import CapitalMonitor
import datetime, time
from daily_monitor import DailyMonitorDTO

while True:
    cm  = CapitalMonitor()
    if datetime.datetime.utcnow().hour == 2:
        cm.run_monitor_delist()
    cm.run_monitor_assets()
    cm.run_monitor_pnl()
    time.sleep(3600)