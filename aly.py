from flask import Flask, render_template_string, request
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# قاعدة بيانات وهمية لحفظ حسابات المستخدمين
USERS_DB = {
    "المهندس": "1234"
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>👑 شات المهندس الاحترافي 👑</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        html, body { height: 100%; background: #0f172a; color: #e2e8f0; font-family: sans-serif; overflow: hidden; }
        
        #login-screen { display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; padding: 20px; background: #0f172a; }
        .login-card { background: #1e293b; padding: 30px 25px; border-radius: 16px; width: 100%; max-width: 380px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); text-align: center; border: 1px solid #334155; }
        .login-card h1 { color: #FFD700; margin-bottom: 20px; font-size: 1.6rem; text-shadow: 0 0 10px rgba(255,215,0,0.2); }
        .login-card input { width: 100%; padding: 14px; margin-bottom: 12px; border: 1px solid #475569; border-radius: 8px; background: #0f172a; color: white; font-size: 1rem; outline: none; text-align: center; }
        .login-card button { width: 100%; padding: 14px; background: #0284c7; color: white; border: none; border-radius: 8px; font-weight: bold; font-size: 1rem; cursor: pointer; transition: background 0.2s; }
        .login-card button:hover { background: #0369a1; }
        #login-error { color: #ef4444; font-size: 0.9rem; margin-top: 10px; display: none; }

        #chat-screen { display: none; flex-direction: column; height: 100%; }
        
        #header { background: #1e293b; padding: 15px; text-align: center; border-bottom: 2px solid #334155; flex-shrink: 0; display: flex; justify-content: space-between; align-items: center; }
        #header h2 { margin: 0; font-size: 1.2rem; color: #FFD700; flex: 1; text-align: center; }
        .user-tag { background: #334155; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; color: #38bdf8; max-width: 100px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        
        #chat-window { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 10px; }
        
        .msg-box { padding: 10px 14px; border-radius: 12px; max-width: 80%; font-size: 0.95rem; line-height: 1.4; word-break: break-word; animation: fadeIn 0.2s ease-out; }
        .msg-normal { background: #1e293b; align-self: flex-start; border-top-right-radius: 2px; }
        .msg-owner { background: linear-gradient(135deg, #1e293b 0%, #2e2612 100%); border: 1px solid #FFD700; align-self: flex-start; border-top-right-radius: 2px; }
        
        .owner-gold { color: #FFD700; font-weight: bold; text-shadow: 0 0 5px #FFD700; }
        .user-name { color: #38bdf8; font-weight: bold; }
        
        #interactive-area { background: #1e293b; border-top: 2px solid #334155; flex-shrink: 0; }
        #emoji-bar { padding: 8px 12px; display: flex; gap: 14px; background: #111827; overflow-x: auto; font-size: 1.2rem; border-bottom: 1px solid #334155; }
        .emoji-btn { cursor: pointer; user-select: none; }
        
        #input-area { padding: 12px; display: flex; gap: 10px; align-items: center; }
        #msg { flex: 1; padding: 14px; border: 1px solid #475569; border-radius: 8px; background: #0f172a; color: white; font-size: 1rem; outline: none; }
        #send-btn { background: #0284c7; color: white; border: none; padding: 14px 24px; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 1rem; flex-shrink: 0; }
        
        @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>

    <div id="login-screen">
        <div class="login-card">
            <h1>👑 تسجيل دخول الشات </h1>
            <input type="text" id="login-user" placeholder="أدخل اسم المستخدم..." autocomplete="off">
            <input type="password" id="login-pass" placeholder="أدخل كلمة المرور..." autocomplete="off">
            <button onclick="loginOrRegister()">دخول / تسجيل جديد</button>
            <div id="login-error">خطأ في كلمة المرور للاسم المحمي!</div>
        </div>
    </div>

    <div id="chat-screen">
        <div id="header">
            <div style="width:60px;"></div>
            <h2>👑 شات المهندس 👑</h2>
            <div class="user-tag" id="my-display-name">...</div>
        </div>
        
        <div id="chat-window"></div>
        
        <div id="interactive-area">
            <div id="emoji-bar">
                <span class="emoji-btn" onclick="addEmoji('👑')">👑</span>
                <span class="emoji-btn" onclick="addEmoji('💻')">💻</span>
                <span class="emoji-btn" onclick="addEmoji('🔥')">🔥</span>
                <span class="emoji-btn" onclick="addEmoji('😂')">😂</span>
                <span class="emoji-btn" onclick="addEmoji('👍')">👍</span>
                <span class="emoji-btn" onclick="addEmoji('🌹')">🌹</span>
            </div>
            <div id="input-area">
                <input id="msg" placeholder="اكتب رسالتك هنا..." autocomplete="off">
                <button id="send-btn" onclick="send()">إرسال</button>
            </div>
        </div>
    </div>

    <script src="https://cloudflare.com"></script>
    <script>
        const socket = io();
        let currentUsername = "";

        document.getElementById('msg').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') send();
        });

        document.getElementById('login-pass').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') loginOrRegister();
        });

        function loginOrRegister() {
            const userField = document.getElementById('login-user');
            const passField = document.getElementById('login-pass');
            let username = userField.value.trim();
            let password = passField.value.trim();

            if(username === "" || password === "") {
                alert("الرجاء كتابة الاسم وكلمة المرور أولاً!");
                return;
            }
            socket.emit('verify_login', { username: username, password: password });
        }

        socket.on('login_response', function(data) {
            const errorDiv = document.getElementById('login-error');
            if(data.success) {
                currentUsername = data.username;
                document.getElementById('my-display-name').textContent = currentUsername;
                document.getElementById('login-screen').style.display = "none";
                document.getElementById('chat-screen').style.display = "flex";
                document.getElementById('msg').focus();
            } else {
                errorDiv.textContent = data.message;
                errorDiv.style.display = "block";
            }
        });

        function addEmoji(emoji) {
            const msgInput = document.getElementById('msg');
            msgInput.value += emoji;
            msgInput.focus();
        }
        
        function send() {
            let msgInput = document.getElementById('msg');
            let msg = msgInput.value.trim();
            if (msg === '' || currentUsername === '') return;
            socket.emit('message', {username: currentUsername, msg: msg});
            msgInput.value = '';
            msgInput.focus();
        }
        
        socket.on('message', function(data) {
            let chat = document.getElementById('chat-window');
            let div = document.createElement('div');
            if(data.is_owner) {
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

@socketio.on('verify_login')
def handle_login(data):
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if username == "المهندس" and password != USERS_DB["المهندس"]:
        socketio.emit('login_response', {'success': False, 'message': 'عذراً، كلمة مرور المالك غير صحيحة!'}, room=request.sid)
        return
        
    if username not in USERS_DB:
        USERS_DB[username] = password
        
    if USERS_DB[username] == password:
        socketio.emit('login_response', {'success': True, 'username': username}, room=request.sid)
    else:
        socketio.emit('login_response', {'success': False, 'message': 'اسم المستخدم مسجل بكلمة مرور أخرى!'}, room=request.sid)

@socketio.on('message')
def handle_message(data):
    if data.get('username') == "المهندس":
        data['is_owner'] = True
    else:
        data['is_owner'] = False
    socketio.emit('message', data)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
