import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, disconnect

app = Flask(__name__)
# مفتاح أمان لتشفير الجلسات (يمكنك تغييره لأي نص تريده)
app.config['SECRET_KEY'] = 'samy_king_secret_key_779'

# إعداد مكتبة السوكت مع تفعيل الـ CORS لتجنب أي مشاكل اتصال على سيرفر Render
socketio = SocketIO(app, cors_allowed_origins="*")

# قاموس ذكي لحفظ المستخدمين المتصلين حالياً داخل سيرفر السحابي (مفتاح: SID، قيمة: بيانات المستخدم)
connected_users = {}

@app.route('/')
def index():
    return render_template('index.html')

# عندما يدخل أي مستخدم جديد للشات
@socketio.on('user_join')
def handle_user_join(data):
    username = data.get('username')
    is_admin = data.get('isAdmin', False)
    
    # حماية: التأكد من أن الشخص الذي يدعي أنه آدمن هو فعلاً "المهندس"
    if username == "المهندس" and not is_admin:
        is_admin = True
        
    # حفظ بيانات اتصال المستخدم بالـ SID الفريد الخاص به
    connected_users[request.sid] = {
        'username': username,
        'isAdmin': is_admin
    }
    print(f"👤 انضمام: {username} | مسؤول: {is_admin}")

# عندما يرسل أي مستخدم رسالة جديدة
@socketio.on('new_message')
def handle_new_message(data):
    username = data.get('username')
    text = data.get('text')
    is_admin = data.get('isAdmin', False)
    
    # حماية السيرفر: منع أي تلاعب برتبة المالك من المتصفح
    if is_admin and username != "المهندس":
        is_admin = False
        username = "زائر منتحل!"  # حظر التلاعب بالأسماء
        
    # إعادة توزيع الرسالة فورياً للجميع
    emit('message_received', {
        'username': username,
        'text': text,
        'isAdmin': is_admin
    }, broadcast=True)

# نظام الطرد الخاص بالمالك (المهندس)
@socketio.on('kick_user')
def handle_kick_user(data):
    sender_sid = request.sid
    sender_data = connected_users.get(sender_sid, {})
    
    # التحقق الأمني: هل مرسل أمر الطرد هو "المهندس" المالك الحقيقي؟
    if sender_data.get('username') == "المهندس" and sender_data.get('isAdmin') == True:
        target_username = data.get('target')
        print(f"🚫 الآدمن المهندس قام بطرد: {target_username}")
        
        # إرسال أمر الطرد لمتصفحات الجميع ليفصل متصفح المطرود نفسه تلقائياً
        emit('user_kicked', {'target': target_username}, broadcast=True)
        
        # قطع الاتصال الفعلي من السيرفر السحابي عن المستخدم المطرود لزيادة الأمان
        for sid, user_info in list(connected_users.items()):
            if user_info.get('username') == target_username:
                disconnect(sid)  # فصل الاتصال نهائياً
                connected_users.pop(sid, None)  # حذفه من قائمة المتصلين
    else:
        print(f"⚠️ محاولة اختراق أو طرد غير مصرح بها من الـ SID: {sender_sid}")

# عند خروج أو إغلاق أي مستخدم للمتصفح
@socketio.on('disconnect')
def handle_disconnect():
    user_info = connected_users.pop(request.sid, None)
    if user_info:
        print(f"🚪 مغادرة: {user_info.get('username')}")

if __name__ == '__main__':
    # تشغيل السيرفر على البورت الذي يحدده سيرفر Render تلقائياً
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
