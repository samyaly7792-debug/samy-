from flask import Flask, render_template_string
from flask_socketio import SocketIO

app = Flask(__name__)
# إعداد SocketIO مع منع تعارض أصول الطلبات وتوافق كامل مع gevent الموضح بصورتك
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# قوالب العرض معالجة بالكامل ومحمية من أخطاء الـ Syntax البرمجية
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>شات المهندس</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { height: 100vh; display: flex; flex-direction: column; background: #0f172a; color: #e2e8f0; font-family: sans-serif; overflow: hidden; }
        #header { background: #1e293b; padding: 12px; text-align: center; border-bottom: 2px solid #334155; }
        #header h2 { margin: 0; font-size: 1.3rem; color: #FFD700; text-shadow: 0 0 10px rgba(255,215,0,0.3); }
        #chat-window { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 10px; }
        .msg-box { padding: 10px 14px; border-radius: 12px; max-width: 85%; font-size: 0.95rem; line-height: 1.4; word-break: break-word; }
        .msg-normal { background: #1e293b; align-self: flex-start; border-top-right-radius: 2px; }
        .msg-owner { background: linear-gradient(135deg, #1e293b 0%, #2e2612 100%); border: 1px solid #FFD700; align-self: flex-start; border-top-right-radius: 2px; }
        .owner-gold { color: #FFD700; font-weight: bold; text-shadow: 0 0 5px #FFD700; }
        .user-name { color: #38bdf8; font-weight: bold; }
        #input-area { padding: 12px; background: #1e293b; display: flex; gap: 8px; border-top: 2px solid #334155; }
        #username { flex: 1; max-width: 100px; padding: 12px; border: 1px solid #475569; border-radius: 8px; background: #0f172a; color: white; font-size: 0.95rem; outline: none; }
        #msg { flex: 2; padding: 12px; border: 1px solid #475569; border-radius: 8px; background: #0f172a; color: white; font-size: 0.95rem; outline: none; }
        #send-btn { background: #0284c7; color: white; border: none; padding: 0 18px; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 0.95rem; }
    </style>
</head>
<body>
    <div id="header">
        <h2>👑 شات المهندس 👑</h2>
    </div>
    <div id="chat-window"></div>
    <div id="input-area">
        <input id="username" placeholder="الاسم..." autocomplete="off">
        <input id="msg" placeholder="اكتب رسالتك هنا..." autocomplete="off">
        <button id="send-btn" onclick="send()">إرسال</button>
    </div>
    <script src="https://cloudflare.com"></script>
    <script>
        const socket = io();
        document.getElementById('msg').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') send();
        });
        function send() {
            let userInput = document.getElementById('username');
            let msgInput = document.getElementById('msg');
            let user = userInput.value.trim() || "زائر";
            let msg = msgInput.value.trim();
            if (msg === '') return;
            socket.emit('message', {username: user, msg: msg});
            msgInput.value = '';
            msgInput.focus();
        }
        socket.on('message', function(data) {
            let chat = document.getElementById('chat-window');
            let div = document.createElement('div');
            if(data.is_owner || data.username === "المهندس") {
                div.className = "msg-box msg-owner";
                div.innerHTML = "<span class='owner-gold'>👑 " + data.username + ":</span> <span style='color: #fff;'>" + data.msg + "</span>";
            } else {
                div.className = "msg-box msg-normal";
                div.innerHTML = "<span class='user-name'>" + data.username + ":</span> <span style='color: #e2e8f0;'>" + data.msg + "</span>";
            }
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        });
    </script>
</body>
</html>"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@socketio.on('message')
def handle_message(data):
    if data.get('username') == "المهندس":
        data['is_owner'] = True
    else:
        data['is_owner'] = False
    socketio.emit('message', data)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
