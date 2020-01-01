import sqlite3

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


#{{{ DISPLAY TASKS FUNCTION
def dply_tasks(str_response):
    sub_str_response = str_response.split(',')[2]
    try:
        sub_str_response = sub_str_response.strip().replace('\x0b','')
        logging.debug(f"length of 'sub_str_response': {len(sub_str_response)}")
        if len(sub_str_response) == 3 or len(sub_str_response) == 4:
            cd1 = status_codes[sub_str_response[:2]]
            cd2 = status_codes_2[sub_str_response[2:]]
            sys.stdout.write(f"the compartment sent the status code: {sub_str_response}\n")
            sys.stdout.write(f"status code interpreted as: code1: {cd1}, code2: {cd2}\n")
            logging.info(f"the compartment sent the status code: {sub_str_response}")
            logging.info(f"status code interpreted as: code1: {cd1}, code2: {cd2}")
        elif len(sub_str_response) > 0 and len(sub_str_response) < 3:
            time_remaining = int(sub_str_response.strip())
            if time_remaining == 0:
                sys.stdout.write("the compartment is not in operation\n")
                logging.info("the compartment is not in operation")
            else:
                sys.stdout.write(f"time remaining for run is: {time_remaining}\n")
                logging.info(f"time remaining for run is: {time_remaining}")
    except Exception as e:
        sys.stdout.write(f"error parsing the sub_str_response : {sub_str_response.strip()} - {str(e)}\n")
        logging.info(f"error parsing the sub_str_response: {sub_str_response.strip()} - {str(e)}")
#}}}
