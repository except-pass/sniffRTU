import atexit
import time
import os

import pandas as pd
from tinydb import TinyDB

HERE = os.path.dirname(__file__)

class DB:
    tscol = 'ts'
    default_db_file_name = 'ts.db.json'
    default_table_name = 'session'
    def __init__(self, fpath=None, tablename=None):
        self.fpath = fpath or os.path.join(HERE, self.default_db_file_name)
        self._db = TinyDB(self.fpath)
        self.table = self._db.table(tablename or self.default_table_name)
        atexit.register(self._db.close)

    def insert(self, payload, ts=None):
        ts = time.time() if ts is None else ts
        insertme = payload.copy()
        insertme.update({self.tscol: ts})
        self.table.insert(insertme)

    def as_df(self):
        return pd.DataFrame.from_records(self.table.all())

    def delete_entire_db(self):
        self._db.close()
        os.remove(self.fpath)


if __name__ == '__main__':
    db = DB()

    #db.insert({'a': 1})
    #db.insert({'b': 2})
    #db.insert({'a': 3})
    #with pd.option_context('display.float_format', '{:0.9f}'.format):
    #    print(db.as_df())
