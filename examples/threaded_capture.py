import time
import threading
from sniffRTU.capture import DB, RTU
from sniffRTU.analyze import Traffic
from dataclasses import asdict
import pandas as pd

port='COM13'
baudrate=19200
session_name='threadtest'
capture_period = None
output_filename = f'session_name.modbus.csv'


start_time = time.time()
db = DB(tablename=session_name)
    # Create an RTU object based on command-line arguments
rtu = RTU(port=port, baudrate=baudrate, tsdb=db)

def start(rtu=rtu, capture_period=capture_period):
    rtu.capture(period=capture_period)

capthread = threading.Thread(target=start)
capthread.start()
time.sleep(30)
end_time = time.time()

rtu.quit = True
capthread.join()

print(start_time, end_time)

traffic = Traffic(tablename=session_name).between(start=start_time-1, end=end_time+1)
hexl = traffic.as_hexl()
messages = traffic.to_messages(hexl=hexl)

records = []

for msg in messages:
    record = {'ts': msg.ts()}
    record.update(asdict(msg))
    record['msg'] = str(msg.__class__.__name__)
    records.append(record)
df = pd.DataFrame.from_records(records)
