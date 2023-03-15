from cr_assis.draw import draw_ssh
from cr_assis.load import *
print(f"running time: {datetime.datetime.now()}")

data = pd.read_csv("/Users/ssh/Downloads/funding.csv", index_col=0)
data.index = pd.to_datetime(data.index)
data