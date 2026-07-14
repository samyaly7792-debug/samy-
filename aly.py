from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import os
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'samy_king_final_2026_stable'

# إعداد SocketIO مع async_mode='threading' لتجنب مشاكل Eventlet
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# إعدادات الأدمن
ADMIN_NAME = "المهندس"
ADMIN_PASS = "Samy779h"
ADMIN_COLOR = "gold"
ADMIN_PREFIX = "👑"

active_users = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    name = data.get('name', 'زائر')
    is_admin = (name == ADMIN_NAME and data.get('pass') == ADMIN_PASS)

    # إذا كان الأدمن، إرسال رسالة ترحيب عامة
    if is_admin:
        emit('message', {
            'sender': "النظام",
            'is_admin': False,
            'msg': f"🚀 تم دخول الملك {ADMIN_PREFIX} {name} إلى الشات! 🚀",
            'color': "cyan"
        }, broadcast=True)

    active_users[request.sid] = {'name': name, 'is_admin': is_admin}
    emit('user_list', list(active_users.values()), broadcast=True)

@socketio.on('text')
def on_text(data):
    user = active_users.get(request.sid)
    if user:
        msg = data.get('msg', '').strip()
        if not msg:  # منع إرسال رسائل فارغة
            return

        # تمييز رسائل الأدمن
        if user['is_admin']:
            msg = f"🔥 {msg} 🔥"  # إضافة تنسيق للأدمن

        emit('message', {
            'sender': f"{ADMIN_PREFIX} {user['name']}" if user['is_admin'] else user['name'],
            'is_admin': user['is_admin'],
            'msg': msg,
            'color': ADMIN_COLOR if user['is_admin'] else "white"
        }, broadcast=True)

@socketio.on('kick')
def on_kick(data):
    if not active_users.get(request.sid, {}).get('is_admin'):
        return  # فقط الأدمن يمكنه الطرد

    target_sid = data.get('sid')
    if target_sid in active_users:
        emit('kicked', room=target_sid)  # إرسال رسالة طرد للمستخدم
        del active_users[target_sid]
        emit('user_list', list(active_users.values()), broadcast=True)

@socketio.on('ban')
def on_ban(data):
    if not active_users.get(request.sid, {}).get('is_admin'):
        return  # فقط الأدمن يمكنه الحظر

    target_name = data.get('name')
    # هنا يمكنك إضافة قاعدة بيانات لحظر الأسماء
    emit('banned', {'name': target_name}, broadcast=True)

@socketio.on('disconnect')
def on_disconnect():
    if request.sid in active_users:
        del active_users[request.sid]
        emit('user_list', list(active_users.values()), broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port)
