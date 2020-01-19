str_resp = ''
code1 = ''
code2 = ''

status_codes = {
    '11' : 'SUB-PROTOCOL STARTED',
    '12' : 'SUB-PROTOCOL FINISHED',
    '13' : 'WASHER PROCESS ABORTED',
    '14' : 'WASHER PROCESS PAUSED',
    '15' : 'WASHER PROCESS CONTINUED',
    '16' : 'WASHER SONICATION ACTIVATED',
    '17' : 'REAGENT ADDED TO SYSTEM',
    '18' : 'WASHER AGITATION ACITIVATED',
    '19' : 'MAIN UV LIGHT ACTIVATED',
    '20' : 'WASTE DRAIN PUMP ACTIVATED',
    '23' : 'WASHER METHOD STARTED',
    '24' : 'WASHER METHOD COMPLETED',
    '25' : 'DRAWER AGITATION ACTIVATED',
    '26' : 'WASHER SONICATION DEACTIVATED',
    '27' : 'UV LIGHT DEACTIVATED',
    '28' : 'WASTE DRAIN PUMP DEACTIVATED',
    '44' : 'WASH PROTOCOL STARTED',
    '45' : 'WASH PROTOCOL FINISHED',
    '51' : 'USER INPUT (lcd)',
    '52' : 'INTEGRATION CONTROL',
    '53' : 'LIQUID SENSOR',
    '54' : 'WASTE SENSOR',
    '55' : 'OVERFLOW SENSOR',
    '56' : 'DRAWER SENSOR',
    '57' : 'MANIFOLD SENSOR',
    '58' : 'UV SENSOR',
    '59' : 'AIR SENSOR',
    '61' : 'LINE REFILL',
    '62' : 'PRIME',
    '63' : 'WASTE DRAIN',
    '64' : 'LINE PURGE',
    '65' : 'OPEN WASHER DRAWER',
    '66' : 'CLOSE WASHER DRAWER',
    '67' : 'SELF CLEAN',
    '68' : 'SENSOR CHECK'
    }

status_codes_2 = {
    '0' : 'NULL',
    '51' : 'USER INPUT',
    '52' : 'INTEGRATION CONTROLLER',
    '53' : 'LIQUID SENSOR',
    '54' : 'WASTE SENSOR',
    '55' : 'OVERFLOW SENSOR',
    '56' : 'DRAWER SENSOR',
    '57' : 'MANIFOLD SENSOR',
    '58' : 'UV SENSOR',
    '59' : 'AIR SENSOR',
    '61' : 'LINE REFILL',
    '62' : 'PRIME',
    '63' : 'WASTE DRAIN',
    '64' : 'LINE PURGE',
    '65' : 'OPEN WASHER DRAWER',
    '66' : 'CLOSE WASHER DRAWER',
    '67' : 'SELF CLEAN',
    '68' : 'SENSOR CHECK'
    }

def print_output(output):
    print(output)
    #yield f"data: {output}\n\n"

def output_status(split_str_resp, Er_code):
    global code1
    global code2
    try:
        if Er_code:
            code_1 = status_codes[split_str_resp[:2]]
            code_2 = status_codes_2[split_str_resp[2:]]
            logging.error(f"""error during run: code_1: {code_1}, code_2: {code_2}""")
        else:
            code_1 = status_codes[split_str_resp[:2]]
            code_2 = status_codes_2[split_str_resp[2:]]
            logging.info(f"""code output: code_1: {code_1}, code_2: {code_2}""")

        code1 = split_str_resp[:2]
        code2 = split_str_resp[2:]

        return (code_1,code_2)
    except Exception as e:
        logging.critical(f"no code string found > {str(e)}")
        code1 = "-1"
        code2 = "1"
        return (None, None)

def dply_cmds(sub_response_str):
    try:
        sub_response_str = sub_response_str.strip().replace('\x0b','')
        if len(sub_response_str) == 3 or len(sub_response_str) == 4:
            cd1 = status_codes[sub_response_str[:2]]
            cd2 = status_codes_2[sub_response_str[2:]]

            print_output(f"the compartment sent the status code: {sub_response_str}")
            print_output(f"status code interpreted as: code1: {cd1}, code2: {cd2}")
            return sub_response_str, cd1, cd2
            #return the 3-4 digit code and the interpretations of both

        elif len(sub_response_str) > 0 and len(sub_response_str) < 3:
            time_remaining = int(sub_response_str.strip())
            if time_remaining == 0:
                print_output("the compartment is not in operation")
            else:
                print_output(f"time remaining for run is: {time_remaining}")
            return sub_response_str.strip()
    except Exception as e:
        print_output(f"error parsing the sub_response string: {sub_response_str.strip()} - {str(e)}")

def sensor_check(sub_response_str):
    try:
        bad_sensor = []
        sensors = ['Manifold', 'Drawer', 'UV', 'Liquid', 'Air', 'Overflow', 'Waste']
        if '0' in sub_response_str or '1' in sub_response_str:
            for i,k in enumerate(sub_response_str):
                if k == '0':
                    bad_sensor.append(f"{str(i+1)}:{sensors[i]}")
            if bad_sensor:
                print_output(f"""the following sensors are faulty: {', '.join(bad_sensor)}""")
            else:
                print_output("sensor check passed")
        else:
            print_output(f"The sensor_check output: '{sub_response_str}' is not interpretable")
        if bad_sensor:
            return ', '.join(bad_sensor)
        else:
            return bad_sensor
    except Exception as e:
        print_output(f"""a problem occured parsing the sensor check repsonse string - {str(e)}\n""")

def split_resp(str_response):
    try:
        sub_response = str_response.split(',')[2]
    except IndexError as e:
        sub_response = ""
    return sub_response

# def check_sr_char(sub_response):
#     if sub_response == '1' or sub_response == '@':
#         return True
#     return False

# def check_ack_resp(str_response):
#     if str_response == "01,ACK,#":
#         return True
#     return False
