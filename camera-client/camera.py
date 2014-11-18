#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import gflags
import time
import picamera
import base64
import sys
import threading
import websocket

FLAGS = gflags.FLAGS

gflags.DEFINE_string("server", None, "e.g. ws://localhost:8000/push")
gflags.DEFINE_integer("width", 320, "Width of movie.")
gflags.DEFINE_integer("height", 240, "Height of movie.")
gflags.DEFINE_integer("fps", 10, "fps")
gflags.DEFINE_integer("quality", 20, "Quality")


def create_camera(width, height, fps):
    """カメラを適当に設定して作るファクトリ
    """
    camera = picamera.PiCamera()
    camera.resolution = (width, height)
    camera.framerate = fps
    camera.stream = io.BytesIO()    # ストリームIO
    camera.vflip = True             # 垂直反転
    camera.hflip = True             # 水平反転
    time.sleep(2)
    return camera


class CameraThread():

    def __init__(self, width, height, fps, quality):
        print "initializing camera..."
        self.stop_event = threading.Event()
        self.camera = create_camera(width, height, fps)
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
        for foo in self.camera.capture_continuous(
                self.camera.stream,
                "jpeg", use_video_port=True, quality=self.quality):
            self.camera.stream.seek(0)
            # データの送信．
            # 鯖側でバイナリでの受信の仕方がわからんかったので
            # base64にエンコードした．
            self.ws.send(base64.b64encode(self.camera.stream.read()))
            self.camera.stream.seek(0)
            self.camera.stream.truncate()
            if self.stop_event.is_set():
                break

ct = CameraThread(width=FLAGS.width, height=FLAGS.height, fps=FLAGS.fps,
                  quality=FLAGS.quality)


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


def main(argv):
    argv = gflags.FLAGS(argv)

    # websocket.enableTrace(True)
    while True:
        try:
            ws = websocket.WebSocketApp(FLAGS.server,
                                        on_message=on_message,
                                        on_error=on_error,
                                        on_close=on_close)
            ws.on_open = on_open
            ws.run_forever()
            time.sleep(1)       # 再接続の試行までのインターバル
        except KeyboardInterrupt:
            print "abort"
            break


if __name__ == '__main__':
    main(sys.argv)
