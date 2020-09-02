import pickle
from sklearn.linear_model import LinearRegression
import sys
import os
from eTape_sensor.hardware_config import *
from datetime import datetime
#import requests
from rest_sql3_class import instance_dir, tpdb
sys.path.insert(1, instance_dir)
from logging_decor import create_logger, handle_logs, time_host, get_time


time_interval = 800 # seconds
#vid_status = {}

def bkg_etape(thread_event):
    while not thread_event.wait(timeout=time_interval):
        background_check_volume()



# def gen_unq_id(size, chars=string.ascii_letters + string.digits):
#     return ''.join(choice(chars) for x in range(size))


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
    load_model = pickle.load(open(f'{os.path.join(instance_dir,"static")}/{filename}', 'rb'))
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
    print(f'VOLT_5L:{round(volt_sm,3)}__PRED_VOL_5L:{round(pred_volume_sm,3)} -- VOLT_20L:{round(volt_lg,3)}__PRED_VOL_20L:{round(pred_volume_lg,3)}', end='\r', flush=True)
