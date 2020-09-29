from flask_restful import Resource, Api
from flask import render_template, Response, jsonify, redirect, request, flash, send_from_directory, abort
from eTape_sensor.pi_camera import *
from eTape_sensor.sensor_funcs import *
import signal
import json
from main_funcs import *
from tp_schemas import *
from eTape_sensor.video_thread import *
from logging_decor import *

api = Api(app)
picam = Camera()
record_video_cls = None
vd_thread = None

app.config['SECRET_KEY'] = 'SECRET'
app.config['VIDEO_DIR'] = os.path.join(fpath, 'recorded_videos', 'mp4_format')
app.config['IPADDR'] = '192.168.1.212'

#{{{ ETAPE SENSOR
class waste_check_5L_carboy(Resource):
    def get(self):
        small_carboy_logs = create_logger('small_5L_carboy')
        volt_sm = check_voltage('small', small_carboy_logs)
        model_sm = poly_reg_model('model_sm.sav')
        pred_volume_sm = check_prediction(model_sm.predict([[volt_sm]])[0])
        small_carboy_logs.info(f'<< API_call >> pred_vol_small_carboy: {pred_volume_sm}')
        return {'small_carboy_voltage': volt_sm, 'small_carboy_predicted_vol' : pred_volume_sm}


class waste_check_20L_carboy(Resource):
    def get(self):
        large_carboy_logs = create_logger('large_20L_carboy')
        volt_lg = check_voltage('large', large_carboy_logs)
        model_lg = poly_reg_model('model_lg.sav')
        pred_volume_lg = check_prediction(model_lg.predict([[volt_lg]])[0])
        large_carboy_logs.info(f'<< API_call >> pred_vol_large_carboy: {pred_volume_lg}')
        return {'large_carboy_voltage' : volt_lg, 'large_carboy_predicted_vol' : pred_volume_lg}
#}}}

@app.route("/<status>")
def onAction(status):
    '''
    turn on lamp switch
    '''
    if status == "on":
        pin = 19
        light_img = ''
        GPIO.output (pin, GPIO.LOW)
        print ("light is on - from flask route")
    if status == "off":
        pin = 0
        light_img = ''
        GPIO.output(pin, GPIO.HIGH)
        print("light is off - from flask route")
    return jsonify({"pin" : pin, "status" : status})


class record_video_stream_on(Resource):
    def put(self):
        global record_video_cls, vd_thread
        vid_status = {}
        vid_status['time'] = request.form['time']
        vid_status['wrkflow_name'] = request.form['wrkflow_name']
        if validate_trigger_cmd(vid_status):
            record_video_cls = RecordVideoClass()
            vd_thread = ThreadWithReturnValue(target=record_video_cls.record_video, args=(vid_status['time'], vid_status['wrkflow_name']))
            vd_thread.start()
            return {'response' :  'video recording...'}, 201
        else:
            abort_if_invalid({'response' : f'error involving argument validation of time and workflow name - {vid_status}'})

class record_video_stream_off(Resource):
    def get(self):
        global record_video_cls, vd_thread
        #print(vd_thread.is_alive())
        record_video_cls.terminate()
        # join with a thread, which waits for it to terminate
        # This blocks the calling thread until the thread whose
        # join() method is called terminates
        file_path = vd_thread.join()
        return {'response': file_path}, 200


@app.route('/tp_ser_wbsrv/video_feed')
def video_feed():
    return render_template('video_feed.html')

@app.route('/tp_ser_wbsrv')
@app.route('/')
def video_recording():
    return render_template('index.html')

