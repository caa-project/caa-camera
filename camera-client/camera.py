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


def camera_streaming(ws, camera, fps):
    """Start sending binary of jpeg images."""
    stream = io.BytesIO()
    SPF = 1.0 / fps         # second per frame
    frames_count = 0        # how many frames are captured (including skips)
    while True:
        frames_count += 1
        start_time = time.time()

        # campure and send start
        camera.capture(stream, "jpeg", use_video_port=True,
                       quality=FLAGS.quality)
        stream.seek(0)
        ws.send_binary(stream.read())
        stream.seek(0)
        stream.truncate()
        # campure and send end

        end_time = time.time()
        # shorten sleeping seconds
        sec = SPF - (end_time - start_time)
        sec = sec if sec > 0 else SPF
        time.sleep(sec)


def main(argv):
    argv = gflags.FLAGS(argv)

    # websocket.enableTrace(True)
    while True:
        try:
            ws = websocket.create_connection(FLAGS.server)
            print "Prepare camera"
            camera = create_camera(FLAGS.width, FLAGS.height,
                                   FLAGS.vflip, FLAGS.hflip)
            print "Start streaming"
            camera_streaming(ws, camera, FLAGS.fps)

        except KeyboardInterrupt:
            print "abort"
            break
        except Exception as e:
            print str(e)
            time.sleep(1)       # 再接続の試行までのインターバル


if __name__ == '__main__':
    main(sys.argv)
