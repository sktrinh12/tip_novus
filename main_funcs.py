from flask_restful import abort
from tipnovus_class_api import *
from ack_funcs import *
from rest_sql3_class import *
from tipnovus_class_api import *

#{{{ MAIN FUNCTIONS

@logit(logger)
def handle_logs(*args):
    return

def send_cmd(cmd):
    tp = tipnovus(cmd)
    tp_ser.write_cmd(tp.encode_str_cmd)
    sleep(0.1)
    str_response = tp_ser.read_resp
    if str_response == tp.code_command:
        print_output(f"resp: {str_response} (SUCCESS)")
    output = f'func: {send_cmd.__name__}', f'sent: {tp.code_command}', f'resp: {str_response}'
    #print(output)
    handle_logs(output)
    return tp.code_command, str_response

def ack_cmd(cmd_=None):
    if cmd_:
        cmd = tipnovus(cmd_)
        status_code_dict = {'ack' : ''}
    ack = tipnovus('ack')
    tp_ser.write_cmd(ack.encode_str_cmd)
    if cmd_:
        if cmd.buffer_wait_time > 7:
            for i in range(round(cmd.buffer_wait_time)):
                print_output('*')
                sleep(1)
                if i % 8 == 0:
                    output = f'~{cmd.buffer_wait_time - i} secs left'
                    print_output(output)
                    logger.debug(output)
        else:
            sleep(cmd.buffer_wait_time)
    str_response = tp_ser.read_resp
    spr = split_resp(str_response) #returns the sub-string response
    if 'ER' in str_response:
        cd1, cd2, msg1, msg2 = error_msg_handle(spr)
        status_code_dict['status'] = f'{cd1}{cd2} {msg1}{msg2}'
        status_code_dict['interp'] = 'critical error during run'
    if not spr:
        print_output(('error', f"No response string to parse from the ping cmd: {cmd_}"))
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
        if data:
            status_code_dict['status'] = data
            status_code_dict['interp'] = 'sensor(s) are faulty!'
        else:
            status_code_dict['interp'] = 'sensors passed!'
    return status_code_dict, str_response


def connect_tp():
    global tp_ser
    tp_ser = tpserial("/dev/ttyUSB0").connect
    tp = tipnovus('connect')
    tp_ser.write_cmd(tp.encode_str_cmd)
    sleep(tp.buffer_wait_time)
    str_response = tp_ser.read_resp
    # print(str_response)
    if str_response == tp.code_command:
        print_output(f"resp: {str_response} (SUCCESS)")
    output = f'func: {connect_tp.__name__}', f'sent: {tp.code_command}', f'resp: {str_response}'
    # print(output)
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
    # print(output)
    handle_logs(output)
    return tp_con.code_command, tp_ack.code_command, str_response
#}}}


#{{{ FUNCTIONS RELATED TO API MECHANISM
def update_data(current_ts, cmd, resp):
    with tpdb(db_filepath) as db:
        db.execute("DELETE FROM CMDRESPONSE")
        db.execute(f"INSERT INTO CMDRESPONSE VALUES ('{current_ts}', '{cmd}', '{resp}')")
        handle_logs(f'ts: {current_ts}', f'sent: {cmd}', f'resp: {resp}')
        return {'timestamp' : current_ts , 'cmd' : cmd, 'response' : resp}


def ref_fx_cmd_proc(cmd, fx):
    data, response = fx(cmd) #ack or send, sent is the code cmd and cmd is the human readable cmd
    input_cmd_dict = {'code_cmd' : '', 'cmd' : cmd, 'resp' : response}
    if isinstance(data, dict):
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
    try: #to load the cmd using the marshmallow schema defined above
        tpcmd_schema.load(input_cmd_dict)
        schema_check = True
    except ValidationError as err:
        pprint(err.messages)
        pprint(err.valid_data)
        handle_logs(err.messages)

    if schema_check:
        with tpdb(db_filepath) as db:
            db.execute("DELETE FROM CMDRESPONSE")
            db.execute(f"INSERT INTO CMDRESPONSE VALUES ('{current_ts}', '{sent}', '{response}')")
        output = f'func: {ref_fx_cmd_proc.__name__}', f'sent: {cmd}', f'code_cmd: {sent}' ,f"resp: {response}"
        if 'interp' in input_cmd_dict.keys():
            output + (f'interpreatation: {input_cmd_dict["interp"]}',)
        handle_logs(output)
        input_cmd_dict['resp'] = response
    return schema_check, input_cmd_dict
#}}}


#{{{ SCHEMA RELATED FUNCTIONS
def abort_if_invalid(input_str):
    msg = "The command, '{}', its reponse or the set parameters were not in a valid format".format(input_str)
    abort(404, error=msg)
    handle_logs(('error', msg))

def validate_val(cmd, val):
    if cmd == 'set_dtime':
        if val[:4] != 'time':
            msg = 'The set parameter and cmd string do not match'
            raise ValidationError(msg)
            handle_logs(('error', msg))
    elif cmd == 'set_dtemp':
        if val[:4] != 'temp':
            msg = 'The set parameter and cmd string do not match'
            raise ValidationError(msg)
            handle_logs(('error', msg))
#}}}