@app.route('/tp_ser_wbsrv/filter_by_date', methods=["POST"])
def filter_by_date():
    date = request.form['date-picker']
    print(date)
    if not date:
        msg = "Enter a date to filter by"
        print(msg)
        flash(msg, 'warning')
        return redirect('/')
    filtered_lst = filter_func(date)
    #today = datetime.strptime(get_time(), '%Y-%b-%d %H:%M:%S')
    today = datetime.now().strftime('%Y-%b-%d %H:%M:%S')
    if datetime.strptime(date, dt_fmt).day > today.day:
        msg = f"{date} is in the future!"
        print(msg)
        flash(msg, 'warning')
        return redirect('/')
    if not filtered_lst:
        msg = f"{date} didn't contain any recordings"
        print(msg)
        flash(msg, 'warning')
        return redirect('/')
    return render_template('index.html', listdir=filtered_lst, ipaddr = app.config['IPADDR'])


@app.route('/tp_ser_wbsrv/video/<filename>')
def show_video(filename):
    try:
        #print(f"{app.config['VIDEO_DIR']}/{filename}")
        return send_from_directory(app.config['VIDEO_DIR'], filename=filename)
    except FileNotFoundError:
        abort(404)

@app.route('/tp_ser_wbsrv/video_feed/start')
def start():
    global picam
    picam.start()
    btn_res = request.args.get('btn_type')
    return jsonify({'btn' : btn_res})

@app.route('/tp_ser_wbsrv/video_feed/stop')
def stop():
    global picam
    picam.stop()
    btn_res = request.args.get('btn_type')
    return jsonify({'btn' : btn_res})

@app.route('/videofeed')
def videofeed():
    return Response(gen(picam), mimetype='multipart/x-mixed-replace; boundary=frame')
#
#@app.route('/output_test')
#def output_test():
#    def inner():
#        for x in range(100):
#            time.sleep(1)
#            json_data = json.dumps({'data' : x})
#            yield f"data:{x}\n\n"
#    return Response(inner(), mimetype = 'text/event-stream')

#@app.route('/console_output')
#def console_output():
#    def inner_co():
#        #main() was the tipnovus_api_v3.py fx
#    return Response(inner_co(), mimetype='text/event-stream')

#@app.route('/tp_ser_wbsrv/display_std_output')
#def dply_output():
#    return render_template('console_output.html' )

#}}}

#{{{ TPSerWebServ class
class tp_wbsrv_upd(Resource):
    def put(self, cmd):
#        try:
#            current_ts = get_time()
#        except Exception:
        current_ts = datetime.now().strftime('%G-%b-%d %H:%M:%S')
        input_cmd_dict = {'cmd' : cmd, \
                          'code_cmd' : request.form['code_cmd']}
        schema_check = False
        req_setval = request.form.get('setval', False)
        if req_setval:
            tpsetcmd_schema = tp_ser_check_setcmd_schema()
            try:
                tpsetcmd_schema.load({'cmd_' : cmd}) #check if set_d -type of command
                validate_val(cmd, input_cmd_dict['code_cmd'], request.form['setval']) #check if the code_cmd is valid
                validate_val(cmd, request.form['response'], request.form['setval']) #check if the response string is valid
                input_cmd_dict['response'] = "01,ACK,#" #temporarily set to a valid response to parse in marshmallow schema
                input_cmd_dict['setval'] = request.form['setval']
                tpcmd_schema.load(input_cmd_dict) #load in main schema to check ranges of setval; with fake response since it will complain if it is a set cmd (won't match up with the fixed list)
                input_cmd_dict['response'] = request.form['response'] #overwrite the response to the real one
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
                input_cmd_dict['response'] = request.form['response']
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
                print(input_cmd_dict)
            change = update_data(current_ts, cmd, input_cmd_dict['code_cmd'], input_cmd_dict['response'])
            output = f'func: {self.__class__.__name__}_{self.put.__name__}', f'ts: {current_ts}',f'sent: {cmd}', f"response: {input_cmd_dict['response']}"
            handle_logs(output)
            return change, 201
        else:
            if req_setval:
                input_cmd_dict['setval'] = request.form['setval']
            abort_if_invalid(input_cmd_dict)


class tp_ser_wbsrv_response(Resource):
    # get the response
    def get(self):
        with tpdb(tp_db_filepath) as db:
            res = db.queryone("SELECT response FROM CMDRESPONSE")
            output = f'func: {self.__class__.__name__}_{self.get.__name__}', f"response: {res}"
            handle_logs(output)
            return  {'response' : res}


