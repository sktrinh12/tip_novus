#import logging
import pickle
#import threading
from sklearn.linear_model import LinearRegression
import sys
import os
from eTape_sensor.hardware_config import *
from datetime import datetime
import string
import sqlite3
from sqlite3 import Error
from rest_sql3_class import instance_dir
from random import choice
sys.path.insert(1, instance_dir)
from logging_decor import create_logger


time_interval = 800 # seconds
vid_status = {}

def validate_trigger_cmd():
    check_trigger = vid_status['trigger'] in ['on', 'off']
    check_time = vid_status['time'].isdigit()
    check_workflow = 'workflow' in vid_status['wrkflow_name'].lower()
    return all([item == True for item in [check_trigger, check_time, check_workflow]])

def bkg_etape(thread_event):
    while not thread_event.wait(timeout=time_interval):
        background_check_volume()


def record_video(record_time, wrkflw):
    with picamera.PiCamera() as camera:
        camera.resolution = (640, 480)
        unq_id = gen_unq_id(12)
        record_time = int(record_time)
        current_time = datetime.now()
        time_iso_format = current_time.isoformat()
        ts_file = current_time.strftime('%G-%b-%dT%H_%M_%S')
        file_path = f'{file_path}{ts_file}_{unq_id}.h264'
        camera.start_recording(file_path, quality=10)
        camera.wait_recording(record_time)
        camera.stop_recording()
    conn = create_connection(db_path)
    with conn:
        items = (current_time, unq_id, wrkflw)
        insert_items(conn, items)
    conn.commit()
    return file_path


def gen_unq_id(size, chars=string.ascii_letters + string.digits):
    return ''.join(choice(chars) for x in range(size))

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    return conn

def insert_items(conn, items):
    sql = f'''INSERT INTO vidids VALUES (?,?,?)'''
    cur = conn.cursor()
    cur.execute(sql, items)
    return cur.lastrowid

def get_date():
    return str(datetime.today().strftime('%G-%d-%b'))

#def setup_logger(name, log_file, level = logging.INFO):
#    handler = logging.FileHandler(log_file, mode='+a')
#    handler.setFormatter(fmt = formatter)
#    logger = logging.getLogger(name)
#    logger.setLevel(level)
#    logger.addHandler(handler)
#    return logger
#
def check_voltage(carboy_size, logs):
      chan = channels_dict[f'{carboy_size}']
      if carboy_size == 'small':
          logs.info(f'adc: {chan.value}, voltage: {chan.voltage}')
      elif carboy_size == 'large':
          logs.info(f'adc: {chan.value}, voltage: {chan.voltage}')
      return chan.voltage

def shutdown():
    for leds in led_dict.keys():
        trigger_led(led_dict[f'{leds}'], 'off')
    GPIO.cleanup()
    sys.exit(0)

def signal_handler(signal, frame):
    print('\nYou pressed Ctrl+C! Python script exiting ...')
    shutdown()

def trigger_led(pin, trigger):
    if trigger == 'on':
        if GPIO.input(pin) == GPIO.HIGH:
            return
        else:
            GPIO.output(pin, GPIO.HIGH)
    elif trigger == 'off':
        if GPIO.input(pin) ==  GPIO.LOW:
            return
        else:
            GPIO.output(pin, GPIO.LOW)

def poly_reg_model(filename):
    load_model = pickle.load(open(f'{os.path.join(instance_dir,"eTape_sensor", "static")}/{filename}', 'rb'))
    return load_model

def condition_led(volume, carboy):
    if carboy == 'small':
        if float(volume) > carboy_capacity[carboy]['min']:
            trigger_led(led_dict[f'green_{carboy}'], 'on')
            trigger_led(led_dict[f'red_{carboy}'], 'off')
        else:
            trigger_led(led_dict[f'red_{carboy}'], 'on')
            trigger_led(led_dict[f'green_{carboy}'],'off')
    elif carboy == 'large':
        if float(volume) < carboy_capacity[carboy]['max']:
            trigger_led(led_dict[f'green_{carboy}'], 'on')
            trigger_led(led_dict[f'red_{carboy}'], 'off')
        else:
            trigger_led(led_dict[f'red_{carboy}'], 'on')
            trigger_led(led_dict[f'green_{carboy}'],'off')

def check_prediction(value):
    if value < 0:
        return 0
    return value

def background_check_volume():
    small_carboy_logs = create_logger('small_5L_carboy')
    large_carboy_logs = create_logger('large_20L_carboy')
    volt_sm = check_voltage('small', small_carboy_logs)
    volt_lg = check_voltage('large', large_carboy_logs)
    model_sm = poly_reg_model('model_sm.sav')
    model_lg = poly_reg_model('model_lg.sav')
    pred_volume_sm = check_prediction(model_sm.predict([[volt_sm]])[0])
    pred_volume_lg = check_prediction(model_lg.predict([[volt_lg]])[0])
    small_carboy_logs.info(f'pred_vol: {pred_volume_sm}')
    large_carboy_logs.info(f'pred_vol: {pred_volume_lg}')
    condition_led(pred_volume_sm, 'small')
    condition_led(pred_volume_lg, 'large')
    print(f'VOLT_5L: {round(volt_sm,3)} _ PRED_VOL_5L: {round(pred_volume_sm,3)}  --  VOLT_20L: {round(volt_lg,3)} _ PRED_VOL_20L: {round(pred_volume_lg,3)}', end='\r', flush=True)
