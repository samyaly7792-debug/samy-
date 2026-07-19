from flask import Flask, render_template_string, request
from flask_socketio import SocketIO

app = Flask(__name__)
# إعداد SocketIO مع دعم كامل للاتصالات المتعددة
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# كود الواجهة (HTML + CSS + JS) مدمج داخل كود بايثون
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl" style="height: 100%; margin: 0;">
<body style="height: 100vh; margin: 0; display: flex; flex-direction: column; background: #0f172a; color: white; font-family: sans-serif;">
    <div id="chat" style="flex: 1; overflow-y: auto; padding: 15px;">
        <h2 style="color: #FFD700; text-align: center;">👑 شات المهندس 👑</h2>
    </div>
    <div style="padding: 15px; background: #1e293b; display: flex;">
        <input id="username" placeholder="اسمك..." style="flex: 1; padding: 10px;">
        <input id="msg" placeholder="الرسالة..." style="flex: 2; padding: 10px;">
        <button onclick="send()" style="padding: 10px;">إرسال</button>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
        const socket = io();
        function send() {
            let user = document.getElementById('username').value;
            let msg = document.getElementById('msg').value;
            socket.emit('message', {username: user, msg: msg});
            document.getElementById('msg').value = '';
        }
        socket.on('message', function(data) {
            let chat = document.getElementById('chat');
            let div = document.createElement('div');
            // التأكد من التنسيق الذهبي للمالك
            if(data.username === "المهندس") {
                div.innerHTML = `<p style="color: #FFD700;">👑 <b>المهندس</b>: ${data.msg}</p>`;
            } else {
                div.innerHTML = `<p><b>${data.username}</b>: ${data.msg}</p>`;
            }
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@socketio.on('message')
def handle_message(data):
    # إعادة إرسال الرسالة لجميع المتصلين
    socketio.emit('message', data)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
