from capital_monitor import CapitalMonitor
import datetime, time

while True:
    cm  = CapitalMonitor()
    cm.run_monitor_assets()
    cm.run_monitor_pnl()
    cm.run_monitor_delist()
    time.sleep(30*60)