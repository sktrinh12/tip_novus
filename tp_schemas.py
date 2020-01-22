from marshmallow import Schema, fields, pprint, ValidationError, validates#, post_load
from main_funcs import handle_logs
from tipnovus_class_api import send_cmd_dict
import re

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
    setval = fields.String()
    status = fields.String()
    interp = fields.String()

    @validates('cmd')
    def validate_cmd(self, cmd):
        if cmd not in send_cmd_dict.keys():
            msg = f"fi:{__file__}_cls:{__class__}_fx:{__name__}:: Invalid command string -> '{cmd}'"
            raise ValidationError(msg)
            handle_logs(('error', msg))

    @validates('code_cmd')
    def validate_code_cmd(self, code_cmd):
        if code_cmd not in [v[0] for v in send_cmd_dict.values()]:
            re_match = '01,TI,DR,{},{}'
            time_m = '([1-9]|[1-9][0-9]|100)#'
            temp_m = '([2-6][0-9]|70)#'
            if not any(re.search(rgs, code_cmd) for rgs in [re_match.format('TM', time_m), re_match.format('MT', temp_m)]):
                msg = f"fi:{__file__}_cls:{__class__}_fx:{__name__}:: Invalid code command string -> '{code_cmd}'"
                raise ValidationError(msg)
                handle_logs(('error', msg))

    @validates('setval')
    def validate_setcmd(self, setval): # input would be like: 'time;8' or 'temp;24'
        if ';' in setval:
            typeof, val = setval.split(';')
            if typeof == 'time':
                if not val.isdigit():
                    msg = f'fi:{__file__}_cls:{__class__}_fx:{__name__}:: Incorrect value to set time parameter -> {val}'
                    raise ValidationError(msg)
                    handle_logs(('error', msg))
                if int(val) < 1 or int(val) > 100:
                    msg = f'fi:{__file__}_cls:{__class__}_fx:{__name__}:: Incorrect range for setting time; >1 and <100 -> {val}'
                    raise ValidationError(msg)
                    handle_logs(f('error', msg))
            elif typeof == 'temp':
                if not val.isdigit():
                    msg = f'fi:{__file__}_cls:{__class__}_fx:{__name__}:: Incorrect value to set temp parameter -> {val}'
                    raise ValidationError(msg)
                    handle_logs(('error', msg))
                if int(val) < 20 or int(val) > 70:
                    msg = f'fi:{__file__}_cls:{__class__}_fx:{__name__}:: Incorrect range for setting temperature; >20 and <70 -> {val}'
                    raise ValidationError(msg)
                    handle_logs(('error', msg))
            else:
                msg = f"fi:{__file__}_cls:{__class__}_fx:{__name__}:: Invalid command string; can only set 'temp' or 'time' -> {val}"
                raise ValidationError(msg)
                handle_logs(('error', msg))
        else:
            msg = f"fi:{__file__}_cls:{__class__}_fx:{__name__}:: Improper string format, requires ';' -> {setval}"
            raise ValidationError(msg)
            handle_logs(('error', msg))

    @validates('resp')
    def validate_resp(self, resp):
        if resp not in [a[0] for a in send_cmd_dict.values()]:
            # if not a dryer time remaining resp or check_sensor response
            if not re.search('01,ACK,\d{1,4},#', resp) and not re.search('[0|1]{7}',resp):
                msg = f'fi:{__file__}_cls:{__class__}_fx:{__name__}:: Invalid response string -> {resp}'
                handle_logs(('error', msg))
                raise ValidationError(msg)
#}}}

#{{{ SCHEMA RELATED FUNCTIONS
def validate_val(cmd, code_cmd, setval):
    typeof, val = setval.split(';')
    if cmd == 'set_dtime':
        if typeof != 'time':
            msg = f'The set parameter and cmd string do not accord with each other -> {setval} != {cmd}'
            handle_logs(('error', msg))
            raise ValidationError(msg)
        if code_cmd not in [a[0] for a in send_cmd_dict.values()]:
            if not re.search(f'(01,TI,DR,TM,{val}#)', code_cmd):
                msg = f'The setval and code_cmd string do not accord with each other -> {setval} & {code_cmd}'
                handle_logs(('error', msg))
                raise ValidationError(msg)
    elif cmd == 'set_dtemp':
        if typeof != 'temp':
            msg = f'The set parameter and cmd string do not accord with each other -> {setval} != {cmd}'
            handle_logs(('error', msg))
            raise ValidationError(msg)
        if code_cmd not in [a[0] for a in send_cmd_dict.values()]:
            if not re.search(f'(01,TI,DR,MT,{val}#)', code_cmd):
                msg = f'The setval and code_cmd string do not accord with each other -> {setval} & {code_cmd}'
                handle_logs(('error', msg))
                raise ValidationError(msg)
#}}}
