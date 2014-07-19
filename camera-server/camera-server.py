#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, io, time, base64, threading
import tornado.web
import tornado.websocket
import tornado.httpserver

class HttpHandler(tornado.web.RequestHandler):
    def initialize(self):
        pass

    def get(self):
        self.render("./html/index.html") 

class WSHandler(tornado.websocket.WebSocketHandler):
    def initialize(self, img_list):
        self.state = True
        self.img_list = img_list

    def open(self):
        t = threading.Thread(target=self.loop)    #送信スレッドの作成
        t.setDaemon(True)
        t.start()

    def loop(self):
        """バイナリをほげほげするスレッド"""
        i = 0
        while self.state:
            if self.img_list:
                self.write_message(self.img_list.pop(), binary=True)
            time.sleep(0.05)

    def on_close(self):
        self.state = False     #映像送信のループを終了させる
        self.close()     #WebSocketセッションを閉じる
        print(self.request.remote_ip, ": connection closed")

class WSRecieveHandler(tornado.websocket.WebSocketHandler):
    def initialize(self, img_list):
        self.img_list = img_list

    def open(self):
        print(self.request.remote_ip, " : open")

    def on_message(self, msg):
        """base64で映像を受け取る
        """
        print "recieve"
        self.img_list.append(base64.b64decode(msg))

    def on_close(self):
        self.close()
        print(self.request.remote_ip, ": connection closed")

def main():
    print("start!")
    
    img_list = [open("hoge.jpg","rb").read()]

    app = tornado.web.Application([
        (r"/", HttpHandler),            #最初のアクセスを受け付けるHTTPハンドラ
        (r"/echo", WSHandler, dict(img_list=img_list)),          #送信のハンドラ
        (r"/recieve", WSRecieveHandler,dict(img_list=img_list)),  #受け取る
    ])
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(8000)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
