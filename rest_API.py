from flask import Flask, request
from marshmallow import Schema, fields, pprint, post_load, ValidationError, validates
from flask_restful import Resource, Api
from rest_sql3_class import *
from tipnovus_class_api import *
import datetime
import os

app = Flask(__name__)
api = Api(app)
db_filepath = os.path.join(app.instance_path.replace('instance',''), 'db', 'tp_rest.db')

#{{{ TALK TO TIPNOVUS
def send_cmd(cmd):
    tp_ser = tpserial()
    tp = tipnovus(cmd)
    tp_ser.write(tp.encode_str_cmd)
    sleep(tp.buffer_wait_time)
    str_response = tp_ser.read
    if str_response == tp.command:
        sys.stdout.write(str_response + "(SUCCESS)\n")
    return [tp.command, str_response]

def connect_tp():
    tp_ser = tpserial()
    tp = tipnovus('connect')
    tp_ser.reset_output_buffer
    tp_ser.reset_input_buffer
    tp_ser.write(tp.encode_str_cmd)
    sleep(tp.buffer_wait_time)
    str_response = tp_ser.read
    if str_response == tp.command:
        sys.stdout.write(str_response + "(SUCCESS)\n")
    return [tp.command, str_response]

def disconnect_tp():
    tp_ser = tpserial()
    tp_con = tipnovus('connect')
    tp_ack = tipnovus('ack')
    tp_ser.write(tp_con.encode_str_cmd)
    tp_ser.write(tp_ack.encode_str_cmd)
    sleep(tp_con.buffer_wait_time)
    str_response = tp_ser.read
    if str_response == tp.command: # NOT THE RIGHT CONDITION (IT IS ANOTHER STRING)
        sys.stdout.write(str_response + "(SUCCESS)\n")
    return [tp_con.command, tp_ack.command, str_response]

#}}}


#{{{ TPSerSchema class
class TPSerSchema(Schema):
    @validates('cmd')
    def validate_cmd(self, cmd):
        if cmd not in send_cmd_dict.keys():
            raise ValidationError('Invalid command')

    cmd = fields.String(validate=validate_cmd)

#}}}

tpcmd_schema = TPSerSchema(many=True) # show many error msgs

#{{{ TPSerWebServ class
class tp_wbsrv_upd(Resource):
    def put(self, cmd):
        current_ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        response = '#,01,@,1'
        input_cmd_dict = {'cmd' : cmd}
        try: #to load the cmd using the marshmallow schema defined above
            tpcmd_schema.load(input_cmd_dict)
        except ValidationError as err:
            pprint(err.messages)
        with tpdb(db_filepath) as db:
            db.execute("DELETE FROM CMDRESPONSE")
            db.execute(f"INSERT INTO CMDRESPONSE VALUES ('{current_ts}', '{cmd}', '{response}')")
        change = {'timestamp' : current_ts , 'cmd' : cmd, 'response' : response}
        return change, 201

class tp_wbsrv_resp(Resource):
    def get(self):
        with tpdb(db_filepath) as db:
            res = db.queryone("SELECT response FROM CMDRESPONSE")
            return  {'response' : res}

class tp_ser_wbsrv(Resource):
    def put(self, cmd):
        # cmd = request.form['cmd']
        input_cmd_dict = {'cmd' : cmd}
        try: #to load the cmd using the marshmallow schema defined above
            tpcmd_schema.load(input_cmd_dict)
        except ValidationError as err:
            pprint(err.messages)
        current_ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sent, response = send_cmd(cmd)

        #response = '01,ACK,1,#'
        with tpdb(db_filepath) as db:
            db.execute("DELETE FROM CMDRESPONSE")
            db.execute(f"INSERT INTO CMDRESPONSE VALUES ('{current_ts}', '{cmd}', '{response}')")
        change = {'timestamp' : current_ts , 'cmd' : cmd, 'response' : response}
        return change, 201

    def connect(self):
        s, r = connect_tp()
        return {'sent_cmd' : s, 'response' : r}

    def disconnect(self):
        s, s2, r = disconnect_tp()
        return {'sent_cmd_1' : s, 'sent_cmd_2' : s2, 'response' : r}


#}}}

def decr_logging():
    def inner_decr_logging():
        logging.debug(f"sent: {tp.command}")
        logging.info(f"response: {str_response}")
    return inner_decr_logging


class tp_ser_wbsrv_cmds(Resource):
    def get(self):
        return send_cmd_dict


api.add_resource(tp_wbsrv_resp, '/tp_wbsrv/response')
api.add_resource(tp_wbsrv_upd, '/tp_wbsrv/<string:cmd>')
api.add_resource(tp_ser_wbsrv, '/tp_ser_wbsrv/<string:cmd>')
api.add_resource(tp_ser_wbsrv_cmds, '/tp_ser_wbsrv/')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
