import zmq
import cv2
from threading import Thread
import numpy as np
import os
import glob
import time
from util import log
import queue

def clip_path(camera, timestamp):
    return "/dev/shm/{}_{}.mp4".format(camera, timestamp)


class ObjectState():
    objects = None
    previous_objects = None
    stale_counter = 0
    motion = 0
    start_timestamp = 0
    clip_writer = None

    def __init__(self, clip_writer=None):
        self.clip_writer = clip_writer

    def generate_state(self, objects):
        state = []
        for obj in objects:
            new_obj = {
                "center_x": obj["xmin"] + int((obj["xmax"] - obj["xmin"]) / 2),
                "center_y": obj["ymin"] + int((obj["ymax"] - obj["ymin"]) / 2),
                "left": obj["xmin"],
                "top": obj["ymin"],
                "width": obj["xmax"] - obj["xmin"],
                "height": obj["ymax"] - obj["ymin"],
                "class_id": obj["class_id"],
                "confidence": obj["confidence"]
            }

            new_obj["spot"] = self.calculate_spot(new_obj)

            state.append(new_obj)

        return state

    def check_state(self, objects, timestamp):
        if self.objects == None:
            self.objects = self.generate_state(objects)
            return

        if len(objects) != len(self.objects):
            self.start_motion(timestamp)
        else:
            hit_spots = set()
            for obj in objects:
                hit_spots = self.in_spot(obj, self.objects, hit_spots)

            if len(hit_spots) != len(self.objects):
                self.start_motion(timestamp)
            else:
                self.stale_counter += 1

        # fix state
        if self.stale_counter >= 3:
            self.stale_counter = 0
            self.stop_motion(timestamp)

        self.objects = self.generate_state(objects)

    def start_motion(self, timestamp):
        self.stale_counter = 0
        if self.motion == 0:
            self.motion = timestamp
            self.clip_writer.startx = True

    def stop_motion(self, timestamp):
        if self.motion > 0:
            print("Motion recorded from {} to {} frame".format(self.motion, timestamp))
            self.clip_writer.startx = False
            self.motion = 0

    def in_spot(self, new_obj, objects, hit_spots):
        center_x = new_obj["xmin"] + int((new_obj["xmax"] - new_obj["xmin"]) / 2)
        center_y = new_obj["ymin"] + int((new_obj["ymax"] - new_obj["ymin"]) / 2)

        for obj in objects:
            (xmin, xmax, ymin, ymax) = obj["spot"]

            if xmin <= center_x <= xmax and ymin <= center_y <= ymax:
                hit_spots.add(obj["spot"])
                break

        return hit_spots

    def calculate_spot(self, obj):
        return (
            obj["center_x"] - int(obj["width"] * 0.1),
            obj["center_x"] + int(obj["width"] * 0.1),
            obj["center_y"] - int(obj["height"] * 0.1),
            obj["center_y"] + int(obj["height"] * 0.1),
        )


class ClipWriter(Thread):
    stop = False
    camera = None
    write_queue = None
    startx = False

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, camera=None, write_queue=None):
        super(ClipWriter, self).__init__(group=group, target=target, name=name)
        self.camera = camera
        self.write_queue = write_queue

    def run(self):

        out = None
        while not self.stop:

            if self.startx == True and out == None:
                fourcc = cv2.VideoWriter_fourcc('a', 'v', 'c', '1')
                out = cv2.VideoWriter("clip_{}.mp4".format(int(time.time())), fourcc, self.camera["meta"]["fps"], (self.camera["meta"]["width"], self.camera["meta"]["height"]))

            if self.startx == False and out != None:
                out.release()
                out = None

            try:
                frame = self.write_queue.get(block=False)
            except queue.Empty:
                time.sleep(0.01)
                continue

            if out:
                out.write(frame)


class ResponseReader(Thread):
    stop = False
    camera = {}
    response_queue = None
    object_state = None

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, response_queue=None, clip_writer=None):
        super(ResponseReader, self).__init__(group=group, target=target, name=name)
        self.response_queue = response_queue
        self.stop = False
        self.object_state = ObjectState(clip_writer=clip_writer)

    def run(self):
        save_snapshot = False
        while not self.stop:
            try:
                (frame, timestamp, objects) = self.response_queue.get(block=False)
            except queue.Empty:
                time.sleep(0.1)
                continue

            self.object_state.check_state(objects, timestamp)

            if self.object_state.motion > 0 and save_snapshot == False:
                save_snapshot = True
                origin_im_size = frame.shape[:-1]
                if len(objects) > 0:
                    for obj in objects:
                        if obj['xmax'] > origin_im_size[1] or obj['ymax'] > origin_im_size[0] or obj['xmin'] < 0 or obj['ymin'] < 0:
                            continue
                        color = (int(min(obj['class_id'] * 12.5, 255)), min(obj['class_id'] * 7, 255), min(obj['class_id'] * 5, 255))
                        det_label = str(obj['class_id'])

                        cv2.rectangle(frame, (obj['xmin'], obj['ymin']), (obj['xmax'], obj['ymax']), color, 2)
                        cv2.putText(frame, det_label + ' ' + str(round(obj['confidence'] * 100, 1)) + ' %', (obj['xmin'], obj['ymin'] - 7), cv2.FONT_HERSHEY_COMPLEX, 0.6, color, 1)

                print("Saving snapshot")
                cv2.imwrite('snapshot_{}.jpg'.format(self.object_state.motion), frame)

            if self.object_state.motion == 0:
                save_snapshot = False



