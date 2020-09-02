from multiprocessing import Pipe, Value
from process import process
import numpy as np
import cv2

def recv_frames(recv_pipe):
    while recv_pipe.poll(0.04):
        buf = np.ndarray(shape=480*640, dtype=np.uint8)
        frame = np.ndarray(shape=(480,640), dtype=np.uint8, buffer=buf)
        idx = 0
        while idx < buf.nbytes:
            idx += recv_pipe.recv_bytes_into(buf, idx)
            if idx == 0:
                return
            yield frame

class frame_process(process):
    def recv(self):
        for frame in recv_frames(self.recv_pipe):
            yield frame

class capture(process):
    def run(self):
        cap = cv2.VideoCapture(0)
        while self.cont:
            ret, frame = cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            flat = np.ndarray(shape=480*640, dtype=np.uint8, buffer=gray.data)
            self.send(flat)
        #TODO: capture exception if recv is closed
        cap.release()

class show(frame_process):
    def send(self,data):
        self.send_pipe.send(data)
        
    def run(self):
        while self.cont:
            try:
                for frame in self.recv():
                    cv2.imshow('frame',frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key != 0xFF:
                        self.send(chr(key))
            except Exception as e:
                cv2.destroyAllWindows()
                break

class write(frame_process):
    def run(self,filename):
        while self.cont:
            for frame in self.recv():
                cv2.imwrite(filename,frame)
                self.cont = 0

        
class interpolate(frame_process):
    def __init__(self, size):
        self.__size = Value('i', size)
        super().__init__()

    @property
    def size(self):
        return self.__size.value

    @size.setter
    def size(self, value):
        self.__size.value = value

    def run(self):
        frames = []
        while self.cont:
            size = self.size
            for frame in self.recv():
                frames.append(frame)
                while len(frames) > size:
                    frames.pop(0)
    
            if len(frames) == size:
                out = frames[0]/size
                n=0
                for frame in frames[1:]:
                    n+=1
                    out += frame/size
                out = out.astype(np.uint8)
                flat = np.ndarray(shape=480*640, dtype=np.uint8, buffer=out.data)
                self.send(flat)
        print("exiting")
        

