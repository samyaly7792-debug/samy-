# استيراد مكتبات التوافق (Monkey Patching) لضمان عمل gevent مع SocketIO
from gevent import monkey
monkey.patch_all()

import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, disconnect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'samy_king_secret_key_779'

# تفعيل CORS والاتصال المتوافق مع المتصفحات
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent', ping_timeout=60, ping_interval=25)

connected_users = {}

@app.route('/')
def index():
    return render_template('index.html')

# دالة التعامل مع انضمام المستخدم (تنتظر حتى يتم استدعاؤها من الزر)
@socketio.on('user_join')
def handle_user_join(data):
    username = data.get('username')
    is_admin = data.get('isAdmin', False)
    
    if username == "المهندس" and not is_admin:
        is_admin = True
        
    connected_users[request.sid] = {'username': username, 'isAdmin': is_admin}
    print(f"👤 انضمام: {username}")

@socketio.on('new_message')
def handle_new_message(data):
    emit('message_received', data, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    connected_users.pop(request.sid, None)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # تشغيل السيرفر باستخدام واجهة gevent المناسبة للمنصات السحابية
    socketio.run(app, host='0.0.0.0', port=port)
