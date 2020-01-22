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
    # create the logging file handler
    logger = logging.getLogger(name)
    fh = logging.FileHandler(f'{fpath}{current_date}_{name.upper()}.log', mode='a+')
    fmt = "%(asctime)s, %(name)s, %(levelname)s [%(filename)s line:%(lineno)d],\t%(message)s"
    formatter = logging.Formatter(fmt, datefmt = "%d-%b-%G %H:%M:%S")
    fh.setFormatter(formatter)

    #add handler to logger object
    logger.addHandler(fh)
    return logger


tipnovus_logger = create_logger('tipnovus')

#only for tipnouvs
def logit(logger):
    def decorator_logit(func):
        @wraps(func)
        def wrapper_logit(args):
            if 'error' in args:
                tipnovus_logger.error(" | ".join([a for a in args if a != 'error']))
            else:
                if not isinstance(args, tuple):
                    tipnovus_logger.info(args)
                else:
                    tipnovus_logger.info(" | ".join(args))
            return func(args)
        return wrapper_logit
    return decorator_logit

