from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'samy_king_final_2026'
socketio = SocketIO(app, cors_allowed_origins="*")

# Database in memory: {nickname: {"password": password, "avatar": avatar_url}}
registered_users = {}

# Active sessions: {socket_id: {"name": nickname, "avatar": avatar_url, "is_admin": Boolean}}
active_sessions = {}

html_template = """
<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>شات المهندس</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        html, body { height: 100%; overflow: hidden; background-color: #121212; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #e0e0e0; direction: rtl; }
    import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
    
        #chat-container { display: flex; flex-direction: column; height: 100%; max-width: 600px; margin: 0 auto; background: #1e1e1e; border-left: 1px solid #2d2d2d; border-right: 1px solid #2d2d2d; position: relative; }
        
        #header { background: #252525; padding: 12px; text-align: center; font-weight: bold; font-size: 1.2rem; border-bottom: 1px solid #2d2d2d; color: #0084ff; flex-shrink: 0; }
        #users-bar { background: #1a1a1a; padding: 8px; display: flex; gap: 10px; overflow-x: auto; border-bottom: 1px solid #2d2d2d; min-height: 55px; align-items: center; flex-shrink: 0; }
        .user-badge { display: flex; flex-direction: column; align-items: center; font-size: 0.7rem; min-width: 50px; color: #aaa; position: relative; }
        .user-badge img { width: 32px; height: 32px; border-radius: 50%; border: 2px solid #0084ff; object-fit: cover; }
        .king-badge { border-color: #ffcc00 !important; }
        
        .kick-btn { display: none; position: absolute; top: -5px; right: -5px; background: #ff3b30; color: white; border: none; border-radius: 50%; width: 18px; height: 18px; font-size: 11px; cursor: pointer; text-align: center; line-height: 16px; font-weight: bold; z-index: 10; }
        .is-admin .kick-btn { display: block !important; }
        
        #messages { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; -webkit-overflow-scrolling: touch; }
        
        .msg-wrapper { display: flex; gap: 8px; align-items: flex-end; width: 100%; margin-bottom: 2px; }
        .msg-wrapper.me { flex-direction: row-reverse; }
        .avatar-chat { width: 35px; height: 35px; border-radius: 50%; object-fit: cover; }
        
        .msg { padding: 10px 14px; border-radius: 18px; max-width: 75%; word-wrap: break-word; font-size: 0.95rem; box-shadow: 0 1px 3px rgba(0,0,0,0.15); display: flex; flex-direction: column; }
        .others { background-color: #2d2d2d; color: #fff; border-bottom-right-radius: 3px; text-align: right; }
        .my-msg { background-color: #0084ff; color: #fff; border-bottom-left-radius: 3px; text-align: right; }
        
        .sender-name { font-size: 0.78rem; color: #ffcc00; margin-bottom: 4px; display: block; font-weight: bold; }
        .sender-name.normal { color: #0084ff; }
        
        .system { background-color: rgba(255,255,255,0.06); align-self: center; font-size: 0.75rem; color: #aaa; border-radius: 8px; padding: 4px 10px; margin: 5px 0; text-align: center; max-width: 90%; }
        
        #input-container { display: flex; padding: 10px; border-top: 1px solid #2d2d2d; background: #1e1e1e; flex-shrink: 0; padding-bottom: calc(10px + env(safe-area-inset-bottom)); }
        #message-input { flex: 1; padding: 12px 16px; border: 1px solid #333; border-radius: 25px; outline: none; font-size: 1rem; background: #252525; color: #fff; }
        #send-btn { background-color: #0084ff; color: white; border: none; padding: 0 22px; margin-right: 8px; border-radius: 25px; cursor: pointer; font-size: 1rem; font-weight: bold; transition: background 0.2s; }
        #send-btn:active { background-color: #0066cc; }
    </style>
    <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
</head>
<body>
    <div id="chat-container">
        <div id="header">🛠️ شات المهندس 🛠️</div>
        <div id="users-bar">
            <span style="font-size:0.8rem; color:#666; margin-left:5px;">المتصلون:</span>
        </div>
        
        <div id="messages"></div>
        
        <div id="input-container">
            <input type="text" id="message-input" placeholder="اكتب رسالتك هنا..." autocomplete="off">
            <button id="send-btn">إرسال</button>
        </div>
    </div>

    <script>
        const socket = io();
        let myNickname = localStorage.getItem('samy_chat_name');
        let myPassword = localStorage.getItem('samy_chat_pass');
        let loginTime = localStorage.getItem('samy_chat_time');
        let isAdmin = false;

        const THREE_DAYS = 3 * 24 * 60 * 60 * 1000;
        const now = new Date().getTime();

        if (!myNickname || !myPassword || !loginTime || (now - loginTime > THREE_DAYS)) {
            localStorage.clear();
            myNickname = "";
            myPassword = "";
            
            while (!myNickname || myNickname.trim() === "") {
                myNickname = prompt("أدخل اسمك المستعار لدخول شات المهندس:");
            }
            while (!myPassword || myPassword.trim() === "") {
                myPassword = prompt("أدخل كلمة السر الخاصة بك:");
            }
            
            localStorage.setItem('samy_chat_name', myNickname);
            localStorage.setItem('samy_chat_pass', myPassword);
            localStorage.setItem('samy_chat_time', now);
        }

        if (myPassword === "7796617199") {
            isAdmin = true;
            document.body.classList.add('is-admin');
        }

        socket.on('connect', () => {
            socket.emit('check_join', {name: myNickname, pass: myPassword, admin: isAdmin});
        });

        socket.on('login_failed', function(data) {
            alert(data.msg);
            localStorage.clear();
            window.location.reload();
        });

        socket.on('user_list', function(userList) {
            const bar = document.getElementById('users-bar');
            bar.innerHTML = '<span style="font-size:0.8rem; color:#666; margin-left:5px;">المتصلون:</span>';
            for (let id in userList) {
                const u = userList[id];
                const badge = document.createElement('div');
                badge.className = 'user-badge';
                
                let imgClass = u.is_admin ? 'king-badge' : '';
                let kickTag = (isAdmin && id !== socket.id) ? `<button class="kick-btn" onclick="kickUser('${id}')">X</button>` : '';
                
                badge.innerHTML = `<img src="${u.avatar}" class="${imgClass}"><span>${u.name}</span>${kickTag}`;
                bar.appendChild(badge);
            }
        });

        socket.on('status', function(data) {
            const messagesContainer = document.getElementById('messages');
            const msgDiv = document.createElement('div');
            msgDiv.className = 'system';
            msgDiv.innerText = data.msg;
            messagesContainer.appendChild(msgDiv);
            scrollToBottom();
        });

        socket.on('message', function(data) {
            const messagesContainer = document.getElementById('messages');
            
            if (data.sender === "System") {
                const msgDiv = document.createElement('div');
                msgDiv.className = 'system';
                msgDiv.innerText = data.msg;
                messagesContainer.appendChild(msgDiv);
            } else {
                const wrapper = document.createElement('div');
                const isMe = (data.sender === myNickname || data.sender === "👑 الملك " + myNickname);
                wrapper.className = isMe ? 'msg-wrapper me' : 'msg-wrapper';
                
                let isKingMsg = data.sender.includes("👑");
                let nameLabel = isMe ? '' : `<span class="sender-name ${isKingMsg ? '' : 'normal'}">${data.sender}</span>`;
                
                wrapper.innerHTML = `
                    <img src="${data.avatar}" class="avatar-chat">
                    <div class="msg ${isMe ? 'my-msg' : 'others'}">
                        ${nameLabel}
                        <div>${data.msg}</div>
                    </div>
                `;
                messagesContainer.appendChild(wrapper);
            }
            scrollToBottom();
        });

        socket.on('kicked', function() {
            alert("لقد تم طردك من الغرفة بواسطة الملك!");
            localStorage.clear();
            window.location.reload();
        });

        function kickUser(socketId) {
            if (confirm("هل أنت متأكد من طرد هذا المستخدم؟")) {
                socket.emit('kick_user', {id: socketId});
            }
        }

        function sendMessage() {
            const input = document.getElementById('message-input');
            const msg = input.value.trim();
            if (msg !== "") {
                socket.emit('text', {'msg': msg});
                input.value = "";
            }
        }

        document.getElementById('send-btn').onclick = sendMessage;
        document.getElementById('message-input').onkeypress = function(e) {
            if (e.key === 'Enter') sendMessage();
        };

        function scrollToBottom() {
            const m = document.getElementById('messages');
            m.scrollTop = m.scrollHeight;
        }

        window.visualViewport.addEventListener('resize', () => {
            document.body.style.height = window.visualViewport.height + 'px';
            scrollToBottom();
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(html_template)

@socketio.on('check_join')
def on_check_join(data):
    if len(active_sessions) >= 20:
        emit('login_failed', {'msg': 'السيرفر ممتلئ! (الحد الأقصى 20 مستخدم)'})
        return
        
    nickname = data['name'].strip()
    password = data['pass'].strip()
    is_admin = data['admin']
    
    if nickname in registered_users:
        if registered_users[nickname]['password'] != password:
            emit('login_failed', {'msg': '❌ هذا الاسم محجوز وكلمة السر غير صحيحة!'})
            return
        else:
            avatar_url = registered_users[nickname]['avatar']
    else:
        avatar_num = random.randint(1, 70)
        avatar_url = f"https://i.pravatar.cc/100?img={avatar_num}"
        registered_users[nickname] = {'password': password, 'avatar': avatar_url}
        
    if is_admin:
        display_name = f"👑 الملك {nickname}"
    else:
        display_name = nickname
        
    active_sessions[request.sid] = {"name": display_name, "avatar": avatar_url, "is_admin": is_admin}
    
    emit('status', {'msg': f'انضم {display_name} إلى شات المهندس.'}, broadcast=True)
    emit('user_list', active_sessions, broadcast=True)

@socketio.on('disconnect')
def on_disconnect():
    if request.sid in active_sessions:
        nickname = active_sessions[request.sid]['name']
        del active_sessions[request.sid]
        emit('status', {'msg': f'غادر {nickname} الشات.'}, broadcast=True)
        emit('user_list', active_sessions, broadcast=True)

@socketio.on('text')
def on_text(data):
    if request.sid in active_sessions:
        sender = active_sessions[request.sid]['name']
        avatar = active_sessions[request.sid]['avatar']
        emit('message', {'sender': sender, 'avatar': avatar, 'msg': data['msg']}, broadcast=True)

@socketio.on('kick_user')
def on_kick(data):
    if request.sid in active_sessions and active_sessions[request.sid]['is_admin']:
        target_id = data['id']
        if target_id in active_sessions:
            target_name = active_sessions[target_id]['name']
            emit('kicked', room=target_id)
            emit('status', {'msg': f'🚫 قام الملك بطرد [{target_name}] من الشات!'}, broadcast=True)
import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
    
        
