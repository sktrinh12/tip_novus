import logging
from functools import wraps
from datetime import datetime
import os

def create_logger(name, level = logging.INFO):
    """
    Creates a logging object and returns it
    """
    current_date = str(datetime.now().strftime('%G-%m-%d'))
    fpath = os.path.join(os.path.dirname(__file__), 'logs/')
    #fpath = '/home/pi/mount/ndrive/logs'

    # create the logging file handler
    logger = logging.getLogger(name)
    logger.setLevel(level)
    fh = logging.FileHandler(f'{fpath}{current_date}_{name.upper()}.log', mode='a+')
    fmt = "%(asctime)s, %(name)s, %(levelname)s,\t%(message)s"
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
