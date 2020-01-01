import sqlite3
import sys
import logging
from datetime import datetime

fpath = "C:\\Program Files\\Hamilton\\logs\\tipNovus\\"
current_datetime = str(datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
current_date = current_datetime.split(' ')[0]

logging.basicConfig(filename=fpath + current_date + "_tipNovus_log.txt", \
                    filemode="a+", format="%(asctime)s, %(name)s, [%(filename)s_%(levelname)s_line:%(lineno)d], %(message)s", \
                    datefmt="%d-%b-%y %H:%M:%S", level=logging.DEBUG)

TableName = 'HAMTP_RTNRESP'
connect_string = 'C:/Program Files/Hamilton/sqlite3_db/hamiltonVantage.db'
str_resp = ''


class dbopen(object):
    """
    Simple CM for sqlite3 databases. Commits everything at exit.
    """
    def __init__(self, path):
        self.path = path
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.path)
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_class, exc, traceback):
        self.conn.commit()
        self.conn.close()

def read_str_resp():
    try:
        with dbopen(connect_string) as cur:
                cur.execute("SELECT response FROM '{0}'".format(TableName))
                result = cur.fetchone()
                if result:                    
                    return result[0]
    except Exception as e:
        logging.critical("problem connecting to sqlite3 db " + "> e: " + str(e))
        sys.stdout.write('error: ' + str(e) + "\n")
        return None
     
def write_str_resp(returnValue):
    try:
        with dbopen(connect_string) as cur:
                cur.execute("UPDATE '{0}' SET response='{1}'".format(TableName, returnValue))
                #result = cur.fetchone()
                #if result:                    
                #   return result[0]
    except Exception as e:
        logging.critical(f"problem connecting to sqlite3 db > {str(e)}")
        sys.stdout.write(f"problem connecting to sqlite3 db > {str(e)}\n")
        return None

if __name__ == "__main__":
    if sys.argv[1] == "read":
        str_resp = read_str_resp()
        logging.info(f"read sqlite3db: {str_resp}")
        sys.stdout.write(str_resp)
        sys.exit(0)
    if sys.argv[1].isdigit() and int(sys.argv[1]) < 10:        
        #update the value as the output string of the tipnovus api call (from within instint IV)

        write_str_resp(sys.argv[1])
        logging.info(f"updated sqlite3db: {sys.argv[1]}")
        sys.exit(0)
            
            
