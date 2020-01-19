import sqlite3
from flask import Flask, request
import os

app = Flask(__name__)


db_filepath = os.path.join(app.instance_path.replace('instance',''), 'db', 'tp_rest.db')

#{{{ TIP NOVUS DATABASE CLASS
class tpdb:
    def __init__(self, db_filepath):
        self.db_filepath = db_filepath
        self._conn = sqlite3.connect(self.db_filepath, detect_types = sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        self._cursor = self._conn.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        self._cursor.close()
        if isinstance(exc_val, Exception):
            self.connection.rollback()
        else:
            self.connection.commit()
        self.connection.close()

    @property
    def connection(self):
        return self._conn

    @property
    def cursor(self): #allows to treat the method like an attribute (syntatic sugar)
        return self._cursor

    def execute(self, sql, params=None):
        self.cursor.execute(sql, params or ())

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchone(self):
        return self.cursor.fetchone()

    def queryall(self, sql, params=None):
        self.cursor.execute(sql, params or ())
        return self.fetchall()

    def queryone(self, sql, params=None):
        self.cursor.execute(sql, params or ())
        return self.fetchone()[0]
#}}}
