import time
import threading


class CameraEvent(object):
    """An Event-like class that signals all active clients when a new frame is
    available.
    """
    trigger_btn = False

    def __init__(self):
        self.events = {}

    def trigger(self, trig):
        if isinstance(trig, int):
            self.trigger_btn = trig
        else:
            raise ValueError('Must be a Boolean')

    def wait(self):
        """Invoked from each client's thread to wait for the next frame."""
        ident = threading.get_ident()
        #thread identifer - nonzero integer; may be recycled when a thread exists and another thread is created
        if ident not in self.events:
            # this is a new client
            # add an entry for it in the self.events dict
            # each entry has two elements, a threading.Event() and a timestamp as 2-element list
            # self.events[ident] = [threading.Event(), time.time()]
            self.events[ident] = threading.Event()
        return self.events[ident].wait()
        #wait() - block until the internal flag is true, if the internal flag is true on entry,
        #return immediately, otherwise block until another thread calls set() to set the flag
        #to true or until timeout occurs

    def set(self):
        """Invoked by the camera thread when a new frame is available."""
        # now = time.time()
        remove = None
        # remove the thread
        for ident, event in self.events.items():
            if not event.isSet() and self.trigger_btn:
                # if this client's event is not set, then set it
                # also update the last set timestamp to now
                event.set()
                #set internal flag to true; all threads waiting for it to become true are awakened
                # event[1] = now
            else:
                # if the client's event is already set, it means the client
                # did not process a previous frame
                # if the event stays set for more than 5 seconds, then assume
                # the client is gone and remove it
                # if now - event[1] > 5:
                    # remove = ident
                remove = ident
        if remove:
            # if the remove variable has a threading identifier then delete the thread to free up the memory
            del self.events[remove]

    def clear(self):
        """Invoked from each client's thread after a frame was processed."""
        self.events[threading.get_ident()].clear()
        # set the internal flag to false, subsequently threads calling wait() will block until set() is called
        # to set the internal flag to true again


class BaseCamera(object):
    thread = None  # background thread that reads frames from camera
    frame = None  # current frame is stored here by background thread
    # last_access = 0  # time of last client access to the camera
    # trigger_btn = False

    def __init__(self):
        BaseCamera.cam_event = CameraEvent()

    def start(self):
        """Start the background camera thread if it isn't running yet."""
        # start background frame thread
        BaseCamera.cam_event.trigger(True)
        print(BaseCamera.cam_event.trigger_btn)
        BaseCamera.thread = threading.Thread(target=self._thread)
        BaseCamera.thread.start()

        # wait until frames are available
        while self.get_frame() is None:
            time.sleep(0)

    def stop(self):
        """Stop the background camera thread"""
        BaseCamera.cam_event.trigger(False)
        print(self.cam_event.trigger_btn)


    def get_frame(self):
        """Return the current camera frame."""

        # wait for a signal from the camera thread
        BaseCamera.cam_event.wait()
        BaseCamera.cam_event.clear()

        return BaseCamera.frame

    @staticmethod
    def frames():
        """"Generator that returns frames from the camera."""
        raise RuntimeError('Must be implemented by subclasses.')

    @classmethod
    def _thread(cls):
        """Camera background thread."""
        if BaseCamera.cam_event.trigger_btn:
            print('Starting camera thread.')
            frames_iterator = cls.frames()
            for frame in frames_iterator:
                BaseCamera.frame = frame
                BaseCamera.cam_event.set()  # send signal to clients
                time.sleep(0)

                # if there hasn't been any clients asking for frames in
                # the last 10 seconds then stop the thread
                if not BaseCamera.cam_event.trigger_btn:
                    frames_iterator.close()
                    print('Stopping camera thread...')
                    break
            BaseCamera.thread = None
