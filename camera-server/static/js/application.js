var INDEX = "";
var UI_SERVER_URL = "";
function setIndex(s) {
  INDEX = s;
}
function setUIServerUrl(s) {
  UI_SERVER_URL = s;
}

/**
 * Prepare WebSocket to receive image buffers.
 */
function prepareWebSocket() {
  // アクセスしてきたアドレス 例: hoge.com:12345
  var adress = location.href.match( /\/\/[^\/]+/ )[0].substr(2);

  var ws = new WebSocket("ws://" + adress + "/pop/" + INDEX); 
  ws.binaryType = 'arraybuffer';

  ws.onopen = function(){
    console.log("open!");
  };

  // 受信したバイナリをbase64にしてsrcに指定する
  ws.onmessage = function(e){
    var src = "data:image/jpeg;base64," + encode(new Uint8Array(e.data));
    $('#liveImg').attr('src', src);
  };

  window.onbeforeunload = function(){
    ws.close(1000);
  };
}

/**
 * QR code
 */
function getQRCode() {
  var url = "/url?index=" + INDEX;
  $.ajax({
    type: 'POST',
    url: url,
    data: {},
    success: function(data) {
      $('#qrCanvas').empty();
      if (data['success']) {
        var url = data['url'];
        var qrcode = "https://chart.googleapis.com/chart?chs=300x300&cht=qr&chl=" + url;
        $('#qrCanvas').append(
          $('<h1>').html('↓読み取ってね！'),
          $('<img>').attr('src', qrcode));
      } else {
        $('#qrCanvas').append($('<h1>').html('準備中'));
        console.log(data['reason']);
      }
    }});
}


/**
 * base64 encode
 *
 * @param input {Uint8Array} binary
 */
function encode (input) {
    var keyStr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
    var output = "";
    var chr1, chr2, chr3, enc1, enc2, enc3, enc4;
    var i = 0;

    while (i < input.length) {
        chr1 = input[i++];
        chr2 = i < input.length ? input[i++] : Number.NaN; // Not sure if the index
        chr3 = i < input.length ? input[i++] : Number.NaN; // checks are needed here

        enc1 = chr1 >> 2;
        enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
        enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
        enc4 = chr3 & 63;

        if (isNaN(chr2)) {
            enc3 = enc4 = 64;
        } else if (isNaN(chr3)) {
            enc4 = 64;
        }
        output += keyStr.charAt(enc1) + keyStr.charAt(enc2) +
                  keyStr.charAt(enc3) + keyStr.charAt(enc4);
    }
    return output;
}


$(function() {
  prepareWebSocket();

  setInterval(getQRCode, 1000);
});
