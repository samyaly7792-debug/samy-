from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'samy_king_final_2026_stable'

# إعداد SocketIO بدون gevent أو eventlet
socketio = SocketIO(app, cors_allowed_origins="*")

# إعدادات الأدمن
ADMIN_NAME = "المهندس"
ADMIN_PASS = "Samy779h"
ADMIN_COLOR = "gold"
ADMIN_PREFIX = "👑"

active_users = {}

@app.route('/')
def index():
    return render_template('index.html')  # عرض صفحة index.html مباشرة

@socketio.on('join')
def on_join(data):
    name = data.get('name', 'زائر')
    is_admin = (name == ADMIN_NAME and data.get('pass') == ADMIN_PASS)

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
        if not msg:
            return

        if user['is_admin']:
            msg = f"🔥 {msg} 🔥"

        emit('message', {
            'sender': f"{ADMIN_PREFIX} {user['name']}" if user['is_admin'] else user['name'],
            'is_admin': user['is_admin'],
            'msg': msg,
            'color': ADMIN_COLOR if user['is_admin'] else "white"
        }, broadcast=True)

@socketio.on('kick')
def on_kick(data):
    if not active_users.get(request.sid, {}).get('is_admin'):
        return

    target_sid = data.get('sid')
    if target_sid in active_users:
        emit('kicked', room=target_sid)
        del active_users[target_sid]
        emit('user_list', list(active_users.values()), broadcast=True)

@socketio.on('disconnect')
def on_disconnect():
    if request.sid in active_users:
        del active_users[request.sid]
        emit('user_list', list(active_users.values()), broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
