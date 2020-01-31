import sys
import serial
from logging_decor import *
from time import sleep
import re

@logit(tipnovus_logger)
def handle_logs(*args):
    print(*args)

#{{{ FORMAT COMMANDS 
class FC:
    def __init__(self, tp_unit, part_of_cmd_1, part_of_cmd_2=''):
        self.tp_unit = tp_unit
        self.part_of_cmd_1 = part_of_cmd_1
        self.part_of_cmd_2 = part_of_cmd_2

    @property
    def run_cmds(self):
        return f"0{self.tp_unit},TI,{self.part_of_cmd_1},{self.part_of_cmd_2},#"

    @property
    def util_cmds(self):
        if self.part_of_cmd_2 == '':
            return f"0{self.tp_unit},{self.part_of_cmd_1},#"
        else:
            return f"0{self.tp_unit},{self.part_of_cmd_1},#"

    def setparam(self, setvar):
        self.setvar = setvar
        return f"0{self.tp_unit},TI,{self.part_of_cmd_1},{self.part_of_cmd_2},{self.setvar}#"

    @staticmethod
    def to_secs(mins):
        return mins*60
#}}}

#{{{ SEND COMMAND DICTIONARY
TP = '1'
WA = 'WA'
DR = 'DR'
send_cmd_dict = {
    #key = command name, val1 = ascii command, val2 = time delay
    'connect' : [FC(TP, '@').util_cmds, FC.to_secs(0.016)],
    'ack' : [FC(TP, 'ACK,1').util_cmds, FC.to_secs(0.016)],
    'nak' : [FC(TP, 'NAK,@').util_cmds, FC.to_secs(0.016)],
    'opendoor_washer' : [FC(TP, WA, 'OD').run_cmds, FC.to_secs(0.04)],
    'closedoor_washer' : [FC(TP, WA, 'CD').run_cmds, FC.to_secs(0.04)],
    'opendoor_dryer' : [FC(TP, DR, 'OD').run_cmds, FC.to_secs(0.04)],
    'closedoor_dryer' : [FC(TP, DR, 'CD').run_cmds, FC.to_secs(0.04)],
    'start_dryer' : [FC(TP, DR, 'SD').run_cmds, FC.to_secs(0.05)],
    'custom2_proc' : [FC(TP, WA, 'S2').run_cmds, FC.to_secs(0.05)],
    'self_clean' : [FC(TP, WA, 'CL').run_cmds, FC.to_secs(0.32)],
    'check_sensor' : [FC(TP, WA, 'SC').run_cmds, FC.to_secs(1.01)],
    'waste_drain' : [FC(TP, WA, 'WD').run_cmds, FC.to_secs(0.035)],
    'dply_wash' : [FC(TP, WA, 'WS').run_cmds, FC.to_secs(0.018)],
    'dply_dryer' : [FC(TP, DR, 'DS').run_cmds, FC.to_secs(0.018)],
    'abort_dryer' : [FC(TP, DR, 'AD').run_cmds, FC.to_secs(0.018)],
    'abort_wash' : [FC(TP, DR, 'AW').run_cmds, FC.to_secs(0.018)],
    'get_dtemp' : [FC(TP, DR, 'CT').run_cmds, FC.to_secs(0.018)],
    'primeA' : [FC(TP, WA, 'PA').run_cmds, FC.to_secs(0.04)],
    'primeDI' : [FC(TP, WA, 'PD').run_cmds, FC.to_secs(0.04)],
    'set_dtime' : [FC(TP, DR, 'TM').setparam(10), FC.to_secs(0.02)],
    'set_dtemp' : [FC(TP, DR, 'MT').setparam(50), FC.to_secs(0.02)],
    'discon_resp' : [FC(TP, 'ACK,@').util_cmds, FC.to_secs(0.016)],
    'ack2' : [FC(TP, 'ACK').util_cmds, FC.to_secs(0.016)],
    'ack3' : [FC(TP, 'ACK,00').util_cmds, FC.to_secs(0.016)],
    'un_op' : [FC(TP, 'ACK,0').util_cmds, FC.to_secs(0.016)]
        }
#}}}


class tipnovus:
    def __init__(self, str_command):
        def check_setcmd(str_cmd):
            if re.search('set_dt.*\d{1,3}$', str_cmd):
                return True
            else:
                return False
        self.check = check_setcmd(str_command)
        if str_command not in send_cmd_dict.keys():
            if not self.check:
                raise ValueError('that command does not exist!')
            else:
                self.str_command = str_command[:9]
                self.setval = str_command[10:]
                self.buffer_wait_time = send_cmd_dict[self.str_command][1]
        else:
            self.str_command = str_command
            self.buffer_wait_time = send_cmd_dict[str_command][1]

    @property
    def word_command(self):
        if self.check:
            return f'{self.str_command};{self.setval}'
        else:
            return self.str_command

    @word_command.setter
    def word_commmand(self, command):
        self.str_command = command

    @property
    def code_command(self):
        if self.check:
            return f'{send_cmd_dict[self.str_command][0][:-3]}{self.setval}#'
        else:
            return send_cmd_dict[self.str_command][0]

    @property
    def encode_str_cmd(self):
        if self.check:
            return f'{send_cmd_dict[self.str_command][0][:-3]}{self.setval}#'.encode()
        else:
            return send_cmd_dict[self.str_command][0].encode()


class tpserial:
    def __init__(self, port):
        self._ser = None
        self._baudrate = 115200
        self._port = port
        self._timeout = 10

    @property
    def connect(self):
        try:
            self._ser = serial.Serial(port = self._port, baudrate = self._baudrate, timeout = self._timeout)
            self._ser.reset_output_buffer
            self._ser.reset_input_buffer
            handle_logs(f"Connected to TipNovus! ({self._port})")
            return self
        except serial.SerialException as e:
            handle_logs(f"Error occured during serial connection - {e}")
            sys.exit(1)

    @property
    def disconnect(self):
        if self._ser.isOpen():
            self._ser.close()
            handle_logs(f'Disconnecting from serial port {self._port}!')

    @property
    def is_connected(self):
        try:
            return self._ser.isOpen()
        except:
            return False

    def write_cmd(self, byte_command):
        self.byte_command = byte_command
        try:
            self._ser.write(byte_command)
            tipnovus_logger.debug(f'Sent {byte_command} to serial device')
        except Exception as e:
            handle_logs(f'Serial connection errored whilst sending {byte_command}: {e}')

    @property
    def read_resp(self):
        _response = self._ser.read(1)
        while True:
            n_ = self._ser.in_waiting
            if not n_:
                break
            else:
                sleep(0.1)
                _response += self._ser.read(n_)
        tipnovus_logger.debug(f'Read {_response.decode()} from serial device')
        return _response.decode()

    def __enter__(self):
        try:
            if self._ser == None:
                self._ser = serial.Serial(port = self._port, baudrate = self._baudrate, timeout = self._timeout)
                handle_logs(f'Connected to serial port {self._port}!')
            else:
                if self._ser.isOpen():
                    self._ser.close()
                    handle_logs('Disconnecting...')
                else:
                    self._ser.open()
                    handle_logs(f'Connected to serial port {self._port}!')
            return self._ser
        except serial.SerialException as e:
            handle_logs(f'Error occured: {e}')
            sys.exit(1)

    def __exit__(self, exc_type, exc_val, traceback):
        self._ser.close()

# tip_clean_tasks = tipnovus('closedoor_dryer')
# tip_clean_tasks.buffer_wait_time
# tip_clean_tasks.encode_str_cmd
# tip_clean_tasks.word_command
# tip_clean_tasks.code_command
