import logging
from functools import wraps
from datetime import datetime
import os

def create_logger():
    """
    Creates a logging object and returns it
    """
    current_date = str(datetime.now().strftime('%G-%m-%d'))
    fpath = os.path.join(os.path.dirname(__file__), 'logs/')
    logger = logging.getLogger('cmd_logger')
    logger.setLevel(logging.INFO)
    # create the logging file handler
    fh = logging.FileHandler(f'{fpath}{current_date}_tipnovus.log', mode='a+')
    fmt = "%(asctime)s, %(name)s, %(levelname)s [%(filename)s line:%(lineno)d],\t%(message)s"
    formatter = logging.Formatter(fmt, datefmt = "%d-%b-%G %H:%M:%S")
    fh.setFormatter(formatter)

    #add handler to logger object
    logger.addHandler(fh)
    return logger


logger = create_logger()


def logit(logger):
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

