from flask import Flask, request
from marshmallow import Schema, fields, pprint, post_load, ValidationError, validates
from flask_restful import Resource, Api, abort
from rest_sql3_class import *
from tipnovus_class_api import *
import os
from logging_decor import *
from ack_funcs import *
import re

app = Flask(__name__)
api = Api(app)
db_filepath = os.path.join(app.instance_path.replace('instance',''), 'db', 'tp_rest.db')
tp_ser = None

#{{{ FUNCTIONS

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
    print(output)
    handle_logs(output)
    return [tp.code_command, str_response]

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
                    print_output(f'~{cmd.buffer_wait_time - i} secs left')
                    logger.debug(f'time_remaining: {cmd.buffer_wait_time - i} secs')
        else:
            sleep(cmd.buffer_wait_time)
    str_response = tp_ser.read_resp
    spr = split_resp(str_response) #returns the sub-string response
    if not spr:
        print_output(f"No response string to parse from the ping cmd: {cmd_}")
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
    return [status_code_dict, str_response]


def connect_tp():
    global tp_ser
    tp_ser = tpserial().connect
    tp = tipnovus('connect')
    tp_ser.write_cmd(tp.encode_str_cmd)
    sleep(tp.buffer_wait_time)
    str_response = tp_ser.read_resp
    print(str_response)
    if str_response == tp.code_command:
        print_output(f"resp: {str_response} (SUCCESS)")
    output = f'func: {connect_tp.__name__}', f'sent: {tp.code_command}', f'resp: {str_response}'
    print(output)
    handle_logs(output)
    return [tp.code_command, str_response]

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
    print(output)
    handle_logs(output)
    return [tp_con.code_command, tp_ack.code_command, str_response]

def update_data(current_ts, cmd, resp):
    with tpdb(db_filepath) as db:
        db.execute("DELETE FROM CMDRESPONSE")
        db.execute(f"INSERT INTO CMDRESPONSE VALUES ('{current_ts}', '{cmd}', '{resp}')")
        handle_logs(f'ts: {current_ts}', f'sent: {cmd}', f'resp: {resp}')
        return {'timestamp' : current_ts , 'cmd' : cmd, 'response' : resp}

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


#{{{ TPSerSchema class
class tp_ser_check_setcmd_schema(Schema):
    cmd_ = fields.String(required = True)

    @validates('cmd_')
    def validate_cmd_(self, cmd_):
        if cmd_ not in ['set_dtime', 'set_dtemp']:
            msg = 'Must be a set command'
            raise ValidationError(msg)
            handle_logs(('error', msg))


class tp_ser_cmd_schema(Schema):
    cmd = fields.String(required = True)
    resp = fields.String(required = True)
    code_cmd = fields.String(required = True)
    setcmd = fields.String()
    status = fields.String()
    interp = fields.String()

    @validates('cmd')
    def validate_cmd(self, cmd):
        if cmd not in send_cmd_dict.keys():
            msg = f"Invalid command string - '{cmd}'"
            raise ValidationError(msg)
            handle_logs(('error', msg))

    @validates('code_cmd')
    def validate_code_cmd(self, code_cmd):
        if code_cmd not in [v[0] for v in send_cmd_dict.values()]:
            msg = f"Invalid code command string - '{code_cmd}'"
            raise ValidationError(msg)
            handle_logs(('error', msg))

    @validates('setcmd')
    def validate_setcmd(self, setcmd):
        if ';' in setcmd:
            typeof, value = setcmd.split(';')
            if typeof == 'time':
                if not value.isdigit():
                    msg = f'Incorrect value to set time parameter - {setcmd}'
                    raise ValidationError(msg)
                    handle_logs(('error', msg))
                if int(value) < 1 or int(value) > 100:
                    msg = f'Incorrect range for setting time; >1 and <100 - {setcmd}'
                    raise ValidationError(msg)
                    handle_logs(f('error', msg))
            elif typeof == 'temp':
                if not value.isdigit():
                    msg = f'Incorrect value to set temp parameter - {setcmd}'
                    raise ValidationError(msg)
                    handle_logs(('error', msg))
                if int(value) < 20 or int(value) > 70:
                    msg = f'Incorrect range for setting temperature; >20 and <70 - {setcmd}'
                    raise ValidationError(msg)
                    handle_logs(('error', msg))
            else:
                msg = f"Invalid command string; can only set 'temp' or 'time' - {setcmd}"
                raise ValidationError(msg)
                handle_logs(('error', msg))
        else:
            msg = f'Incorrect format for setting parameter - {setcmd}'
            raise ValidationError(msg)
            handle_logs(('error', msg))

    @validates('resp')
    def validate_resp(self, resp):
        if resp not in [a[0] for a in send_cmd_dict.values()]:
            # if not a dryer time remaining resp or check_sensor response
            if not re.search('01,ACK,\d{1,4},#', resp) or not re.search('[01]{7}',resp):
                msg = f'Invalid response string - {resp}'
                handle_logs(('error', msg))
                raise ValidationError(msg)
