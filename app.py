#!/usr/bin/env python3
# app.py
# "شات المهندس" - Flask + Flask-SocketIO backend
# Ready for public deployment with Eventlet WebSocket support.
#
# Notes:
# - Owner credentials are hardcoded as requested:
#     username: "المهندس"
#     password: "samy779h"
# - For production, consider moving secrets out of source code and using environment variables.
#
# Requirements:
#   pip install flask flask-socketio eventlet

import os
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, join_room, leave_room, emit
from collections import defaultdict, deque
from datetime import datetime
import logging

# Owner credentials (as requested)
OWNER_USERNAME = "المهندس"
OWNER_PASSWORD = "samy779h"

# Try to enable eventlet for best WebSocket support
async_mode = None
try:
    import eventlet  # noqa: F401
    eventlet.monkey_patch()
    async_mode = 'eventlet'
except Exception:
    async_mode = 'threading'

# Flask app
app = Flask(__name__, template_folder="templates")
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-secret-in-production')

# SocketIO configuration
socketio = SocketIO(app, cors_allowed_origins="*", async_mode=async_mode)

# In-memory message history per room (keep last N messages)
MAX_HISTORY_PER_ROOM = 200
message_history = defaultdict(lambda: deque(maxlen=MAX_HISTORY_PER_ROOM))

# Connected users: sid -> { username, room, is_owner, joined_at }
connected_users = {}

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chat_engineer")

def _now_iso():
    return datetime.utcnow().isoformat() + "Z"

def room_presence(room):
    """
    Return list of participants in the room with owner flag.
    """
    plist = []
    for info in connected_users.values():
        if info.get("room") == room:
            plist.append({
                "username": info.get("username"),
                "is_owner": bool(info.get("is_owner")),
                "joined_at": info.get("joined_at")
            })
    # Sort owners first then by join time
    plist.sort(key=lambda x: (0 if x["is_owner"] else 1, x["joined_at"]))
    return plist

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "time": _now_iso()})

@socketio.on("connect", namespace="/chat")
def on_connect():
    sid = request.sid
    logger.info(f"[connect] sid={sid}")
    emit("connected", {"message": "متصل بالخادم", "time": _now_iso()})

@socketio.on("join", namespace="/chat")
def on_join(data):
    """
    Expected data: { username: str, room: str, password?: str }
    If username == OWNER_USERNAME, password is required and must match OWNER_PASSWORD.
    Returns ack: { status: "ok", history: [...], presence: [...] } OR { status: "error", reason: "..." }
    """
    sid = request.sid
    username = (data.get("username") or "").strip() or "مستخدم غير معروف"
    room = (data.get("room") or "main").strip() or "main"
    password = data.get("password") or ""

    # Owner check
    is_owner = False
    if username == OWNER_USERNAME:
        if password != OWNER_PASSWORD:
            logger.warning(f"[join] sid={sid} attempted owner login with wrong password")
            return {"status": "error", "reason": "invalid_owner_password"}
        else:
            is_owner = True
            logger.info(f"[join] sid={sid} owner logged in")

    # Register user
    connected_users[sid] = {
        "username": username,
        "room": room,
        "is_owner": is_owner,
        "joined_at": _now_iso()
    }
    join_room(room)
    logger.info(f"[join] sid={sid} username={username} room={room} owner={is_owner}")

    # Broadcast a system message to room
    if is_owner:
        system_text = f"دخل المالك المهندس 👑"
    else:
        system_text = f"{username} انضمّ إلى الغرفة."
    system_msg = {
        "type": "system",
        "text": system_text,
        "time": _now_iso()
    }
    emit("system_message", system_msg, room=room)

    # Send history and presence to the joining client as ack
    hist = list(message_history[room])
    presence = room_presence(room)
    # Also broadcast updated presence to room
    emit("presence_update", {"presence": presence}, room=room)
    return {"status": "ok", "history": hist, "presence": presence}

@socketio.on("leave", namespace="/chat")
def on_leave(data):
    """
    Expected data: { username: str, room: str }
    """
    sid = request.sid
    username = (data.get("username") or "مستخدم غير معروف")
    room = (data.get("room") or "main")
    leave_room(room)
    logger.info(f"[leave] sid={sid} username={username} room={room}")

    # Remove from connected users if exists
    user = connected_users.pop(sid, None)
    # Broadcast system message
    system_msg = {
        "type": "system",
        "text": f"{username} غادر الغرفة.",
        "time": _now_iso()
    }
    emit("system_message", system_msg, room=room)
    # Broadcast presence update
    presence = room_presence(room)
    emit("presence_update", {"presence": presence}, room=room)
    return {"status": "ok"}

@socketio.on("message", namespace="/chat")
def on_message(data):
    """
    Expected data: { username: str, room: str, text: str, client_id?: str }
    Returns ack: { status: "ok", time: ... } or error.
    """
    sid = request.sid
    username = (data.get("username") or "مستخدم غير معروف")
    room = (data.get("room") or "main")
    text = (data.get("text") or "").strip()
    client_id = data.get("client_id")
    if not text:
        logger.info(f"[message] empty message from sid={sid}; ignoring")
        return {"status": "error", "reason": "empty_text"}

    # Determine if sender is owner from server-side record (trust server)
    user = connected_users.get(sid, {})
    is_owner = bool(user.get("is_owner"))

    timestamp = _now_iso()
    msg = {
        "type": "message",
        "username": username,
        "text": text,
        "time": timestamp,
        "client_id": client_id,
        "is_owner": is_owner
    }

    # Append to history
    message_history[room].append(msg)
    # Broadcast to room
    emit("message", msg, room=room)
    logger.info(f"[message] room={room} username={username} owner={is_owner} text_len={len(text)}")
    return {"status": "ok", "time": timestamp}

@socketio.on("ping_server", namespace="/chat")
def on_ping(data):
    client_ts = data.get("ts")
    server_ts = _now_iso()
    emit("pong_server", {"ts": client_ts, "server_ts": server_ts})

@socketio.on("disconnect", namespace="/chat")
def on_disconnect():
    sid = request.sid
    user = connected_users.pop(sid, None)
    if user:
        username = user.get("username", "مستخدم")
        room = user.get("room", "main")
        logger.info(f"[disconnect] sid={sid} username={username} room={room}")
        system_msg = {
            "type": "system",
            "text": f"{username} فقد الاتصال أو غادر.",
            "time": _now_iso()
        }
        emit("system_message", system_msg, room=room)
        # Broadcast presence update
        presence = room_presence(room)
        emit("presence_update", {"presence": presence}, room=room)
    else:
        logger.info(f"[disconnect] sid={sid} (unknown user)")

if __name__ == "__main__":
    # For public deployment, run with eventlet worker (socketio.run will use eventlet if available).
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting server on {host}:{port} (async_mode={async_mode})")
    # Note: In production it's recommended to use gunicorn with eventlet workers:
    # gunicorn -k eventlet -w 1 -b 0.0.0.0:5000 app:app
    socketio.run(app, host=host, port=port)
