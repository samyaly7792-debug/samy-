import os
import sqlite3
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'samy_king_final_2026'
socketio = SocketIO(app, cors_allowed_origins="*")

# إعداد قاعدة البيانات
def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, avatar TEXT, is_admin INTEGER)''')
    # إضافة "المهندس" كمسؤول افتراضي إذا لم يكن موجوداً
    c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?)", 
              ("المهندس", "Samy779h", "https://cdn-icons-png.flaticon.com/512/3135/3135715.png", 1))
    conn.commit()
    conn.close()

init_db()

active_users = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    username = data.get('name')
    password = data.get('pass')
    
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()

    # إذا كان المستخدم جديداً نعتبره مستخدم عادي
    is_admin = 1 if user and user[3] == 1 else 0
    avatar = user[2] if user else 'https://cdn-icons-png.flaticon.com/512/3135/3135715.png'
    
    active_users[request.sid] = {'name': username, 'is_admin': is_admin, 'avatar': avatar}
    emit('user_list', active_users, broadcast=True)

@socketio.on('text')
def on_text(data):
    user = active_users.get(request.sid)
    if user:
        emit('message', {'sender': user['name'], 'is_admin': user['is_admin'], 'msg': data.get('msg')}, broadcast=True)

@socketio.on('disconnect')
def on_disconnect():
    if request.sid in active_users:
        del active_users[request.sid]
        emit('user_list', active_users, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port)
