import requests
from socket import gethostname
from pprint import pprint
import argparse
#from tipnovus_class_api import send_cmd_dict
import re
import platform    # For getting the operating system name
import subprocess  # For executing a shell command

"""
    Script to interface with TipNovus instrument via the Hamilton Instinct V software. An API call can be made to the Flask web server on the raspberry pi (or other host) connected to the TipNovus instrument. Can be used as a CLI from terminal as well. The output is a simple 'OK' or 'BAD' based on the request status code, either 201 or 400; and the response string.

"""

def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """

    # Option for the number of packets as a function of
    param = '-n' if platform.system().lower()=='windows' else '-c'

    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', host]
    #will raise error if return value is not 0, suppresses output, redirect stdout and stderr to DEVNULL
    try:
        subprocess.check_call(command,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL
                                )
        return True
    except subprocess.CalledProcessError:
        return False


#for argparse endpoint choices
with open('send_cmds.csv', 'r') as f:
    available_word_cmds = f.readlines()[0].split(',')
with open('code_cmds.csv', 'r') as f:
    available_code_cmds = f.readlines()[0].split(',')

available_word_cmds = available_word_cmds + \
                [f'update/{cmds}' for cmds in available_word_cmds] + \
                ['connect','disconnect','response', 'cmds', 'record_video']

description = '''
    Call the tipnovus API using a url with endpoint that corresponds to the flask-restful defined endpoint. Used to issue commands, receive responses, list the available commands, connect and disconnect from the tipnovus instrument.
              '''

def setval_check(arg_string):
    if not re.search('[time|temp];\d{1,3}',arg_string):
        raise argparse.ArgumentTypeError(f'The set command is not valid -> {arg_string}')
    else:
        return arg_string

def allowed_cmds_check(arg_string):
    if arg_string not in available_code_cmds:
        # chk_setvar_flag = True
        if not re.search('01,TI,DR,[T|M][T|M],\d{1,3}#',arg_string):
            # chk_setvar_flag = False
            # raise argparse.ArgumentTypeError(f'The command string is not valid -> {arg_string}')
        # if not chk_setvar_flag:
            raise argparse.ArgumentTypeError(f'Invalid command string -> {arg_string}')
        else:
            return arg_string
    else:
        return arg_string

parser = argparse.ArgumentParser(description=description)
parser.add_argument('-e', '--endpoint', type=str, default='cmds',
                    choices=available_word_cmds, metavar='',
                    help='Enter an endpoint for the api')
parser.add_argument('-t', '--request_type', type=str, required=True,
                    choices=['put', 'get'], metavar='',
                    help='What type of request? (get, put)')

# group = parser.add_mutually_exclusive_group()

parser.add_argument('-cr', '--code_resp', nargs='*',
                    type=allowed_cmds_check, metavar='',
                    help='The raw code command and the response to update the SQL3 database manually')
parser.add_argument('-sv', '--setval', nargs='?', type=setval_check, metavar='',
                     help='The value to set for the dryer compartment, i.e. time;20 or temp;50')
parser.add_argument('-vd', '--video', nargs='*', metavar='',
                    help='Set two parameters to start a video recording, (time, workflow name)')

args = parser.parse_args()


def set_url_endpoint(endpoint, request_type):
    if ping('raspberrypi.local'):
        hostnm = 'raspberrypi.local' #the rpi seen from mac osx
    elif ping('spencerrpi.local'):
        hostnm = 'spencerrpi.local' #other rpi for testing
    else:
        hostnm = '192.168.1.212' #the rpi seen from the hamilton pc, since using static ip
    url = f'http://{hostnm}:5000/tp_ser_wbsrv/{endpoint}'
    if request_type == "get":
        response = requests.get(url=url, timeout=12)
    elif request_type == "put":
        if args.video:
            data = dict(
                time=args.video[0],
                wrkflow_name=args.video[1]
            )
        elif endpoint.startswith('update'):
            data = dict(
                setval=args.setval,
                code_cmd=args.code_resp[0],
                response=args.code_resp[1]
            )
        elif 'set_dt' in endpoint:
            data = dict(
                setval=args.setval
                )
        else:
            data = ''
        # print(data)
        response = requests.put(url=url, data=data, timeout=12)
    return response


if __name__ == "__main__":
    res = set_url_endpoint(args.endpoint, args.request_type)
    # print(f'setval: {args.setval}, endpoint: {args.endpoint}, type: {args.request_type}')
    # print(res.url)
    if res.status_code >= 200 and res.status_code < 300:
        print('OK')
    else:
        print('BAD')
    output = res.json()
    output = output['response']
    # output['status_code'] = res.status_code
    # output['reason'] = res.reason
    pprint(output)

