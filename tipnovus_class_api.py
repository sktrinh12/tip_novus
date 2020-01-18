import sys
import serial
#{{{ FORMAT COMMANDS 
class FC:
    def __init__(self, tp_unit, part_of_cmd_1, part_of_cmd_2=''):
        self.tp_unit = tp_unit
        self.part_of_cmd_1 = part_of_cmd_1
        self.part_of_cmd_2 = part_of_cmd_2

    @property
    def run_cmds(self):
        return f"#,0{self.tp_unit},TI,{self.part_of_cmd_1},{self.part_of_cmd_2},#"

    @property
    def util_cmds(self):
        if self.part_of_cmd_2 == '':
            return f"#,0{self.tp_unit},{self.part_of_cmd_1},#"
        else:
            return f"#,0{self.tp_unit},{self.part_of_cmd_1},#"

    def setparam(self, setvar):
        self.setvar = setvar
        return f"#,0{self.tp_unit},TI,{self.part_of_cmd_1},{self.part_of_cmd_2},{self.setvar}#"

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
    'connect' : [FC(TP, '@').util_cmds, FC.to_secs(0.1)],
    'ack' : [FC(TP, 'ACK,1').util_cmds, FC.to_secs(0.07)],
    'nak' : [FC(TP, 'NAK,@').util_cmds, FC.to_secs(0.07)],
    'opendoor_washer' : [FC(TP, WA, 'OD').run_cmds, FC.to_secs(0.2)],
    'closedoor_washer' : [FC(TP, WA, 'CD').run_cmds, FC.to_secs(0.2)],
    'opendoor_dryer' : [FC(TP, DR, 'OD').run_cmds, FC.to_secs(0.2)],
    'closedoor_dryer' : [FC(TP, DR, 'CD').run_cmds, FC.to_secs(0.2)],
    'start_dryer' : [FC(TP, DR, 'SD').run_cmds, FC.to_secs(0.4)],
    'custom2_proc' : [FC(TP, WA, 'S2').run_cmds, FC.to_secs(0.4)],
    'self_clean' : [FC(TP, WA, 'CL').run_cmds, FC.to_secs(0.4)],
    'check_sensor' : [FC(TP, WA, 'SC').run_cmds, FC.to_secs(1.2)],
    'waste_drain' : [FC(TP, WA, 'WD').run_cmds, FC.to_secs(0.2)],
    'dply_wash' : [FC(TP, WA, 'WS').run_cmds, FC.to_secs(0.12)],
    'dply_dryer' : [FC(TP, DR, 'DS').run_cmds, FC.to_secs(0.12)],
    'abort_dryer' : [FC(TP, DR, 'AD').run_cmds, FC.to_secs(0.1)],
    'abort_wash' : [FC(TP, DR, 'AW').run_cmds, FC.to_secs(0.1)],
    'get_dtemp' : [FC(TP, DR, 'CT').run_cmds, FC.to_secs(0.1)],
    'primeA' : [FC(TP, WA, 'PA').run_cmds, FC.to_secs(0.2)],
    'primeDI' : [FC(TP, WA, 'PD').run_cmds, FC.to_secs(0.2)],
    'set_dtime' : [FC(TP, DR, 'TM').setparam(10), FC.to_secs(0.12)],
    'set_dtemp' : [FC(TP, DR, 'MT').setparam(50), FC.to_secs(0.12)],
    'discon_resp' : [FC(TP, 'ACK,@').util_cmds, FC.to_secs(0.07)],
    'ack2' : [FC(TP, 'ACK').util_cmds, FC.to_secs(0.07)],
    'un_op' : [FC(TP, 'ACK,0').util_cmds, FC.to_secs(0.07)]
        }
#}}}


class tipnovus:
    def __init__(self, str_command):
        if str_command not in send_cmd_dict.keys():
            raise ValueError('that command does not exist!')
        else:
            self.str_command = str_command
            self.buffer_wait_time = send_cmd_dict[str_command][1]

    @property
    def command(self):
        return self.str_command

    @command.setter
    def commmand(self, command):
        self.str_command = command

    @property
    def encode_str_cmd(self):
        return send_cmd_dict[self.str_command][0].encode()


class tpserial:
    def __init__(self):
        pass

    @property
    def init(self):
        self._ser = None
        self._baudrate = 115200
        self._port = "COM17"
        self._timeout = 10
        return self

    @property
    def connect(self):
        try:
            self._ser = serial.Serial(port = self._port, baudrate = self._baudrate, timeout = self._timeout)
            return self._ser
        except serial.SerialException as e:
            sys.stdout.write(f"Error occured during serial connection - {e}")
            logging.info(f"Error occured during serial connection - {e}")
            sys.exit(1)

    @property
    def disconnect(self):
        if self._ser.isOpen():
            self._ser.close()
            sys.stdout.write(f'Disconnecting from serial port {self._port}!')

    @property
    def is_connected(self):
        try:
            return self._ser.isOpen()
        except:
            return False

    def write(self, byte_command):
        self.byte_command = byte_command
        try:
            self._ser.write(byte_command)
        except Exception as e:
            sys.stdout.write(f'Serial connection errored whilst sending {byte_command}: {e}')

    @property
    def read(self):
        _response = self._ser.read(1)
        while True:
            _response = self._ser.in_waiting
            if not _response:
                break
            else:
                _response += self._ser.read()
        return _response.decode()

    def __enter__(self):
        try:
            if self._ser == None:
                self._ser = serial.Serial(port = self._port, baudrate = self._baudrate, timeout = self._timeout)
                sys.stdout.write(f'Connected to serial port {self._port}!')
            else:
                if self._ser.isOpen():
                    self._ser.close()
                    sys.stdout.write('Disconnecting...')
                else:
                    self._ser.open()
                    sys.stdout.write(f'Connected to serial port {self._port}!')
            return self._ser
        except serial.SerialException as e:
            sys.stdout.write(f'Error occured: {e}')
            sys.exit(1)

    def __exit__(self, exc_type, exc_val, traceback):
        self._ser.close()

# tip_clean_tasks = tipnovus('closedoor_dryer')
# tip_clean_tasks.buffer_wait_time
# tip_clean_tasks.encode_str_cmd
# tip_clean_tasks.command
