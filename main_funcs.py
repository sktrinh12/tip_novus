from flask_restful import abort
from tipnovus_class_api import *
from ack_funcs import *
from rest_sql3_class import *
from tipnovus_class_api import *
from marshmallow import ValidationError, pprint
from tp_schemas import tp_ser_cmd_schema, tp_ser_check_setcmd_schema, validate_val

tpcmd_schema = tp_ser_cmd_schema()
tp_ser = None
#{{{ MAIN FUNCTIONS


def send_cmd(cmd):
    tp = tipnovus(cmd)
    tp_ser.write_cmd(tp.encode_str_cmd)
    sleep(0.1)
    str_response = tp_ser.read_resp
    if str_response == tp.code_command:
        print_output(f"response: {str_response} (SUCCESS)")
    elif re.search('01,TI,DR,(TM|MT),\d{1,3}#', str_response): #substring up to the default value within the tipnovus cmd class
        print_output(f"response: {str_response} (SUCCESS)")
    output = f'func: {__name__}', f'sent: {tp.code_command}', f'response: {str_response}'
    handle_logs(output)
    return tp.code_command, str_response

def ack_cmd(cmd_):
    cmd = tipnovus(cmd_) #just to print out '*' for long delays
    status_code_dict = {'ack' : ''}
    ack = tipnovus('ack')
    tp_ser.write_cmd(ack.encode_str_cmd)
    if cmd.buffer_wait_time > 2:
        for i in range(round(cmd.buffer_wait_time)):
            print_output('*')
            sleep(1)
            if i % 8 == 0:
                output = f'~{cmd.buffer_wait_time - i} secs left'
                print_output(output)
                tipnovus_logger.debug(output)
    else:
        sleep(cmd.buffer_wait_time)
    str_response = tp_ser.read_resp
    spr = split_resp(str_response) #returns the sub-string response
    if 'ER' in str_response:
        cd1, cd2, msg1, msg2 = error_msg_handle(spr)
        handle_logs(('error', f"error code: {cd1}{cd2} {msg_1} {msg_2}"))
        status_code_dict['status'] = f'{cd1}{cd2} {msg1}{msg2}'
        status_code_dict['interp'] = 'critical error during run'
    if not spr:
        output = f"{__file__}_{__name__}: No response string to parse from the ping cmd: {cmd_}"
        handle_logs(('error', output))
        #print_output(output)
    else:
        status_code_dict['ack'] = ack.code_command
    if 'dply' in cmd_:
        data = dply_cmds(spr) #print out time remaining or current status or status codes
        if isinstance(data, tuple):
            status_code_dict['status'] = data[2]
            status_code_dict['interp'] = f'{data[0]} {data[1]}'
        else:
            if data == '00':
                interp_msg = 'washer not in operation'
            elif data == '0':
                interp_msg = 'dryer not in operation'
            else:
                interp_msg = f'{data} min remaining'
            #dryer remaining time
            status_code_dict['interp'] = interp_msg
    if cmd_ == "check_sensor":
        data = sensor_check(spr) #print out sensor numbers that are faulty
        if data and data != 'problem': #if there is a list of codes due to faulty sensor, then...
            status_code_dict['status'] = data
            status_code_dict['interp'] = 'sensor(s) are faulty!'
        elif data == 'problem':
            status_code_dict['interp'] = 'problem interpreting the response!'
        else:
            status_code_dict['interp'] = 'sensors passed!'
    return status_code_dict, str_response

def check_conn():
    res = tp_ser.is_connected
    print_output(f'is connected: {res}')
    output = f'{__file__}_{__name__}: check if connected = {res}'
    handle_logs(output)
    return res

def connect_tp():
    global tp_ser
    tp_ser = tpserial("/dev/ttyUSB0").connect
    tp = tipnovus('connect')
    tp_ser.write_cmd(tp.encode_str_cmd)
    sleep(tp.buffer_wait_time)
    str_response = tp_ser.read_resp
    if str_response == tp.code_command:
        print_output(f"resp: {str_response} (SUCCESS)")

    output = f'func: {connect_tp.__name__}', f'sent: {tp.code_command}', f'resp: {str_response}'
    handle_logs(output)
    return tp.code_command, str_response

def disconnect_tp():
    tp_con = tipnovus('connect')
    tp_ack = tipnovus('ack2')
    tp_ser.write_cmd(tp_con.encode_str_cmd)
    tp_ser.write_cmd(tp_ack.encode_str_cmd)
    sleep(tp_con.buffer_wait_time)
    str_response = tp_ser.read_resp
    if str_response == send_cmd_dict['connect'][0] + send_cmd_dict['discon_resp'][0] or \
        str_response == send_cmd_dict['discon_resp'][0]:
        print_output(f"resp: {str_response} (SUCCESS)")
    tp_ser.disconnect
    output = f'func: {disconnect_tp.__name__}', f'sent: {tp_con.code_command} {tp_ack.code_command}', f'resp: {str_response}'
    handle_logs(output)
    return tp_con.code_command, tp_ack.code_command, str_response
