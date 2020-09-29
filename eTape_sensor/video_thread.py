from threading import Thread
from logging_decor import handle_logs#, get_time
from eTape_sensor.pi_camera import picamera
from datetime import datetime
import subprocess
import os

#rec_vid_dir = '/home/pi/mount/hampc/tp_logs/recorded_videos/'
rec_vid_dir = os.path.join('/home/pi/mount/hampc/tp_logs/recorded_videos')

def validate_trigger_cmd(vid_status_dict):
    #check_trigger = vid_status['trigger'] in ['on', 'off']
    check_time = vid_status_dict['time'].isdigit() and int(vid_status_dict['time']) < 15
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
        self._camera = picamera.PiCamera()
        self._camera.resolution = (640, 480)
        #self._camera = None
        self._file_name = ''
        self._file_path = ''

    def terminate(self):
        try:
            self._camera.stop_recording()
        except picamera.PiCameraNotRecording:
            pass
        self._camera.close()
        file_name = self._file_name.split('.')[0] + '.mp4'
        new_file_path= os.path.join(rec_vid_dir, 'mp4_format', file_name)
        subproc_cmd = f"MP4Box -add {self._file_path} {new_file_path}"
        #convert from h264 -> mp4
        try:
            output = subprocess.check_output(subproc_cmd, stderr=subprocess.STDOUT, shell=True)
            handle_logs('Subprocess for MP4Box convesion to {} was successful'.format(self._file_name ))
        except subprocess.CalledProcessError as e:
            err_msg= f'Failed to convert file {self._file_path} - cmd:{e.cmd}; output:{e.output}'
            handle_logs(('error',err_msg))

        # clean up h264 files
        if os.path.exists(new_file_path):
            parent_dir = os.path.dirname(self._file_path)
            for hfile in os.listdir(parent_dir):
                os.remove(os.path.join(parent_dir, hfile))

    def record_video(self, record_time, wrkflw):
        #if self._running and int(record_time) < 15:
        record_time = int(record_time)
        #ts = datetime.strptime(get_time(), '%Y-%b-%d %H:%M:%S').strftime('%Y-%b-%d_%H-%M-%S')
        ts = datetime.now().strftime('%Y-%b-%d_%H-%M-%S')
        self._file_name = f'{ts}_{wrkflw}.h264'
        self._file_path = os.path.join(rec_vid_dir,'h264_format', self._file_name)
        self._camera.start_recording(self._file_path, quality=22) # lower is better
        self._camera.wait_recording(record_time) #in seconds
        return self._file_path
