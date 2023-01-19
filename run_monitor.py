from capital_monitor import CapitalMonitor
import datetime, time, os, yaml
from daily_monitor import DailyMonitorDTO
from daily_DTFmonitor import DailyMonitorDTF
from IPython.display import display
with open(f"{os.environ['HOME']}/.cryptobridge/private_key.yml", "rb") as f:
    data = yaml.load(f, Loader= yaml.SafeLoader)
for info in data:
    if "mongo" in info.keys():
        os.environ["MONGO_URI"] = info['mongo']
        os.environ["INFLUX_URI"] = info['influx']
        os.environ["INFLUX_MARKET_URI"] = info['influx_market']

daily = DailyMonitorDTF(ignore_test= False)
now_situation = daily.get_now_situation()
display(now_situation)
value, spread = daily.run_mr()

while True:
    cm  = CapitalMonitor()
    if datetime.datetime.utcnow().hour == 2:
        cm.run_monitor_delist()
    cm.run_monitor_assets()
    cm.run_monitor_pnl()
    time.sleep(3600)