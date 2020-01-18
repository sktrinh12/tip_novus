from logging_decor import *
from time import sleep
import sys


@logit(logger)
def handle_logs(*args):
    return

def send_cmd(cmd):
    sleep(1.5)
    str_response = '#,01,ACK,1,#'
    sys.stdout.write(str_response + "(SUCCESS)\n")
    handle_logs(f'func: {send_cmd.__name__}',f'sent: {cmd}', f'resp: {str_response}')
    return [cmd, str_response]

if __name__ == "__main__":
    send_cmd('test')
