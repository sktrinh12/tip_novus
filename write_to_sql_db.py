from sqlite3_strcmd_test import *

str_cmd = input()
#str_cmd = 'washer'

with Database(db_file) as db:
    db.execute('''UPDATE tp_cmds SET ts = :ts, cmds = :str_cmd ''',\
                    {'ts':datetime.datetime.now(), 'str_cmd': str_cmd})
