from typing import List, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
from crc import Crc16, Calculator

def raw_to_hexl(raw:str)->List:
    pairs = []
    for i in range(0, len(raw), 2):
        pair = raw[i:i+2]
        pairs.append(pair)
    return pairs

class IllegalFunctionCode(Exception):
    pass

class IncorrectLength(Exception):
    pass

class NoCRC(Exception):
    pass

PARSE_ERRORS = (IllegalFunctionCode, IncorrectLength, NoCRC)

@dataclass
class Message:
    slaveid: int
    fc: int    
    crc: str
    raw: str
    pairs: List[str]
    def check_crc(self):
        if (self.raw[-4:-2] not in self.crc) or (self.raw[-2:] not in self.crc):
            raise NoCRC(f'CRC must be in the raw string. {self.raw}, {self.crc}')

        calculator = Calculator(Crc16.MODBUS)
        hexl = raw_to_hexl(self.raw)

        data = bytes(int(b, 16) for b in hexl[:-2])
        calculated = calculator.checksum(data)
        
        crc_l = raw_to_hexl(self.crc)
        actual = int(crc_l[1]+crc_l[0], 16)  #the low byte is first in modbus so we reverse the order
        return calculated==actual
    def ts(self):
        return self.pairs[0].ts
    

@dataclass
class BadBytes(Message):
    slaveid: Optional[int] = None
    fc: Optional[int] = None
    crc: Optional[str] = None
    pairs: Optional[List] = None
    raw: Optional[str] = None

@dataclass
class Response(Message):
    pass

@dataclass
class Request(ABC, Message):
    total_length=8
    address: int
    @abstractmethod
    def response_class(self)-> Response:
        pass        


@dataclass 
class ReadResponse(Response):
    #slaveid: int
    #fc: int
    num_bytes: int
    payload: List
    total_length: int
    #raw: str
    #crc: str    

    @classmethod
    def from_hex(cls, hexl:List):
        '''
        hexl can be too long and the rest will be silently ignored
        '''
        if len(hexl) < 5:
            raise IncorrectLength(f'{hexl} is not long enough to be a {cls}')
        num_bytes = int( hexl[2], 16)
        total_length = num_bytes + 5 #total number of registers.  slaveid, fc, num_bytes, 2 for crc, plus the payload itself
        this_hexl = hexl[:total_length]
        

        slaveid = int(this_hexl[0], 16)
        fc = int(this_hexl[1], 16)
        payload = this_hexl[3:3+num_bytes]
        crc = ''.join(this_hexl[-2:])
        raw = ''.join(this_hexl)
        return cls(slaveid=slaveid, fc=fc, num_bytes=num_bytes, payload=payload, total_length=total_length, crc=crc, raw=raw, pairs=this_hexl)

    @classmethod
    def from_raw(cls, hexs:str):
        hexl = raw_to_hexl(hexs)
        return cls.from_hex(hexl)


@dataclass
class ReadRequest(Request):
    total_length=8
    #slaveid: int
    #fc: int
    #crc: str
    #raw: str    
    #address: int
    num_registers: int
    
    def response_class(self)-> ReadResponse:
        return ReadResponse

    @classmethod
    def from_hex(cls, hexl):
        if len(hexl) != 8:
            raise IncorrectLength(f"Must enter a list of 8 hex strings, each being 2 characters long.  Instead got {hexl}")
        slaveid = int(hexl[0], 16)
        fc = int(hexl[1], 16)
        if fc not in (3,4):
            raise IllegalFunctionCode(f'Unsupported function code {fc} from {hexl}')
        address = int(''.join(hexl[2:4]), 16)
        num_registers = int( ''.join(hexl[4:6]), 16)
        crc = ''.join(hexl[6:8])
        raw = ''.join(hexl)
        return cls(slaveid=slaveid, fc=fc, address=address, num_registers=num_registers, crc=crc, raw=raw, pairs=hexl)

    @classmethod
    def from_raw(cls, hexs:str):
        hexl = raw_to_hexl(hexs)
        return cls.from_hex(hexl)

@dataclass
class WriteSingleResponse(Response):
    #slaveid: int
    #fc: int
    address: int
    #crc: str
    #raw: str
    value: List
    total_length: int

    @classmethod
    def from_hex(cls, hexl):
        if len(hexl) < 5:
            raise IncorrectLength(f'{hexl} is not long enough to be a {cls}')
                    
        slaveid = int(hexl[0], 16)
        fc = int(hexl[1], 16)
        if fc != 6:
            raise IllegalFunctionCode(f'Unsupported function code {fc} from {hexl}')
        address = int(''.join(hexl[2:4]), 16)
        value = hexl[5:6]
        crc = ''.join(hexl[6:8])
        pairs = hexl[:8]
        raw = ''.join(pairs)
        return cls(slaveid=slaveid, fc=fc, address=address, value=value, total_length=8, crc=crc, raw=raw, pairs=pairs)

    @classmethod
    def from_raw(cls, hexs:str):
        hexl = raw_to_hexl(hexs)
        return cls.from_hex(hexl)


@dataclass
class WriteSingleRequest(Request):
    total_length=8
    slaveid: int
    fc: int
    address: int
    value: List
    crc: str
    raw: str

    def response_class(self)-> WriteSingleResponse:
        return WriteSingleResponse
    
    @classmethod
    def from_hex(cls, hexl):
        if len(hexl) != 8:
            raise IncorrectLength(f"Must enter a list of 8 hex strings, each being 2 characters long.  Instead got {hexl}")
        slaveid = int(hexl[0], 16)
        fc = int(hexl[1], 16)
        if fc not in [6]:
            raise IllegalFunctionCode(f'Unsupported function code {fc} from {hexl}')
        address = int(''.join(hexl[2:4]), 16)
        value = hexl[5:6]
        crc = ''.join(hexl[6:8])
        pairs = hexl[:8]
        raw = ''.join(pairs)
        return cls(slaveid=slaveid, fc=fc, address=address, value=value, crc=crc, raw=raw, pairs=pairs)

    @classmethod
    def from_raw(cls, hexs:str):
        hexl = raw_to_hexl(hexs)
        return cls.from_hex(hexl)

MESSAGES = [ReadRequest, ReadResponse, WriteSingleRequest, WriteSingleResponse]

def discover_message_type(hexl:List):
    for Msg in MESSAGES:
        msg = None
        try:
            msg = Msg.from_hex(hexl)
        except PARSE_ERRORS as e:
            pass

        
        if msg and msg.check_crc():
            return msg


if __name__ == '__main__':
    pass