class tp_ser_wbsrv(Resource):
    # issuing commands
    def put(self, cmd):
        schema_check, data_dict = ref_fx_cmd_proc(cmd, send_cmd) #send cmd is a function
        if schema_check:
            #then acknowledge
            schema_check, ack_dict = ref_fx_cmd_proc(cmd, ack_cmd)
            if schema_check and data_dict['response']:
                #if cmd in ['dply_wash', 'dply_dryer', 'check_sensor'] or cmd.startswith('set_dt'):
                return ack_dict, 201
                #return data_dict, 201
            else:
                return data_dict, 502
        else:
            abort_if_invalid(data_dict)


class tp_ser_wbsrv_check_con(Resource):
    # check connection of tip novus
    def get(self):
        try:
            bool_connected =  check_conn()
        except AttributeError as e:
            bool_connected = False
        output = f'func: {self.__class__.__name__}_{self.get.__name__}', f'is_connected? =  {bool_connected}'
        return {'response' : bool_connected}


class tp_ser_wbsrv_con(Resource):
    # connect to tip novus
    def get(self):
        s, r = connect_tp()
        output = f'func: {self.__class__.__name__}_{self.get.__name__}', f'sent: {s}', f"response: {r}"
        handle_logs(output)
        return {'sent' : s, 'response' : r}

class tp_ser_wbsrv_discon(Resource):
    # disconnect from tip novus
    def get(self):
        s, s2, r = disconnect_tp()
        output = f'func: {self.__class__.__name__}_{self.get.__name__}', f'sent: {s} {s2}', f"response: {r}"
        handle_logs(output)
        return {'sent' : f'{s} {s2}', 'response' : r}

#}}}

class tp_ser_wbsrv_cmds(Resource):
    # get list of available commands
    def get(self):
        return send_cmd_dict

#{{{ TIP NOVUS API
api.add_resource(tp_ser_wbsrv_con, '/tp_ser_wbsrv/connect')
api.add_resource(tp_ser_wbsrv_check_con, '/tp_ser_wbsrv/check_con')
api.add_resource(tp_ser_wbsrv_discon, '/tp_ser_wbsrv/disconnect')
api.add_resource(tp_ser_wbsrv_response, '/tp_ser_wbsrv/response')
api.add_resource(tp_wbsrv_upd, '/tp_ser_wbsrv/update/<string:cmd>') # change/update the command andrepsonse string 
api.add_resource(tp_ser_wbsrv, '/tp_ser_wbsrv/<string:cmd>') # issue commands to tp
api.add_resource(tp_ser_wbsrv_cmds, '/tp_ser_wbsrv/cmds') #get list of valid commands
#}}}


#{{{ ETAPE SENSOR API SOURCE
api.add_resource(waste_check_5L_carboy, '/tp_ser_wbsrv/carboy/5L')
api.add_resource(waste_check_20L_carboy, '/tp_ser_wbsrv/carboy/20L')
api.add_resource(record_video_stream_on, '/tp_ser_wbsrv/record_video_on') #start video recording
api.add_resource(record_video_stream_off, '/tp_ser_wbsrv/record_video_off') #stop video recording
#}}}

signal.signal(signal.SIGINT, signal_handler)
check_waste_volume = threading.Event()
continue_logging_tp = threading.Event()

bkg_thread = threading.Thread(name = 'bkg_led_indicator', target = bkg_etape, args=(check_waste_volume,))
bkg_thread.setDaemon(True)
bkg_thread.start()

bkg_tp_logging = threading.Thread(name = 'bkg_tp_logging', target = bkg_tp_log, args=(continue_logging_tp,))
bkg_tp_logging.setDaemon(True)
bkg_tp_logging.start()

if __name__ == '__main__':
    background_check_volume()
    app.run(debug=True, host='0.0.0.0', threaded=True)
