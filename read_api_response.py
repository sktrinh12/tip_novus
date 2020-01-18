import requests
from rest_API import print_output

url = 'http://raspberrypi.local:5000/'

params = dict(
    data='test'
)

def split_resp(str_response):
    try:
        sub_response = str_response.split(',')[2]
    except IndexError as e:
        sub_response = ""
    return sub_response

def check_sr_char(sub_response):
    if sub_response == '1' or sub_response == '@':
        return True
    return False


if __name__ == "__main__":
    resp = requests.get(url=url, params=params)
    data = resp.json()
    sub_response_str = data[''].split(',')[2]

