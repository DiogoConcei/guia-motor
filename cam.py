import cv2
from threading import Thread, Lock


class AccessError(Exception):
    pass


class Cam(Thread):
    def __init__(self, cam_port=0):
        super().__init__()
        self.cam: cv2.VideoCapture
        self.cam_port = cam_port
        self.start_cam()
        self.ret, self.frame = False, None
        self.stopped = False
        self.lock = Lock()
        self._new_frame = False

    def start_cam(self):
        try:
            temp_cam = cv2.VideoCapture(self.cam_port)

            if not temp_cam.isOpened():
                raise AccessError("Falha ao abrir webcam na entrada 0")

            self.cam = temp_cam
        except AccessError:
            temp_cam = cv2.VideoCapture(1)

            if not temp_cam.isOpened():
                raise AccessError("Falha ao abrir webcam na entrada 1")

            self.cam = temp_cam

    def run(self):
        while not self.stopped:
            with self.lock:
                self.ret, self.frame = self.cam.read()

                if self.ret:
                    self._new_frame = True
                else:
                    self._new_frame = False

    def read(self):
        with self.lock:
            self._new_frame = False
            return self.ret, self.frame

    def stop(self):
        self.stopped = True
        self.join()
        self.cam.release()
