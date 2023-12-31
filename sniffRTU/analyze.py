from datetime import datetime
import pandas as pd
from loguru import logger
from dataclasses import asdict

from sniffRTU.tinytsdb import DB
from sniffRTU.parsehex import ReadRequest, WriteSingleRequest, Request, BadBytes, PARSE_ERRORS

def to_datetime(ts):
    if ts is None:
        return None
    try:
        ts = float(ts)
    except TypeError:
        pass
    try:
        ts = ts.astype(float)
    except AttributeError:
        pass
    try:
        return pd.to_datetime(ts, unit='s')
    except TypeError:
        return pd.to_datetime(ts)

class TSStr(str):
    def attach_timestamp(self, ts):
        self.ts = ts

class Traffic:
    tsdiff='tsdiff'
    def __init__(self, df=None, tsdb=None, tablename=None):
        '''
        Use the raw tsdb data in df.
        If df is not given, use the database tsdb.
        If tsdb is also not given, use the default database and tablename
        '''
        db = tsdb or DB(tablename=tablename)
        #df is a dataframe of the raw captured hex data, timestamped
        self.df = db.as_df() if df is None else df
        self.df.set_index(to_datetime(self.df['ts']), inplace=True)

    def between(self, start=None, end=None):
        filtered_df = self.df.copy()
        start = to_datetime(start)
        end = to_datetime(end)
        if start is not None:
            filtered_df = filtered_df[filtered_df.index >= start]
        if end is not None:
            filtered_df = filtered_df[filtered_df.index <= end]
        logger.debug(f'filtered from {self.df.shape} to {filtered_df.shape}')
        return Traffic(df=filtered_df)

    def as_hexl(self, max_rows=None):
        master_hexl = []
        for index, row in self.df.iterrows():
            if max_rows and index>max_rows:
                break
            str_pairs = row.data.split(' ')
            hexl_pairs = [TSStr(pair) for pair in str_pairs]
            [pair.attach_timestamp(row['ts']) for pair in hexl_pairs]
            master_hexl.extend(hexl_pairs)
        return master_hexl    

    def format_df(self):
        self.df[self.tsdiff] = self.df.ts-self.df.ts.shift(periods=1, axis=0)
        
    def group_messages(self, threshold=0.1):
        #FIX!
        commands = []
        serdat = []
        for index,row in self.df.iterrows():
            if row.tsdiff < threshold:
                serdat.extend(row.data.split(' '))
            else:
                commands.append(serdat)
                serdat = row.data.split(' ')
        return commands
    
    def to_messages(self, hexl=None):
        #REFACTOR ME PLEASE
        hexl = hexl or self.as_hexl()
        messages = []

        index = 0
        bad_bytes = 0
        while index < len(hexl)-8:
            msg = None
            logger.debug(index)
            try:
                candidate = hexl[index:index+8]
                msg = ReadRequest.from_hex(candidate)
                logger.debug(f'{msg} is a request')
            except PARSE_ERRORS as e:
                logger.debug(f"{candidate} is not a read request")

            if msg is None:
                try:
                    candidate = hexl[index:index+8]
                    msg = WriteSingleRequest.from_hex(candidate)
                    logger.debug(f'{msg} is a request')        
                except PARSE_ERRORS as e:
                    logger.debug(f"{candidate} is not a write single request")

            if msg and msg.check_crc():
                logger.debug(f'{msg} is a request')
            else:
                logger.debug(f"{msg} is not a request.  CRC may have failed")
                msg = None

            #next look for response
            resp = None
            if isinstance(msg, Request):
                resp_candidate = hexl[index+8:]
                logger.debug(f'looking for response in {resp_candidate[:8]}')

                try:
                    resp = msg.response_class().from_hex(resp_candidate)
                except PARSE_ERRORS as e:
                    logger.debug(f"The bytes that follow are not the response due to {e}")

                #responses must pass crc and must have the same slaveid as the message
                if resp and resp.check_crc() and (resp.slaveid==msg.slaveid):
                    logger.debug(f'{resp} is a response')
                    
                else:
                    logger.debug(f"{resp} is not a valid response to {msg}")
                    resp = None


            if msg is None and resp is None:
                index += 1
                bad_bytes += 1
            else:
                if bad_bytes:
                    messages.append(BadBytes(pairs=hexl[index-bad_bytes:index]))
            if msg:
                index += msg.total_length
                bad_bytes = 0
                messages.append(msg)        
            if resp:
                index += resp.total_length
                bad_bytes = 0            
                messages.append(resp)
        return messages
    
    def as_df(self) -> pd.DataFrame:
        '''
        Returns a dataframe of the parsed message data
        '''
        hexl = self.as_hexl()
        messages = self.to_messages(hexl=hexl)
        records = []

        for msg in messages:
            record = {'ts': msg.ts()}
            record.update(asdict(msg))
            record['msg'] = str(msg.__class__.__name__)
            records.append(record)
        df = pd.DataFrame.from_records(records)
        #df['dt'] = df['ts'] - df.iloc[0, 'ts']
        return df
