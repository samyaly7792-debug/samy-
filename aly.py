from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, disconnect
import os

app = Flask(__name__)
# يُفضل دائماً تغيير مفتاح التشفير ليكون أكثر أماناً في الإنتاج
app.config['SECRET_KEY'] = 'samy_king_final_2026'
# إعداد SocketIO مع السماح بجميع المصادر للاتصال
socketio = SocketIO(app, cors_allowed_origins="*", async_mode=None)

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
    
    # حفظ المستخدم في قاموس المستخدمين النشطين
    active_users[request.sid] = {'name': name, 'is_admin': is_admin}
    
    # إرسال تأكيد الانضمام للعميل (لإخفاء شاشة الدخول)
    emit('join_success', {'status': 'success'}, room=request.sid)
    
    # إرسال رسالة ترحيبية للجميع
    welcome_msg = f"دخل المالك {name}" if is_admin else f"دخل {name} بإشراف المهندس"
    emit('status', {'msg': welcome_msg}, broadcast=True)
    
    # تحديث قائمة المستخدمين للجميع
    emit('user_list', active_users, broadcast=True)

@socketio.on('text')
def on_text(data):
    user = active_users.get(request.sid)
    if user:
        emit('message', {
            'sender': user['name'],
            'is_admin': user['is_admin'],
            'msg': data.get('msg', '')
        }, broadcast=True)

@socketio.on('disconnect')
def on_disconnect():
    if request.sid in active_users:
        name = active_users[request.sid]['name']
        del active_users[request.sid]
        emit('status', {'msg': f'غادر {name} الشات.'}, broadcast=True)
        emit('user_list', active_users, broadcast=True)

if __name__ == '__main__':
    # استخدام المنفذ المخصص من بيئة الاستضافة أو الافتراضي 5000
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
