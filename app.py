#!/usr/bin/env python3
# app.py
# "شات المهندس" - Flask + Flask-SocketIO backend
#
# ميزات:
# - غرفة عامة واحدة لجميع المستخدمين
# - تمييز المالك (المهندس) باللون الذهبي/TAG في الواجهة (client-side)
# - إشعار نظام عند دخول المالك: "انضم المالك المهندس"
# - رفع ملفات/صور إلى مجلد uploads وتأمين اسم الملف
# - دعم Reply/Quote عبر حقل reply_to في الرسائل
# - قائمة المتواجدين (presence)
# - تغيير اسم المستخدم (update_profile) وتحديث الحضور
#
# Requirements:
#   pip install flask flask-socketio eventlet python-dotenv werkzeug
#
# تشغيل في التطوير:
#   python app.py
# تشغيل بالإنتاج (موصى به):
#   gunicorn -k eventlet -w 1 -b 0.0.0.0:5000 app:app
#

import os
import uuid
from datetime import datetime
from collections import defaultdict, deque
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Flask, render_template, jsonify, request, send_from_directory, abort
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging

# -----------------------
# Configuration
# -----------------------
# Owner credentials (كما طلبت)
OWNER_USERNAME = "المهندس"
OWNER_PASSWORD = "samy779h"

# Upload settings
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "webp",
    "pdf", "txt", "md", "zip", "rar", "csv"
}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

# Message history settings
MAX_HISTORY_PER_ROOM = 500  # keep last N messages

# SocketIO async mode (eventlet preferred)
async_mode = None
try:
    import eventlet  # noqa: F401
    eventlet.monkey_patch()
    async_mode = "eventlet"
except Exception:
    async_mode = "threading"

# Flask app
app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me-in-prod")
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode=async_mode)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chat_engineer")

# In-memory stores (simple; consider DB/Redis for production)
message_history = defaultdict(lambda: deque(maxlen=MAX_HISTORY_PER_ROOM))
# connected_users: sid -> { username, is_owner(bool), joined_at, bg (optional) }
connected_users = {}

# Single global room name
GLOBAL_ROOM = "global"

# -----------------------
# Utility helpers
# -----------------------
def _now_iso():
    return datetime.utcnow().isoformat() + "Z"

def allowed_file(filename):
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def make_file_save_name(filename: str) -> str:
    # secure and prefix with uuid to avoid collisions
    filename = secure_filename(filename)
    uid = uuid.uuid4().hex
    return f"{uid}_{filename}"

def current_presence():
    """
    Return list of participants in the global room with owner flag and join time.
    """
    result = []
    for sid, info in connected_users.items():
        if info.get("room") == GLOBAL_ROOM:
            result.append({
                "username": info.get("username"),
                "is_owner": bool(info.get("is_owner")),
                "joined_at": info.get("joined_at")
            })
    # sort owners first, then by joined_at
    result.sort(key=lambda x: (0 if x["is_owner"] else 1, x["joined_at"]))
    return result

# -----------------------
# Routes: UI + uploads
# -----------------------
@app.route("/", methods=["GET"])
def index():
    # Pass OWNER_USERNAME into the template so client can detect owner locally if needed
    return render_template("index.html", OWNER_USERNAME=OWNER_USERNAME)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "time": _now_iso()})

@app.route("/uploads/<path:filename>", methods=["GET"])
def uploaded_file(filename):
    # serve uploaded files - in production serve via CDN or nginx
    safe_path = Path(app.config["UPLOAD_FOLDER"]) / filename
    if not safe_path.exists():
        abort(404)
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=False)

@app.route("/upload", methods=["POST"])
def upload():
    """
    Expects multipart form 'file'
    Returns JSON: { success: True, url: "/uploads/....", filename: "...", mimetype: "..." }
    """
    if "file" not in request.files:
        return jsonify({"success": False, "error": "no_file"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "empty_filename"}), 400
    if not allowed_file(file.filename):
        return jsonify({"success": False, "error": "file_type_not_allowed"}), 400
    save_name = make_file_save_name(file.filename)
    save_path = Path(app.config["UPLOAD_FOLDER"]) / save_name
    file.save(str(save_path))
    url = f"/uploads/{save_name}"
    return jsonify({"success": True, "url": url, "filename": file.filename, "mimetype": file.mimetype})

# -----------------------
# SocketIO events
# -----------------------
@socketio.on("connect", namespace="/chat")
def handle_connect():
    sid = request.sid
    logger.info(f"[connect] sid={sid}")
    # Don't auto-join until client sends 'join'
    emit("connected", {"message": "مرحبًا!"})

