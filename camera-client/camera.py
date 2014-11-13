#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import picamera
import base64
import sys, io
import threading
import websocket

def create_camera(width, height, fps):
    """カメラを適当に設定して作るファクトリ
    """
    camera = picamera.PiCamera()
    camera.resolution = (width, height)
    camera.framerate = fps
    camera.stream = io.BytesIO()    #ストリームIO
    camera.vflip = True             #垂直反転
    camera.hflip = True             #水平反転
    time.sleep(2)
    return camera

class CameraThread():

    def __init__(self, width=640, height=480, fps=10, quality=85):
        print "initializing camera..."
        self.stop_event = threading.Event()
        self.camera = create_camera(width,height,fps)
        print "done"

        self.quality = quality
        self.send_thread = threading.Thread(target=self.loop)
        self.send_thread.setDaemon(True)

    def start(self, ws):
        self.ws = ws
        self.send_thread.start()

    def stop(self):
        self.stop_event.set()

    def loop(self):
        for foo in self.camera.capture_continuous(\
                self.camera.stream,\
                "jpeg", use_video_port=True, quality=self.quality):
            self.camera.stream.seek(0)
            #データの送信．
            #鯖側でバイナリでの受信の仕方がわからんかったのでbase64にエンコードした．
            self.ws.send(base64.b64encode(self.camera.stream.read()))
            self.camera.stream.seek(0)
            self.camera.stream.truncate()
            if self.stop_event.is_set():
                break

ct = CameraThread(width=320, height=240, fps=5, quality=20)

def on_message(ws, msg):
    pass

def on_error(ws, error):
    print error

def on_open(ws):
    print "### open ###"
    ct.start(ws)

def on_close(ws):
    print "### close ###"
    ct.stop()

if __name__ == '__main__':
    server_adress = "localhost:5000"
    if len(sys.argv) == 2:
        server_adress = sys.argv[1]

    # websocket.enableTrace(True)
    while True:
        try:
            ws = websocket.WebSocketApp("ws://" + server_adress,
                                      on_message = on_message,
                                      on_error = on_error,
                                      on_close = on_close)
            ws.on_open = on_open
            ws.run_forever()
            time.sleep(1)       #再接続の試行までのインターバル
            time.sleep(1)       #再接続の試行までのインターバル
        except KeyboardInterrupt:
            print "abort"
            break
