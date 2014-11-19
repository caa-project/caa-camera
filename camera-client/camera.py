#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import gflags
import time
import picamera
import sys
import websocket

FLAGS = gflags.FLAGS

gflags.DEFINE_string("server", None, "e.g. ws://localhost:8000/push")
gflags.DEFINE_integer("width", 320, "Width of movie.")
gflags.DEFINE_integer("height", 240, "Height of movie.")
gflags.DEFINE_integer("fps", 10, "fps")
gflags.DEFINE_integer("quality", 20, "Quality")
gflags.DEFINE_bool("vflip", True, "Virtical flip")
gflags.DEFINE_bool("hflip", True, "Horizontal flip")


def create_camera(width, height, vflip, hflip):
    """カメラを適当に設定して作るファクトリ
    """
    camera = picamera.PiCamera()
    camera.resolution = (width, height)
    camera.vflip = vflip            # 垂直反転
    camera.hflip = hflip            # 水平反転
    time.sleep(2)
    return camera


def camera_streaming(ws, camera):
    stream = io.BytesIO()
    SPF = 1.0 / FLAGS.fps   # second per frame
    for foo in camera.capture_continuous(
            stream, "jpeg", use_video_port=True, quality=FLAGS.quality):
        stream.seek(0)
        ws.send_binary(stream.read())
        stream.seek(0)
        stream.truncate()
        time.sleep(SPF)


def main(argv):
    argv = gflags.FLAGS(argv)

    # websocket.enableTrace(True)
    while True:
        try:
            ws = websocket.create_connection(FLAGS.server)
            camera = create_camera(FLAGS.width, FLAGS.height, FLAGS.fps,
                                   FLAGS.vflip, FLAGS.hflip)
            camera_streaming(ws, camera)

        except KeyboardInterrupt:
            print "abort"
            break
        except Exception as e:
            print str(e)
            time.sleep(1)       # 再接続の試行までのインターバル


if __name__ == '__main__':
    main(sys.argv)
