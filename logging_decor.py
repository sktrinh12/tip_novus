import logging
from functools import wraps
from datetime import datetime
import requests
import os

time_host = "http://192.168.1.3:8020/time"
fpath = '/home/pi/mount/hampc/tp_logs/'

def get_time():
    return requests.get(time_host).json()['current_time']

def create_logger(name, level = logging.INFO):
    """
    Creates a logging object and returns it
    """
    try:
        # get just the date for log files
        current_date = get_time().split(' ')[0]
    except Exception:
        current_date = str(datetime.now().strftime('%G-%m-%d'))
    #fpath = os.path.join(os.path.dirname(__file__), 'logs/')

    # create the logging file handler
    logger = logging.getLogger(name)
    logger.setLevel(level)
    _fpath = os.path.join(fpath, 'logs')
    fh = logging.FileHandler(f'{_fpath}{current_date}_{name.upper()}.log', mode='a+')
    fmt = "%(asctime)s, %(name)s, %(levelname)s, %(threadName)s,\t%(message)s"
    formatter = logging.Formatter(fmt, datefmt = "%d-%b-%G %H:%M:%S")
    fh.setFormatter(formatter)

    #add handler to logger object
    logger.addHandler(fh)
    return logger


#only for tipnouvs
def logit(logger):
    """
    decorator tha twraps the passed in function and logs them
    @param logger: the logging object
    """
    def decorator_logit(func):
        @wraps(func)
        def wrapper_logit(args):
            if 'error' in args:
                logger.error(" | ".join([a for a in args if a != 'error']))
            else:
                if not isinstance(args, tuple):
                    logger.info(args)
                else:
                    logger.info(" | ".join(args))
            return func(args)
        return wrapper_logit
    return decorator_logit


global tipnovus_logger
tipnovus_logger = create_logger('tipnovus')


@logit(tipnovus_logger)
def handle_logs(args):
    return
    #print(args)
