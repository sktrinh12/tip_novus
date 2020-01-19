import requests
from socket import gethostname
from pprint import pprint
import argparse
from tipnovus_class_api import send_cmd_dict


"""
    Script to interface with TipNovus instrument via the Hamilton Instinct V software. An API call can be made to the Flask web server on the raspberry pi (or other host) connected to the TipNovus instrument. Can be used as a CLI from terminal as well. The output is a simple 'OK' or 'BAD' based on the request status code, either 201 or 400.

"""


#for argparse endpoint choices
available_word_cmds = list(send_cmd_dict.keys())
available_word_cmds = available_word_cmds + \
                [f'update/{cmds}' for cmds in available_word_cmds] + \
                ['connect','disconnect','response', 'cmds']

available_code_cmds = [v[0] for v in send_cmd_dict.values()]
description = '''
    Call the tipnovus API using a url with endpoint that corresponds to the flask-restful defined endpoint. Used to issue commands, receive responses, list the available commands, connect and disconnect from the tipnovus instrument.
              '''

parser = argparse.ArgumentParser(description=description)
parser.add_argument('-e', '--endpoint', type=str, default='cmds',
                    choices=available_word_cmds, metavar='', required=True,
                    help='Enter an endpoint for the api')
parser.add_argument('-t', '--request_type', type=str, required=True,
                    choices=['put', 'get'], metavar='',
                    help='What type of request? (get, put)')
group = parser.add_mutually_exclusive_group()
group.add_argument('-cr', '--code_resp', nargs=2,
                    choices=available_code_cmds, metavar='',
                    help='The raw code command and the response to update the SQL3 database')
args = parser.parse_args()

def set_url_endpoint(endpoint, request_type):
    hostname = gethostname()
    url = f'http://{hostname}:5000/tp_ser_wbsrv/{endpoint}'
    if request_type == "get":
        response = requests.get(url=url)
    elif request_type == "put":
        data = dict(
            code_cmd=args.code_resp[0],
            resp=args.code_resp[1]
        )
        response = requests.put(url=url, data=data)
    return response


if __name__ == "__main__":
    res = set_url_endpoint(args.endpoint, args.request_type)
    if res.status_code >= 200 and res.status_code < 300:
        print('OK')
    else:
        print('BAD')
    output = res.json()
    # output['status_code'] = res.status_code
    # output['reason'] = res.reason
    pprint(output)

