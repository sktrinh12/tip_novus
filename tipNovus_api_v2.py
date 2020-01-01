import time
import serial
import sys
from cmd_input_class import *
import tpInsertResponse
from string import Template
from tpReadResponse import status_codes, status_codes_2, datetime, logging, current_datetime, current_date

tipnovus_id = "01"
dryer = "DR"
washer = "WA"
integration = "TI"
sleep_time = 0.4
fpath = "C:\\Program Files\\Hamilton\\logs\\tipNovus\\"

run = False
global_timed_cmd = False
bool_issue_cmd = True
hexdec_string = ''

#current_datetime = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
#current_date = current_datetime.split(' ')[0]

##logging.basicConfig(filename=fpath + current_date + "_tipNovus_log.txt", \
##                    filemode="a+", format="%(asctime)s, %(name)s, %(levelname)s [%(filename)s line:%(lineno)d],\t%(message)s", \
##                    datefmt="%d-%b-%y %H:%M:%S", level=logging.DEBUG)

with open(fpath[:-9] + "InstinctV\\pltcode_logs.txt", "r") as fi:
    rows = fi.readlines() #extract run info for header

def read_cmd_ts():
    with Database(db_file) as db:
        return db.queryall('''SELECT * FROM tp_cmds''')

def dcode(byte_response):
    return byte_response.decode('utf-8')

def action_str(tp_id,inter,unit,action):
    return f"{tp_id},{inter},{unit},{action},#"

def connect_str(tp_id):
    return f"{tp_id},@,#"

def ack(tp_id,verif):
    return f"{tp_id},{verif},#"

def response_str(tp_id,data):
    return f"{tp_id},ACK,{data},#"

def inSecs(mins):
    return mins*60

def dply_tasks(response_str):
    global hexdec_string
    sub_response_str = response_str.split(',')[2]
    
    try:
        sub_response_str = sub_response_str.strip().replace('\x0b','')
       
        logging.debug(f"length of 'sub_response_string': {len(sub_response_str)}")
        hexdec_string = sub_response_str #write to sqlite3 for tpRead script
        if len(sub_response_str) == 3 or len(sub_response_str) == 4:                

            cd1 = status_codes[sub_response_str[:2]]
            cd2 = status_codes_2[sub_response_str[2:]]

            sys.stdout.write(f"the compartment sent the status code: {hexdec_string}\n")
            sys.stdout.write(f"status code interpreted as: code1: {cd1}, code2: {cd2}\n")
            logging.info(f"the compartment sent the status code: {hexdec_string}")
            logging.info(f"status code interpreted as: code1: {cd1}, code2: {cd2}")

        elif len(sub_response_str) > 0 and len(sub_response_str) < 3:            
            time_remaining = int(sub_response_str.strip())
            if time_remaining == 0:
                sys.stdout.write("the compartment is not in operation\n")
                logging.info("the compartment is not in operation")
            else:
                sys.stdout.write(f"time remaining for run is: {time_remaining}\n")
                logging.info(f"time remaining for run is: {time_remaining}")
        #elif hexdec_string == '01634500340': #due to current firmware bug
        #    sys.stdout.write(f"the compartment is not in operation - washer status: {hexdec_string}\n")
        #    logging.info(f"the compartment is not in operation - washer status: {hexdec_string}")
    except Exception as e:
        sys.stdout.write(f"error parsing the sub_response string: {sub_response_str.strip()} - {str(e)}\n")
        logging.info(f"error parsing the sub_response string: {sub_response_str.strip()} - {str(e)}")

def sensor_check(sub_response_str):
    try:
        bad_sensor = []
        sensors = ['Manifold', 'Drawer', 'UV', 'Liquid', 'Air', 'Overflow', 'Waste']
        for i,k in enumerate(sub_response_str):
            if k == '0':
                bad_sensor.append(f"{str(i+1)}:{sensors[i]}")
        if bad_sensor:
            sys.stdout.write(f"""the following sensors are faulty: {', '.join(bad_sensor)}\n""")
            logging.info(f"""the following sensors are faulty: {', '.join(bad_sensor)}\n""")
        else:
            sys.stdout.write("sensor check passed")
            logging.info("sensor check passed")
    except Exception as e:
        logging.error(f"""a problem occured parsing the sensor check repsonse string - {str(e)}""")
        sys.stdout.write(f"""a problem occured parsing the sensor check repsonse string - {str(e)}""")