#}}}

tpcmd_schema = tp_ser_cmd_schema()

#{{{ TPSerWebServ class
class tp_wbsrv_upd(Resource):
    def put(self, cmd):
        current_ts = datetime.now().strftime('%G-%b-%d %H:%M:%S')
        input_cmd_dict = {'cmd' : cmd, 'resp' : request.form['resp']}
        schema_check = False
        if request.form.get('setcmd', False):
            tpsetcmd_schema = tp_ser_check_setcmd_schema()
            try:
                tpsetcmd_schema.load({'cmd_' : cmd})
                validate_val(cmd, request.form['setcmd'])
                input_cmd_dict['setcmd'] = request.form['setcmd']
                schema_check = True
            except ValidationError as err:
                pprint(err.messages)
                output = f'func: {self.__class__.__name__}_{self.put.__name__}', f"error: {err.messages}"
                handle_logs(output)
        else:
            try: #to load the cmd using the marshmallow schema defined above
                tpcmd_schema.load(input_cmd_dict)
                schema_check = True
            except ValidationError as err:
                pprint(err.messages)
                pprint(f'valid data: {err.valid_data}')
                output = f'func: {self.__class__.__name__}_{self.put.__name__}', f"error: {err.messages}"
                handle_logs(output)
        if schema_check:
            if len(input_cmd_dict.keys()) > 2:
                cmd = input_cmd_dict['setcmd']
            change = update_data(current_ts, cmd, input_cmd_dict['resp'])
            output = f'func: {self.__class__.__name__}_{self.put.__name__}', f'ts: {current_ts}',f'sent: {cmd}', f"resp: {input_cmd_dict['resp']}"
            handle_logs(output)
            return change, 201
        else:
            abort_if_invalid(cmd)


class tp_wbsrv_resp(Resource):
    def get(self):
        with tpdb(db_filepath) as db:
            res = db.queryone("SELECT response FROM CMDRESPONSE")
            output = f'func: {self.__class__.__name__}_{self.get.__name__}', f"resp: {res}"
            handle_logs(output)
            return  {'response' : res}


def ref_fx_cmd_proc(cmd, fx):
    data, response = fx(cmd) #ack or send, sent is the code cmd and cmd is the human readable cmd
    input_cmd_dict = {'code_cmd' : '', 'cmd' : cmd, 'resp' : response}
    #interp = 'interpretation:'
    if isinstance(data, dict):
        sent = data['ack']
        if len(data.keys()) > 2: #washer status code response 3-4 digits with interpretation
            input_cmd_dict['interp'] = data['interp']
            input_cmd_dict['status'] = data['status']
        elif len(data.keys()) == 2: #cmds wo interpretation
            input_cmd_dict['interp'] = data['interp']
#            for i in range(1,len(data.keys())):
#                input_cmd_dict[f'status_{i}'] = data[f'cd{i}']
#                interp += f' {data[f"cd{i}"]}'
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
        input_cmd_dict['resp'] = response
        handle_logs(output)
    return schema_check, input_cmd_dict

class tp_ser_wbsrv(Resource):
    def put(self, cmd):
        schema_check, data_dict = ref_fx_cmd_proc(cmd, send_cmd)
        if schema_check:
            #then acknowledge
            schema_check, data_dict = ref_fx_cmd_proc(cmd, ack_cmd)
            if schema_check and data_dict['resp']:
                return data_dict, 201
            else:
                return data_dict, 502
        else:
            abort_if_invalid(cmd)


class tp_ser_wbsrv_con(Resource):
    def get(self):
        s, r = connect_tp()
        output = f'func: {self.__class__.__name__}_{self.get.__name__}', f'sent: {s}', f"resp: {r}"
        handle_logs(output)
        return {'sent' : s, 'response' : r}


class tp_ser_wbsrv_discon(Resource):
    def get(self):
        s, s2, r = disconnect_tp()
        output = f'func: {self.__class__.__name__}_{self.get.__name__}', f'sent: {s} {s2}', f"resp: {r}"
        handle_logs(output)
        return {'sent' : f'{s} {s2}', 'response' : r}

#}}}

class tp_ser_wbsrv_cmds(Resource):
    def get(self):
        return send_cmd_dict


api.add_resource(tp_ser_wbsrv_con, '/tp_ser_wbsrv/connect')
api.add_resource(tp_ser_wbsrv_discon, '/tp_ser_wbsrv/disconnect')
api.add_resource(tp_wbsrv_resp, '/tp_ser_wbsrv/response')
api.add_resource(tp_wbsrv_upd, '/tp_ser_wbsrv/update/<string:cmd>') # change/update the command and/or repsonse string individually
api.add_resource(tp_ser_wbsrv, '/tp_ser_wbsrv/<string:cmd>') # issue commands to tp
api.add_resource(tp_ser_wbsrv_cmds, '/tp_ser_wbsrv/cmds') #get list of valid commands

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
