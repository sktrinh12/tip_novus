from tipnovus_class_api import *
import time
from logging_decor import *

#tp = tipnovus('connect')
##print(tp.code_command)
##print(tp.encode_str_cmd)
#tps = tpserial().connect
#tp_ack = tipnovus('ack2')
##print(tp_ack.encode_str_cmd)
#tps.write_cmd(tp.encode_str_cmd)
#time.sleep(1)
#tps.write_cmd(tp_ack.encode_str_cmd)
##print(tps.is_connected)
#print(tps.read_resp)
#tps.disconnect

for k,v in send_cmd_dict.items():
    print(f'{k} - {v}')

print([k for k,v in send_cmd_dict.items() if v[0] == '01,TI,WA,WS,#'])