#}}}


#{{{ SCHEMA RELATED FUNCTIONS
def update_data(current_ts, cmd, code_cmd, resp):
    with tpdb(tp_db_filepath) as db:
        db.execute("DELETE FROM CMDRESPONSE")
        db.execute(f"INSERT INTO CMDRESPONSE VALUES ('{current_ts}', '{cmd}', '{code_cmd}', '{resp}')")
#        output = f'ts: {current_ts}', f'cmd: {cmd}', f'code_cmd: {code_cmd}', f'resp: {resp}'
#        handle_logs(output)
        return {'timestamp' : current_ts , 'cmd' : cmd, 'code_cmd' : code_cmd, 'response' : resp}


def ref_fx_cmd_proc(cmd, fx):
    setval_request = request.form.get('setval', False)
    input_cmd_dict = {'code_cmd' : '', 'cmd' : cmd, 'response' : ''} # initialise
    if setval_request and fx.__name__ == "send_cmd":
        tpsetcmd_schema = tp_ser_check_setcmd_schema() # checks if it is a set_d type cmd
        tpsetcmd_schema.load({'cmd_' : cmd})
        # temporarily fudge the resp/code_cmd to just check/validate the setval entry
        input_cmd_dict['code_cmd'] = input_cmd_dict['response'] = "01,ACK,#"
        input_cmd_dict['setval'] = setval_request
        cmd_wo_setval = cmd
        tpcmd_schema.load(input_cmd_dict) # actually only checking the setval
        cmd = f"{cmd};{setval_request.split(';')[1]}" #concatenate the cmd to update it with the setval
        input_cmd_dict['cmd'] = cmd #overwrite with the current human readable cmd string
    data, response = fx(cmd) #ack or send, sent is the code cmd and cmd is the human readable cmd
    input_cmd_dict['response'] = response
    if isinstance(data, dict): #an ack cmd returns a dict
        sent = data['ack']
        if len(data.keys()) > 2: #washer status code response 3-4 digits with interpretation
            input_cmd_dict['interp'] = data['interp']
            input_cmd_dict['status'] = data['status']
        elif len(data.keys()) == 2: #cmds that output only short responses, i.e. dryer time, check sensor
            input_cmd_dict['interp'] = data['interp']
    else:
        sent = data
    input_cmd_dict['code_cmd'] = sent
    current_ts = datetime.now().strftime('%G-%b-%d %H:%M:%S')
    schema_check = False
    try: #to load the cmd using the main marshmallow schema defined in tp_chema.py
        if setval_request and fx.__name__ == "send_cmd":
            #print(cmd_wo_setval, input_cmd_dict['code_cmd'], input_cmd_dict['setval'])
            validate_val(cmd_wo_setval, input_cmd_dict['code_cmd'], input_cmd_dict['setval']) #validate the setval and code_cmd
            print('validation of setval completed')
            input_cmd_dict['cmd'] = cmd_wo_setval #overwrite the current human readable cmd string to prepare loading into  validation schema (a default accepted value)
        tpcmd_schema.load(input_cmd_dict) # if setval; check second time with real data
        schema_check = True
    except ValidationError as err:
        pprint(err.messages)
        pprint(err.valid_data)
        #handle_logs(err.messages)

    if schema_check:
        with tpdb(tp_db_filepath) as db:
            db.execute("DELETE FROM CMDRESPONSE")
            db.execute(f"INSERT INTO CMDRESPONSE VALUES ('{current_ts}', '{cmd}', '{sent}', '{response}')")
        output = f'fi:{__file__}_fx:{ref_fx_cmd_proc.__name__}', f'cmd: {cmd}', f'code_cmd: {sent}' ,f"response: {response}"
        if 'interp' in input_cmd_dict.keys():
            output = output + (f'interpretation: {input_cmd_dict["interp"]}',)
        handle_logs(output)
        input_cmd_dict['response'] = response
        if fx.__name__ == "send_cmd":
            input_cmd_dict['cmd'] = cmd #overwrite the current human readable cmd string with ';[::digits::]
    return schema_check, input_cmd_dict

def abort_if_invalid(input_str_dict):
    msg = ' '
    # print(input_str_dict)
    for i,(k,v) in enumerate(input_str_dict.items()):
        msg += f'({k}:{v})'
    msg += f" - The response or the data parameters were not valid"
    abort(404, error=msg)
    handle_logs(('error', msg))
#}}}