class Phase1Detector(Thread):
    MAX_LENGTH = 30 # seconds
    MAX_SILENCE = 3 # seconds
    RATE = 10 # each N frame

    stop = False
    camera = {}
    detector = None
    detection_start = 0
    silence_start = 0
    queue = None
    response_queue = None
    current_frame_index = 0
    out = None
    response_reader = None
    write_queue = None
    clip_writer = None

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, camera=None, out_queue=None):
        super(Phase1Detector, self).__init__(group=group, target=target, name=name)
        self.camera = camera
        self.out_queue = out_queue
        self.stop = False
        self.response_queue = queue.Queue()

        self.write_queue = queue.Queue()
        self.clip_writer = ClipWriter(camera=camera, write_queue=self.write_queue)
        self.clip_writer.start()

        self.response_reader = ResponseReader(response_queue=self.response_queue, clip_writer=self.clip_writer)
        self.response_reader.start()

    def run(self):
        log("[phase1] [{}] Starting detector".format(self.camera["name"]))
        ctx = zmq.Context()
        s = ctx.socket(zmq.SUB)
        s.connect("ipc:///tmp/streamer_%s" % self.camera["name"])
        s.setsockopt(zmq.SUBSCRIBE, b"")
        s.setsockopt(zmq.RCVTIMEO, 2000)

        prev_time = 0
        while not self.stop:
            try:
                msg = s.recv()
            except:
                continue

            A = np.frombuffer(msg, dtype=self.camera["meta"]["dtype"])
            frame = A.reshape(self.camera["meta"]['shape'])
            del A

            if self.current_frame_index % self.RATE == 0:
                self.out_queue.put((self.response_queue, frame, time.time()))

            if self.clip_writer.startx == True:
                self.write_queue.put(frame)

            self.current_frame_index += 1

        s.close()
        self.response_reader.stop = True
        self.response_queue.join()


class SplitWriter:
    def __init__(self, split_size=30,
                 pub_address="tcp://127.0.0.1:5557",
                 directory='/tmp',
                 split_history=2,
                 split_prefix='split',
                 fps=30):
        self.pub_address = pub_address
        self.split_size = split_size
        self.directory = directory
        self.split_history = split_history
        self.fps = fps
        self.split_prefix = split_prefix

        self.zmq_context = zmq.Context()
        self.src = self.zmq_context.socket(zmq.SUB)
        self.src.connect(self.pub_address)
        self.src.setsockopt_string(zmq.SUBSCRIBE, "")

        self.current_split = 0
        self.new_split = 0
        self.writer = None
        self.last_frame_delay = 0
        self.remote_frameno = 0
        self.frameno = 0

    def _gen_split_name(self):
        return os.path.join(self.directory, self.split_prefix + '.%d.%d.avi' % (self.current_split, self.split_size))

    def _start_new_split(self, frame):
        self.current_split = int(time.time())
        self.new_split = self.current_split + self.split_size
        if self.writer:
            self.writer.release()
        self.writer = cv2.VideoWriter(self._gen_split_name(),
                                      cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                                      self.fps, (frame.shape[1], frame.shape[0]))
        print("++", self._gen_split_name(),
              "Last_Frame_Delay", self.last_frame_delay,
              "Frame_Delta", self.remote_frameno - self.frameno)
        self._clear_old_splits()



    def _clear_old_splits(self):
        for f in glob.glob(os.path.join(self.directory, self.split_prefix + '.*.*.avi')):
            parts = f.split('.')
            ts = int(parts[-3])
            if ts < time.time() - self.split_size * self.split_history:
                print("--", f)
                os.unlink(f)


    def write(self):
        frame = self.src.recv_pyobj()
        meta = self.src.recv_pyobj()
        now = time.time()
        self.frameno += 1
        self.remote_frameno = meta['frameno']
        self.last_frame_delay = int((now - meta['ts']) * 1000)
        if now > self.new_split:
            self._start_new_split(frame)
        self.writer.write(frame)

    def release(self):
        self.writer.release()
        self.src.close()
        self.zmq_context.destroy()