def check_set_str(current_str_cmd):
    bool_var = False
    if "set_dtime" in current_str_cmd:
        time_to_set = int(current_str_cmd.split(',')[1])
        if time_to_set > 1 and time_to_set < 100:
            bool_var = True
        
    if "set_dtemp" in current_str_cmd:
        temp_to_set = int(current_str_cmd.split(',')[1])
        if temp_to_set >= 20 and temp_to_set <= 70:
            bool_var = True
    logging.debug(f"'check_set_str' function returned: {str(bool_var)}")
    return bool_var

cmd_dictionary = {
    "connect": connect_str(tipnovus_id),
    "ack": ack(tipnovus_id,"ACK"),
    'incorrect': ack(tipnovus_id,"NAK"),
    "opendoor_washer": action_str(tipnovus_id, integration, washer, "OD"),
    "closedoor_washer": action_str(tipnovus_id, integration, washer, "CD"),
    "dply_wash": action_str(tipnovus_id, integration,washer, "WS"),
    "abort_wash": action_str(tipnovus_id, integration, washer, "AW"),
    "waste_drain": action_str(tipnovus_id, integration, washer, "WD"),
    "opendoor_dryer": action_str(tipnovus_id, integration, dryer, "OD"),
    "closedoor_dryer": action_str(tipnovus_id, integration, dryer, "CD"),
    "abort_dryer": action_str(tipnovus_id, integration, dryer, "AD"),
    "dply_dryer": action_str(tipnovus_id, integration, dryer, "DS"),
    "get_dtemp" : action_str(tipnovus_id, integration, dryer, "CT"),
    "hello" : "hello,world,#",
    "test" : "01,TI,DR,DS,#",
    "time" : "01,TI,DR,TD,20,#",
    "t" : "testing,#",
}

time_cmd_dictionary = { #not actual duration; just a delay to start pinging again
    "start_dryer": {"cmd" : action_str(tipnovus_id, integration, dryer, "SD"), "time" : inSecs(0.2)},
    "self_clean": {"cmd" : action_str(tipnovus_id, integration, washer, "CL"), "time" : inSecs(0.2)},
    "check_sensor": {"cmd" : action_str(tipnovus_id, integration, washer, "SC"), "time" : inSecs(0.72)},
    "custom2_proc": {"cmd" : action_str(tipnovus_id, integration, washer, "S2"), "time" : inSecs(0.2)},
    "primeA": {"cmd" : action_str(tipnovus_id, integration, washer, "PA"), "time" : inSecs(0.15)},
    "primeDI": {"cmd" : action_str(tipnovus_id, integration, washer, "PD"), "time" : inSecs(0.15)},
    }

cmd_dictionary.update((k, v.encode('ascii')) for k,v in cmd_dictionary.items()) #encode to bytes
time_cmd_dictionary.update((k,{'cmd':v['cmd'].encode('ascii'), 'time': v['time']}) for k,v in time_cmd_dictionary.items())

def connect():
    global run
    ser.reset_output_buffer
    ser.reset_input_buffer
    ser.write(cmd_dictionary['connect'])
    logging.debug(f"sent: '{cmd_dictionary['connect'].decode('utf-8')}'")
    response = ser.read(1)
    while True:
        n = ser.in_waiting
        if not n:
            break
        else:
            response = response + ser.read(n)    
    str_response = dcode(response)
    if str_response == dcode(cmd_dictionary['connect']):
        run = True
    sys.stdout.write(str_response+"\n")
    logging.info(f"response: '{str_response}'")
    tpInsertResponse.insert_str_resp(current_datetime, "01,@,#", str_response) 


