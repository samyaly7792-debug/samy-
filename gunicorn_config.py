# gunicorn_config.py
import multiprocessing

# إعدادات Gunicorn مع gevent (بديل أفضل لـ eventlet)
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"  # استخدام gevent بدلاً من eventlet
bind = "0.0.0.0:$PORT"
timeout = 120
keepalive = 5
