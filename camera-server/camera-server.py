#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, io, time, base64, threading
import tornado.web
import tornado.websocket
import tornado.httpserver

class HttpHandler(tornado.web.RequestHandler):
    """HTTPのハンドラ
    
    /に対応．普通にindex.htmlを返す．
    """
    def initialize(self):
        pass

    def get(self):
        self.render("./html/index.html") 

class WSSendHandler(tornado.websocket.WebSocketHandler):
    """画像の送信を担うWebSocketのハンドラ

    /echo に対応．

    コンストラクタの引数にとるimg_listはスタックとして用い，受信のハンドラである
    WSRecieveHandlerと同じものを参照している．受信側で画像を積んだらそいつを
    loop関数の中でpopしてクライアントを送信する．
    """

    def initialize(self, img_list):
        """コンストラクタ
        
        @param img_list 画像のリスト

        @memo リストをスタックとして用いている．これをただのオブジェクトとする
        と，受信のハンドラで代入したときにこちらのオブジェクトと参照している先が
        異なってしまうので，入れ物を用意する必要があり，とりあえずリストにした．
        """
        self.state = True
        self.img_list = img_list

    def open(self):
        t = threading.Thread(target=self.loop)    #送信スレッドの作成
        t.setDaemon(True)
        t.start()

    def loop(self):
        """メインスレッドと非同期でクライアントに画像を送りつける"""
        while self.state:
            if self.img_list:
                self.write_message(self.img_list.pop(), binary=True)
            time.sleep(0.05)

    def on_close(self):
        self.state = False      #映像送信のループを終了させる
        self.close()            #WebSocketセッションを閉じる
        print("open: " + self.request.remote_ip)

class WSRecieveHandler(tornado.websocket.WebSocketHandler):
    """Piからの画像を受け取るハンドラ

    /recieve に対応．

    画像はbase64でエンコードされて送られてくる（on_messageでバイナリで
    受け取る方法がわからなかったため）．受信したらデコードしてWSSendHandlerと
    共通のスタックへ積んであげる．
    """
    def initialize(self, img_list):
        self.img_list = img_list

    def open(self):
        print("open: " + self.request.remote_ip)

    def on_message(self, msg):
        """base64で映像を受け取ってデコードしてスタックへ入れる"""
        self.img_list.append(base64.b64decode(msg))

    def on_close(self):
        self.close()
        print(self.request.remote_ip, ": connection closed")

if __name__ == "__main__":
    print("start!")
    
    img_list = [open("./static/img/default.jpg","rb").read()]   #初期画像の用意

    #ハンドラの登録
    #２つのハンドラに同じimg_listを渡しているのに注目！
    app = tornado.web.Application([
        (r"/", HttpHandler),
        (r"/echo", WSSendHandler, dict(img_list=img_list)),
        (r"/recieve", WSRecieveHandler,dict(img_list=img_list)),
    ])
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(8000)
    tornado.ioloop.IOLoop.instance().start()