def run_task(task, timed_cmd=False, set_var=None):
    global global_timed_cmd
    global run

    run = False
    bool_check_cmd = False
    
    if timed_cmd:
        ser.write(time_cmd_dictionary[task]['cmd'])
        logging.info(f"sent: '{time_cmd_dictionary[task]['cmd'].decode('utf-8')}'")
        global_timed_cmd = True
    
    elif set_var:            
        if task == "set_dtime":
            set_cmd = "TM" #time
            bool_check_cmd = True
        elif task == "set_dtemp":
            set_cmd = "MT" #max temp
            bool_check_cmd = True
                        
        set_cmd = f"{tipnovus_id},{integration},{dryer},{set_cmd},"        
        set_cmd = set_cmd + Template('$var#').substitute(var=set_var)
        
        ser.write(set_cmd.encode()) #set var for temp or time on dryer
        sys.stdout.write(f"sent: '{set_cmd}'\n")
        logging.info(f"sent: '{set_cmd}'")            
    else:
        ser.write(cmd_dictionary[task])
        sys.stdout.write(f"sent: '{cmd_dictionary[task].decode('utf-8')}'\n")
        logging.info(f"sent: '{cmd_dictionary[task].decode('utf-8')}'")

    ser.reset_output_buffer
    ser.reset_input_buffer  
    time.sleep(sleep_time)                
    response = ser.read(1)
    
    while True:
        n = ser.in_waiting
        if not n:
            break
        else:
            time.sleep(0.1)
            response = response + ser.read(n)        

    str_response = dcode(response).strip()

    try:
        if str_response == dcode(cmd_dictionary[task]):
            run = True
    except:
         pass
        
    if bool_check_cmd:                
       
                        
        if str_response == set_cmd:
            #print('it is true')
            run = True
            
    if global_timed_cmd:
        try:
            if str_response == dcode(time_cmd_dictionary[task]['cmd']):
                run = True
        except:
            pass
    
    if timed_cmd:
        tpInsertResponse.insert_str_resp(current_datetime, time_cmd_dictionary[task]['cmd'].decode('utf-8'), str_response)
    else:
        if set_var and bool_check_cmd:
            tpInsertResponse.insert_str_resp(current_datetime, set_cmd, str_response)
        else:
            tpInsertResponse.insert_str_resp(current_datetime, cmd_dictionary[task].decode('utf-8'), str_response)
        
    sys.stdout.write("response: " + str_response+"\n")
    #sys.stdout.write(f'bool_check_cmd variable from run_task function: {bool_check_cmd}\n')    
    #sys.stdout.write(f'run variable from run_task function: {run}\n')
    logging.debug(f'bool_check_cmd var from run_task function: {bool_check_cmd}')
    logging.debug(f'run var from run_task function: {run}')    
    logging.info(f"response: '{str_response}'")
        
def unack():    
    ser.reset_input_buffer
    ser.reset_output_buffer
    ser.write(cmd_dictionary['incorrect'])
    sys.stdout.write(f"nulling cmd: '{cmd_dictionary['incorrect'].decode('utf-8')}'\n")
    logging.info(f"nulling cmd: '{cmd_dictionary['incorrect'].decode('utf-8')}'")
    

def acknowledge(task=None,wait_time=1):
    global run
    global hexdec_string
    hexdec_string = ''
    #if not run and task:
    #    return
    if global_timed_cmd:
        wait_time = time_cmd_dictionary[task]['time']

    ser.reset_output_buffer
    ser.reset_input_buffer
    ser.write(cmd_dictionary['ack'])
    
    logging.info(f"sent: '{cmd_dictionary['ack'].decode('utf-8')}'")
    
    if global_timed_cmd:
        wait_time = int(wait_time)
        sys.stdout.write(f"waiting for cmd: {current_str_cmd}\n")
        logging.debug(f"waiting for cmd: {current_str_cmd}")
        for i in range(wait_time):
            sys.stdout.write('*\n')
            time.sleep(1) # if timed cmd, wait for the defined time
            if i % 10 == 0:
                sys.stdout.write(f'~{wait_time - i} secs left\n')
                logging.debug(f'~{wait_time - i} secs left')
    else:
        time.sleep(sleep_time)
        
    response = ser.read(1)
    while True:
        n = ser.in_waiting
        if not n:
            break
        else:
            time.sleep(0.1)
            response = response + ser.read(n)
            
    str_response = dcode(response)
    
    try:
        sub_response = str_response.split(',')[2]
    except IndexError as e:
        sub_response = "0"
    
    try:        
        if sub_response == '1' or sub_response == '@':
            run = True
    except:
        run = False

    try:
        if str_response == "01,ACK,#":
            run = True
    except:
        run = False

    try:
        
        if 'dply' in task:
            #dply_tasks(sub_response) #print out time remaining or current status or status codes
            dply_tasks(str_response)
        if task == "check_sensor":
            sensor_check(sub_response) #print out sensor numbers that are faulty        
    except:
        run = False
    
    sys.stdout.write(f"response after ack: {str_response}\n")      
    logging.info(f"response after ack: '{str_response}'")
    sys.stdout.write("end of ack function\n")
    if hexdec_string:
        s1, s2, s3, s4 = str_response.split(',')
        str_response = f"{s1},{s2},{hexdec_string},{s4}"
    tpInsertResponse.insert_str_resp(current_datetime, "01,ACK,1,#", str_response)
    

