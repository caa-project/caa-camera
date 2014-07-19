#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import picamera
import sys, io
import threading
import tornado.web
import tornado.websocket
import tornado.httpserver

WIDTH = 320
HEIGHT = 240
FPS = 3
class HttpHandler(tornado.web.RequestHandler):
    def initialize(self):
            pass

    def get(self):
        self.render("./index.html")  #最初のHTTPアクセスを受け付け、WebSocket接続を確立させるスクリプトが入ったindex.htmlを返す

class WSHandler(tornado.websocket.WebSocketHandler):
    def initialize(self, camera):
        self.camera = camera
        self.state = True

    def open(self):
        t = threading.Thread(target=self.loop)    #撮影&送信スレッドの作成
        t.setDaemon(True)
        t.start()

    def loop(self):
        for foo in self.camera.capture_continuous(self.camera.stream, "jpeg", use_video_port=True):
            self.camera.stream.seek(0)
            self.write_message(self.camera.stream.read(), binary=True)
            self.camera.stream.seek(0)
            self.camera.stream.truncate()
            if not self.state:
                break

    def on_close(self):
        self.state = False     #映像送信のループを終了させる
        self.close()     #WebSocketセッションを閉じる
        print(self.request.remote_ip, ": connection closed")

def piCamera():
    camera = picamera.PiCamera()
    camera.resolution = (WIDTH, HEIGHT)
    camera.framerate = FPS
    camera.stream = io.BytesIO()     #ストリームIO
    time.sleep(2)        #カメラ初期化
    return camera

def main():
    camera = piCamera()
    print("complete initialization")
    app = tornado.web.Application([
        (r"/", HttpHandler),                     #最初のアクセスを受け付けるHTTPハンドラ
        (r"/camera", WSHandler, dict(camera=camera)),   #WebSocket接続を待ち受けるハンドラ
    ])
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(8000)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
