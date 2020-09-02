from threading import Thread
from logging_decor import handle_logs, get_time
from eTape_sensor.pi_camera import picamera
from datetime import datetime
import subprocess
import os

rec_vid_dir = '/home/pi/mount/hampc/tp_logs/recorded_videos/'

def validate_trigger_cmd(vid_status_dict):
    #check_trigger = vid_status['trigger'] in ['on', 'off']
    check_time = vid_status_dict['time'].isdigit() and int(vid_status_dict['time']) > 0
    check_workflow = 'workflow' in vid_status_dict['wrkflow_name'].lower()
    return all([item == True for item in [check_time, check_workflow]])


class ThreadWithReturnValue(Thread):

    '''inherits from base Thread class and allows to return the value from the target function'''

    def __init__(self, group=None, target=None, name=None, args=(), Verbose=None):
        Thread.__init__(self, group, target, name, args)
        self._return = None

    def run(self):
        print(type(self._target))
        if self._target is not None:
            self._return = self._target(*self._args)

    def join(self, *args):
        Thread.join(self, *args)
        return self._return


class RecordVideoClass:

    '''simple class that will record a video using the picamera that will be invoked by the ThreadWithReturnValue; able to start and stop manually'''
    def __init__(self):
        self._running = True

    def terminate(self):
        self._running = False

    def record_video(self, record_time, wrkflw):
        if self._running and int(record_time) != 0:
            with picamera.PiCamera() as camera:
                camera.resolution = (640, 480)
                record_time = int(record_time)
                ts = datetime.strptime(get_time(), '%Y-%b-%d %H:%M:%S').strftime('%Y-%b-%d_%H-%M-%S')
                print(ts)
                file_name = f'{ts}_{wrkflw}.h264'
                file_path = os.path.join(rec_vid_dir,'h264_format', file_name)
                camera.start_recording(file_path, quality=10) #lower is better
                camera.wait_recording(record_time) #in seconds
                camera.stop_recording()
                file_name = file_name.split('.')[0] + '.mp4'
                #print(f'filename: {file_name}')
                #print(f'filepath: {file_path}')
                new_file_path= os.path.join(rec_vid_dir, 'mp4_format', file_name)
                subproc_cmd = f"MP4Box -add {file_path} {new_file_path}"
                #convert from h264 -> mp4
                try:
                    output = subprocess.check_output(subproc_cmd, stderr=subprocess.STDOUT, shell=True)
                    handle_logs('Subprocess for MP4Box convesion to {} was successful (record time = {}s)'.format(file_name, record_time))
                except subprocess.CalledProcessError as e:
                    err_msg= f'Failed to convert file {file_path} - cmd:{e.cmd}; output:{e.output}'
                    handle_logs(('error',err_msg))
        return file_path
