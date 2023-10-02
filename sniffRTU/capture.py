import serial
import time
import atexit

from loguru import logger
from sniffRTU.tinytsdb import DB

class RTU:
    def __init__(self, port, baudrate, timeout=3, tsdb=None):
        self.port = port
        self.baudrate = baudrate 
        self.timeout = 3  # Timeout for reading data (in seconds)

        self.db = tsdb or DB()

        self.ser = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
        atexit.register(self.tearDown)
        logger.info(f"Connected to {self.port} at {self.baudrate} baud")

    def capture(self, period=None):
        '''
        Capture for `period` seconds or unit you hit Ctrl+C.  By default the period is forever
        '''
        start_cap = time.time()
        try:
            while True:
                # Read data from the serial port
                data = self.ser.read(self.ser.in_waiting)

                # Check if data is received
                if data:
                    # Print data to the screen in hexadecimal format
                    formatted_data = ' '.join([f"{byte:02X}" for byte in data])
                    self.db.insert({'data': formatted_data})
                    logger.debug(formatted_data)
                else:
                    if period and (time.time() > start_cap+period):
                        return None

        except KeyboardInterrupt:
            logger.warning("\nCapture stopped by user.")

    def tearDown(self):
        self.ser.close()

def main(args):
    db = DB(tablename=args.session_name)
    # Create an RTU object based on command-line arguments
    rtu = RTU(port=args.port, baudrate=args.baudrate, tsdb=db)
    
    # Perform the capture with the specified period
    rtu.capture(period=args.capture_period)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Modbus RTU Capture')

    # Add command-line arguments
    parser.add_argument('port', type=str, help='Serial port for communication (e.g., COM13)')
    parser.add_argument('--baudrate', type=int, default=19200, help='Baud rate for serial communication')
    parser.add_argument('--session_name', type=str, default=None, help="Name of this capture session.  You'll need this name later to retrieve the data.")
    parser.add_argument('--capture_period', type=float, default=0, help='Capture period in seconds.  Default is forever')

    args = parser.parse_args()
    main(args)