import re
from marshmallow import Schema, fields, pprint, ValidationError, validates#, post_load
from main_funcs import handle_logs

#{{{ TPSerSetCmdSchema class
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
