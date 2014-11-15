#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import gflags
import os
import sys
import threading
import tornado.web
import tornado.websocket
import tornado.httpserver

gflags.DEFINE_integer("port", None, "port the server listen on")
gflags.DEFINE_string("ui_server_url", "http://localhost:5001", "ui_server_url")

FLAGS = gflags.FLAGS


class PopHandlerHolder(object):
    """Indexに対応するPopHandlerを保存する．

    PushHandler.on_messageでこのholderを通じてwrite_messageする．
    """

    def __init__(self):
        self._handlers = dict()
        self._lock = threading.Lock()
        with open("./static/img/default.jpg", "rb") as f:
            self._default_image = f.read()

    @staticmethod
    def instance():
        if not hasattr(PopHandlerHolder, "_instance"):
            PopHandlerHolder._instance = PopHandlerHolder()
        return PopHandlerHolder._instance

    def get_handler(self, index):
        if index in self._handlers:
            return self._handlers[index]
        return None

    def set_handler(self, index, handler):
        self._handlers[index] = handler

    def write_message(self, index, buf, binary=False):
        handler = self.get_handler(index)
        if handler:
            handler.write_message(buf, binary=binary)

    def write_default(self, index):
        self.write_message(index, self._default_image, binary=True)


class HttpHandler(tornado.web.RequestHandler):
    """HTTPのハンドラ

    /watchに対応．普通にindex.htmlを返す．
    """
    def initialize(self):
        pass

    def get(self, index):
        self.render("index.html",
                    index=index, ui_server_url=FLAGS.ui_server_url)


class WSPopHandler(tornado.websocket.WebSocketHandler):
    """ブラウザへの画像の送信

    /popに対応．
    """

    def initialize(self):
        self.state = True
        self.index = None

    def open(self, index):
        print "pop:", index
        PopHandlerHolder.instance().set_handler(index, self)

    def on_close(self):
        # 映像送信のループを終了させる
        self.state = False
        self.close()
        print("close: " + self.request.remote_ip)


class WSPushHandler(tornado.websocket.WebSocketHandler):
    """Piからの画像を受け取るハンドラ

    /push に対応．

    画像はbase64でエンコードされて送られてくる（on_messageでバイナリで
    受け取る方法がわからなかったため）．
    """
    def initialize(self):
        self.index = None
        self.pop_holder = PopHandlerHolder.instance()

    def open(self, index):
        print("open: " + self.request.remote_ip)
        self.index = index

    def on_message(self, msg):
        buf = base64.b64decode(msg)
        self.pop_holder.write_message(self.index, buf, binary=True)

    def on_close(self):
        self.close()
        self.pop_holder.write_default()
        print(self.request.remote_ip, ": connection closed")


def main(argv):
    argv = gflags.FLAGS(argv)
    print("start!")

    # ハンドラの登録
    # ２つのハンドラに同じimg_listを渡しているのに注目！
    handlers = [
        (r"/watch/([0-9a-zA-Z]+)", HttpHandler),
        (r"/pop/([0-9a-zA-Z]+)", WSPopHandler),
        (r"/push/([0-9a-zA-Z]+)", WSPushHandler),
    ]
    settings = dict(
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),)
    app = tornado.web.Application(handlers, **settings)
    http_server = tornado.httpserver.HTTPServer(app)
    if FLAGS.port:
        port = FLAGS.port
    else:
        port = int(os.environ.get("PORT", 5000))
    print port
    http_server.listen(port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main(sys.argv)