if __name__ == "__main__":
    try:
        if sys.argv[1] == "wh": #write header
            hamilton_script_info = rows[len(rows)-1].replace('"', ' ')

            with open(fpath + current_date + "_tipNovus_log.txt", "a") as fi:
                fi.write("##################################################################################\n")
                fi.write(f"##{hamilton_script_info.strip()}##\n")
                fi.write("##################################################################################\n")
    except:
           pass     #Do nothing if there is no argument to write header
        
    try:
        with serial.Serial(port='COM17',baudrate=115200,timeout=12) as ser:
            if ser.isOpen():       
                connect()                
                if run:
                    sys.stdout.write('Connected!\n')
                    logging.info('Connected!')
                else:
                    sys.stdout.write('Could not connect\n')
                    logging.critical('Could not connect')
                    raise
                        
                #read first ts of cmd
                
                first_dt = read_cmd_ts()[0]                
                    
                while bool_issue_cmd:
                    sys.stdout.write('awaiting new command...\n')
                    logging.debug('awaiting new command...')
                    
                    while True:
                        fetch_db_values = read_cmd_ts()
                        current_dt = fetch_db_values[0]
                        current_str_cmd = fetch_db_values[1]
                        time.sleep(0.4)
                        #logging.debug(f'ts of orig cmd: {first_dt} | ts of cur cmd: {current_dt}')
                        
                        if first_dt < current_dt:
                            logging.info(f'ts of orig cmd: {first_dt} | ts of cur cmd: {current_dt}')   
                            first_dt = current_dt
                            break
                        else:
                            for i in range(5):
                                sys.stdout.write(".\n")
                                if i == 4:
                                    sys.stdout.write('..\n')
                                time.sleep(1)
                            continue

                    logging.info(f'current cmd value: {current_str_cmd}')
                    if current_str_cmd.lower() == 'q':
                        bool_issue_cmd = False
 
                    if current_str_cmd not in cmd_dictionary.keys() and \
                       current_str_cmd not in time_cmd_dictionary.keys() and\
                       current_str_cmd[:9] not in ['set_dtime', 'set_dtemp']:                        
                        if current_str_cmd.lower() == 'q':
                            pass
                        else:
                            sys.stdout.write(f'{current_str_cmd.lower()} was not a valid command\n')
                            logging.error(f'{current_str_cmd.lower()} was not a valid command')
                            continue
                    
                    if current_str_cmd in time_cmd_dictionary.keys():
                        run_task(current_str_cmd, True)                    
                    elif current_str_cmd in cmd_dictionary.keys():                         
                        run_task(current_str_cmd)                        
                    elif ',' in current_str_cmd:
                        if check_set_str(current_str_cmd):                    
                            run_task(task = current_str_cmd.split(',')[0],\
                                 set_var = current_str_cmd.split(',')[1])                        
                        else:
                            sys.stdout.write(f'{current_str_cmd.lower()} was not a valid command; set parameter is not within range\n')
                            logging.error(f'{current_str_cmd.lower()} was not a valid command; set parameter is not within range')
                            continue
                        
                    if current_str_cmd.lower() != 'q':
                        if run:
                            acknowledge(current_str_cmd.lower())                                                    
                        else:
                            unack() #if the strings do not match (run = False)

                    if current_str_cmd.lower() == 'q':
                        sys.stdout.write('disconnecting\n')
                        logging.info('disconnecting')
                        global_timed_cmd = False
                        connect()
                        acknowledge()                        
                        break
                    elif run:
                        sys.stdout.write(f"process ran through for '{current_str_cmd}'\n")
                        logging.debug(f"process ran through for '{current_str_cmd}'")
                    else:
                        sys.stdout.write(f"unsuccessful action '{current_str_cmd}'\n")
                        logging.error(f"unsuccessful action '{current_str_cmd}'")                            
                    
                    global_timed_cmd = False    
                    bool_issue_cmd = True #reset vars back
                    run = False
            else:
                sys.stdout.write("the port is not open\n")
                logging.critical("the port is not open")
                sys.stdout.flush()
                sys.exit(0)
    except Exception as e:
        logging.critical(str(e))
        sys.stdout.write("error: " + str(e))
        sys.stdout.flush()
        sys.exit(0)
