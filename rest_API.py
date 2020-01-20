from flask_restful import Resource, Api, abort
from main_funcs import *
from tp_schemas import *

api = Api(app)
tp_ser = None
tpcmd_schema = tp_ser_cmd_schema()

#{{{ TPSerWebServ class
class tp_wbsrv_upd(Resource):
    def put(self, cmd):
        current_ts = datetime.now().strftime('%G-%b-%d %H:%M:%S')
        input_cmd_dict = {'cmd' : cmd, \
                          'resp' : request.form['resp'], \
                          'code_cmd' : request.form['code_cmd']}
        schema_check = False
        if request.form.get('setval', False):
            tpsetcmd_schema = tp_ser_check_setcmd_schema()
            try:
                tpsetcmd_schema.load({'cmd_' : cmd})
                validate_val(cmd, input_cmd_dict['code_cmd'], request.form['setval'])
                input_cmd_dict['setval'] = request.form['setval']
                tpcmd_schema.load(input_cmd_dict) #load in main schema to check ranges of setcmd
                schema_check = True
            except ValidationError as err:
                pprint(err.messages)
                output = f'func: {self.__class__.__name__}_{self.put.__name__}', f"error: {err.messages}"
                handle_logs(output)
        else:
            if 'set_' in cmd:
                msg = "Required 'setval' argument missing"
                raise ValidationError(msg)
                handle_logs(msg)
            try: #to load the cmd using the marshmallow schema defined above
                tpcmd_schema.load(input_cmd_dict)
                schema_check = True
            except ValidationError as err:
                pprint(err.messages)
                pprint(f'valid data: {err.valid_data}')
                output = f'func: {self.__class__.__name__}_{self.put.__name__}', f"error: {err.messages}"
                handle_logs(output)
        if schema_check:
            if len(input_cmd_dict.keys()) > 3:
                cmd = cmd + input_cmd_dict['setval'].split(';')[1]
            change = update_data(current_ts, cmd, input_cmd_dict['code_cmd'], input_cmd_dict['resp'])
            output = f'func: {self.__class__.__name__}_{self.put.__name__}', f'ts: {current_ts}',f'sent: {cmd}', f"resp: {input_cmd_dict['resp']}"
            handle_logs(output)
            return change, 201
        else:
            abort_if_invalid(cmd)


class tp_wbsrv_resp(Resource):
    # get the response
    def get(self):
        with tpdb(db_filepath) as db:
            res = db.queryone("SELECT response FROM CMDRESPONSE")
            output = f'func: {self.__class__.__name__}_{self.get.__name__}', f"resp: {res}"
            handle_logs(output)
            return  {'response' : res}


class tp_ser_wbsrv(Resource):
    # issuing commands
    def put(self, cmd):
        schema_check, data_dict = ref_fx_cmd_proc(cmd, send_cmd) #send cmd is a function
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
    # connect to tip novus
    def get(self):
        s, r = connect_tp()
        output = f'func: {self.__class__.__name__}_{self.get.__name__}', f'sent: {s}', f"resp: {r}"
        handle_logs(output)
        return {'sent' : s, 'response' : r}


class tp_ser_wbsrv_discon(Resource):
    # disconnect from tip novus
    def get(self):
        s, s2, r = disconnect_tp()
        output = f'func: {self.__class__.__name__}_{self.get.__name__}', f'sent: {s} {s2}', f"resp: {r}"
        handle_logs(output)
        return {'sent' : f'{s} {s2}', 'response' : r}

#}}}

class tp_ser_wbsrv_cmds(Resource):
    # get list of available commands
    def get(self):
        return send_cmd_dict


api.add_resource(tp_ser_wbsrv_con, '/tp_ser_wbsrv/connect')
api.add_resource(tp_ser_wbsrv_discon, '/tp_ser_wbsrv/disconnect')
api.add_resource(tp_wbsrv_resp, '/tp_ser_wbsrv/response')
api.add_resource(tp_wbsrv_upd, '/tp_ser_wbsrv/update/<string:cmd>') # change/update the command andrepsonse string 
api.add_resource(tp_ser_wbsrv, '/tp_ser_wbsrv/<string:cmd>') # issue commands to tp
api.add_resource(tp_ser_wbsrv_cmds, '/tp_ser_wbsrv/cmds') #get list of valid commands

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
