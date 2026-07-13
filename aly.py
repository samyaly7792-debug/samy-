from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import os

app = Flask(__name__)
# مفتاح تشفير قوي لضمان أمان الجلسات
app.config['SECRET_KEY'] = 'samy_king_final_2026_secure'

# إعداد SocketIO ليتوافق مع جميع بيئات الاستضافة السحابية
socketio = SocketIO(app, cors_allowed_origins="*", async_mode=None)

# قاعدة بيانات مؤقتة للمستخدمين المتصلين
active_users = {}
ADMIN_NAME = "المهندس"
ADMIN_PASS = "Samy779h"

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    name = data.get('name', 'زائر')
    password = data.get('pass', '')
    # التحقق من صلاحيات المدير
    is_admin = (name == ADMIN_NAME and password == ADMIN_PASS)
    active_users[request.sid] = {'name': name, 'is_admin': is_admin}
    
    # إرسال قائمة المستخدمين المحدثة للجميع
    emit('user_list', active_users, broadcast=True)

@socketio.on('text')
def on_text(data):
    user = active_users.get(request.sid)
    if user:
        # إرسال الرسالة مع اسم المرسل وحالة الإدارة
        emit('message', {
            'sender': user['name'], 
            'is_admin': user['is_admin'], 
            'msg': data.get('msg', '')
        }, broadcast=True)

@socketio.on('disconnect')
def on_disconnect():
    if request.sid in active_users:
        del active_users[request.sid]
        emit('user_list', active_users, broadcast=True)

if __name__ == '__main__':
    # الحصول على المنفذ من النظام أو استخدام 10000 كقيمة افتراضية لـ Render
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port)
