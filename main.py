import process as proc
import filter_process as fp
import numpy as np
import cv2
import multiprocessing as mp



# coding:utf-8
from kivy.logger import Logger
from kivy.app import App
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty, NumericProperty
import cv2


class KivyImageSink(Image):
    filter_pipe = ObjectProperty(None)
    fps = NumericProperty(None)

    def __init__(self, **kwargs):
        super(KivyImageSink, self).__init__(**kwargs)

    def on_fps(self, instance, value):
        if hasattr(self,'clock_event'):
            self.clock_event.cancel()
        self.clock_event = Clock.schedule_interval(self.update, 1.0 / value)

    def update(self, dt):
        for frame in fp.recv_frames(self.filter_pipe):
            # convert it to texture
            buf1 = cv2.flip(frame, 0)
            buf = buf1.tostring()
            image_texture = Texture.create(
                size=(frame.shape[1], frame.shape[0]), colorfmt='luminance')
            image_texture.blit_buffer(buf, colorfmt='luminance', bufferfmt='ubyte')
            # display image from the texture
            self.texture = image_texture

class CamApp(App):
    def __init__(self, *args, **kwargs):
        super(CamApp, self).__init__(**kwargs)
        recv, send = mp.Pipe(False)
        self.capture = fp.capture()
        self.capture_pipe = recv
        self.capture.send_pipe = send
        self.capture.start()

        self.filters = [fp.interpolate(2)]
        self.filter_pipe = proc.process_chain(self.capture_pipe,self.filters)

    def snapshot(self):
        last_pipe = self.filter_pipe
        for f in reversed(self.filters):
            Logger.info("stopping "+str(f))
            f.cont=0
            for frame in fp.recv_frames(last_pipe):
                Logger.info("dumping frame")
                pass
            f.join()
            last_pipe = f.recv_pipe

        write = fp.write() 
        snap_filters = [fp.interpolate(32)]
        write.recv_pipe = proc.process_chain(self.capture_pipe,snap_filters)
        write.start("test.png")
        write.join()

        last_pipe = write.recv_pipe
        for f in reversed(snap_filters):
            Logger.info("stopping "+str(f))
            f.cont=0
            for frame in fp.recv_frames(last_pipe):
                Logger.info("dumping frame")
                pass
            f.join()
            last_pipe = f.recv_pipe
        

        for f in self.filters:
            Logger.info("starting "+str(f))
            f.start()
        
    def on_stop(self):
        last_pipe = self.filter_pipe
        for f in reversed([self.capture]+self.filters):
            f.cont=0
            for frame in fp.recv_frames(last_pipe):
                pass
            f.join()
            last_pipe = f.recv_pipe


if __name__ == '__main__':
    CamApp().run()

