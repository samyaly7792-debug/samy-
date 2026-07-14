# gunicorn_config.py
import multiprocessing

# إعدادات Gunicorn الأساسية
workers = multiprocessing.cpu_count() * 2 + 1  # عدد العمال (2xCPU + 1)
worker_class = "eventlet"  # استخدام Eventlet (مطلوب لـ Flask-SocketIO)
bind = "0.0.0.0:$PORT"     # استخدام $PORT من Render (يجب أن يكون متغير بيئة)
timeout = 120              # وقت انتظار الطلبات (بالثواني)
keepalive = 5              # وقت الإبقاء على الاتصال
