import requests
from socket import gethostname
from pprint import pprint
import argparse
from tipnovus_class_api import send_cmd_dict
import re

"""
    Script to interface with TipNovus instrument via the Hamilton Instinct V software. An API call can be made to the Flask web server on the raspberry pi (or other host) connected to the TipNovus instrument. Can be used as a CLI from terminal as well. The output is a simple 'OK' or 'BAD' based on the request status code, either 201 or 400.

"""

#for argparse endpoint choices
available_word_cmds = list(send_cmd_dict.keys())
available_word_cmds = available_word_cmds + \
                [f'update/{cmds}' for cmds in available_word_cmds] + \
                ['connect','disconnect','response', 'cmds', 'record_video']

available_code_cmds = [v[0] for v in send_cmd_dict.values()]
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
                    help='The raw code command and the response to update the SQL3 database')
parser.add_argument('-sv', '--setval', nargs='?', type=setval_check, metavar='',
                     help='The value to set for the dryer compartment, i.e. time;20 or temp;50')
parser.add_argument('-vd', '--video', nargs='*', metavar='',
                    help='Set three parameters to start a video recording, (on, time, workflow name)')

args = parser.parse_args()


def set_url_endpoint(endpoint, request_type):
    hostname = gethostname()
    if hostname.startswith('raspb'):
        hostname += '.local'
    url = f'http://{hostname}:5000/tp_ser_wbsrv/{endpoint}'
    if request_type == "get":
        response = requests.get(url=url)
    elif request_type == "put":
        if args.video:
            data = dict(
                trigger=args.video[0],
                time=args.video[1],
                wrkflow_name=args.video[2]
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
        response = requests.put(url=url, data=data)
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