@socketio.on("join", namespace="/chat")
def handle_join(data):
    """
    data: { username: str, password?: str }
    If username == OWNER_USERNAME, password must match.
    Returns ack: { status: "ok", history: [...], presence: [...] } or { status: "error", reason: ... }
    """
    sid = request.sid
    username = (data.get("username") or "").strip() or "مستخدم غير معروف"
    password = data.get("password", "")
    # Check owner credentials
    is_owner = False
    if username == OWNER_USERNAME:
        if password != OWNER_PASSWORD:
            logger.warning(f"[join] sid={sid} attempted owner login with wrong password")
            return {"status": "error", "reason": "invalid_owner_password"}
        is_owner = True
        logger.info(f"[join] sid={sid} owner logged in")

    # Register user
    connected_users[sid] = {
        "username": username,
        "is_owner": is_owner,
        "joined_at": _now_iso(),
        "room": GLOBAL_ROOM,
        # optional client background preference (could be set later)
        "bg": data.get("bg", "")
    }
    join_room(GLOBAL_ROOM)
    logger.info(f"[join] {username} (owner={is_owner}) joined room {GLOBAL_ROOM}")

    # System message: special wording when owner joins
    if is_owner:
        system_text = "انضم المالك المهندس"
    else:
        system_text = f"{username} انضمّ إلى الشات."

    system_msg = {
        "id": uuid.uuid4().hex,
        "type": "system",
        "text": system_text,
        "time": _now_iso()
    }
    # append system to history and broadcast
    message_history[GLOBAL_ROOM].append(system_msg)
    emit("system_message", system_msg, room=GLOBAL_ROOM)

    # Prepare ack: send history + presence
    hist = list(message_history[GLOBAL_ROOM])
    presence = current_presence()
    # broadcast updated presence
    emit("presence_update", {"presence": presence}, room=GLOBAL_ROOM)
    return {"status": "ok", "history": hist, "presence": presence}

@socketio.on("message", namespace="/chat")
def handle_message(data):
    """
    data: { text: str, reply_to?: message_id, file?: { url, filename, mimetype } }
    Server will attach username (from connected_users) and is_owner flag.
    Returns ack { status: ok, id: message_id, time: ... }
    """
    sid = request.sid
    user = connected_users.get(sid)
    if not user:
        logger.warning(f"[message] sid {sid} sent message before join")
        return {"status": "error", "reason": "not_joined"}

    text = (data.get("text") or "").strip()
    fileinfo = data.get("file")
    reply_to = data.get("reply_to")
    if not text and not fileinfo:
        return {"status": "error", "reason": "empty_message"}

    msg_id = uuid.uuid4().hex
    msg = {
        "id": msg_id,
        "type": "message",
        "username": user.get("username"),
        "is_owner": bool(user.get("is_owner")),
        "text": text,
        "file": fileinfo or None,
        "reply_to": reply_to or None,
        "time": _now_iso()
    }
    # store and broadcast
    message_history[GLOBAL_ROOM].append(msg)
    emit("message", msg, room=GLOBAL_ROOM)
    logger.info(f"[message] {msg['username']} (owner={msg['is_owner']}) sent msg id={msg_id}")
    return {"status": "ok", "id": msg_id, "time": msg["time"]}

@socketio.on("update_profile", namespace="/chat")
def handle_update_profile(data):
    """
    data: { new_name?: str, bg?: str }
    Update server-side username and bg preference, broadcast presence and optional system notice.
    """
    sid = request.sid
    user = connected_users.get(sid)
    if not user:
        return {"status": "error", "reason": "not_joined"}
    old_name = user.get("username")
    new_name = (data.get("new_name") or "").strip()
    new_bg = data.get("bg")
    changed = False
    if new_name and new_name != old_name:
        user["username"] = new_name
        changed = True
        # system message for name change
        system_msg = {
            "id": uuid.uuid4().hex,
            "type": "system",
            "text": f"{old_name} غيّر اسمه إلى {new_name}.",
            "time": _now_iso()
        }
        message_history[GLOBAL_ROOM].append(system_msg)
        emit("system_message", system_msg, room=GLOBAL_ROOM)
    if new_bg is not None:
        user["bg"] = new_bg
        changed = True
    # broadcast updated presence
    presence = current_presence()
    emit("presence_update", {"presence": presence}, room=GLOBAL_ROOM)
    return {"status": "ok", "changed": changed}

@socketio.on("disconnect", namespace="/chat")
def handle_disconnect():
    sid = request.sid
    user = connected_users.pop(sid, None)
    if user:
        username = user.get("username")
        logger.info(f"[disconnect] {username} disconnected")
        system_msg = {
            "id": uuid.uuid4().hex,
            "type": "system",
            "text": f"{username} غادر الشات.",
            "time": _now_iso()
        }
        message_history[GLOBAL_ROOM].append(system_msg)
        emit("system_message", system_msg, room=GLOBAL_ROOM)
        # broadcast updated presence
        presence = current_presence()
        emit("presence_update", {"presence": presence}, room=GLOBAL_ROOM)
    else:
        logger.info(f"[disconnect] unknown sid disconnected")

# -----------------------
# Run
# -----------------------
if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting server at {host}:{port} (async_mode={async_mode})")
    # For production it's recommended to use gunicorn with eventlet worker:
    # gunicorn -k eventlet -w 1 -b 0.0.0.0:5000 app:app
    socketio.run(app, host=host, port=port)
