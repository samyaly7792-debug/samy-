#!/usr/bin/env python3
# app.py
# Flask + Flask-SocketIO backend for "شات المهندس"
# Requirements:
#   pip install flask flask-socketio eventlet

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, join_room, leave_room, emit
from collections import deque, defaultdict
from datetime import datetime
import logging

# Try to use eventlet for better WebSocket support/performance; fallback otherwise.
async_mode = None
try:
    import eventlet  # noqa: F401
    eventlet.monkey_patch()
    async_mode = 'eventlet'
except Exception:
    async_mode = 'threading'

app = Flask(__name__, template_folder="templates")
app.config['SECRET_KEY'] = 'change-this-secret-in-production'

# Configure SocketIO with CORS allowed for development. Restrict in production!
socketio = SocketIO(app, cors_allowed_origins="*", async_mode=async_mode)

# In-memory message history per room (keeps last N messages)
MAX_HISTORY_PER_ROOM = 100
message_history = defaultdict(lambda: deque(maxlen=MAX_HISTORY_PER_ROOM))

# Simple in-memory mapping of sid -> user info (for logging/disconnect handling)
connected_users = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chat")

@app.route("/", methods=["GET"])
def index():
    """
    Serve the chat UI.
    """
    return render_template("index.html")

@app.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint.
    """
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat() + "Z"})

def _now_iso():
    return datetime.utcnow().isoformat() + "Z"

@socketio.on("connect", namespace="/chat")
def handle_connect():
    sid = request.sid
    logger.info(f"[connect] sid={sid}")
    # No ACK return; client will receive 'connected' event after join if needed.
    # But emit a welcome (private) message.
    emit("connected", {"message": "متصل بالخادم", "time": _now_iso()})

@socketio.on("join", namespace="/chat")
def handle_join(data):
    """
    data: { username: str, room: str }
    Returns ack with current room history.
    """
    sid = request.sid
    username = data.get("username", "مستخدم غير معروف")
    room = data.get("room", "main")
    # Save user info
    connected_users[sid] = {"username": username, "room": room}
    join_room(room)
    logger.info(f"[join] sid={sid} username={username} room={room}")
    system_msg = {
        "type": "system",
        "text": f"{username} انضمّ إلى الغرفة.",
        "time": _now_iso()
    }
    # Broadcast system message to room (including to the new user)
    emit("system_message", system_msg, room=room)
    # Send current history back to the joining client as ack (return value)
    hist = list(message_history[room])
    return {"status": "ok", "history": hist}

@socketio.on("leave", namespace="/chat")
def handle_leave(data):
    """
    data: { username: str, room: str }
    """
    sid = request.sid
    username = data.get("username", "مستخدم غير معروف")
    room = data.get("room", "main")
    leave_room(room)
    logger.info(f"[leave] sid={sid} username={username} room={room}")
    system_msg = {
        "type": "system",
        "text": f"{username} غادر الغرفة.",
        "time": _now_iso()
    }
    emit("system_message", system_msg, room=room)
    # Remove from connected_users if matches
    if sid in connected_users:
        try:
            if connected_users[sid].get("room") == room:
                del connected_users[sid]
        except KeyError:
            pass
    return {"status": "ok"}

@socketio.on("message", namespace="/chat")
def handle_message(data):
    """
    data: { username: str, room: str, text: str, client_id?: str }
    Returns ack with server timestamp and optional message id.
    """
    sid = request.sid
    username = data.get("username", "مستخدم غير معروف")
    room = data.get("room", "main")
    text = data.get("text", "")
    client_id = data.get("client_id")  # optional id from client for matching acks
    timestamp = _now_iso()
    if not text:
        logger.info(f"[message] empty text from sid={sid}; ignoring")
        return {"status": "error", "reason": "empty_text"}

    msg = {
        "type": "message",
        "username": username,
        "text": text,
        "time": timestamp,
        "client_id": client_id
    }

    # Append to history
    message_history[room].append(msg)
    # Broadcast to the room
    emit("message", msg, room=room)
    logger.info(f"[message] room={room} username={username} text_len={len(text)}")
    # Return ack
    return {"status": "ok", "time": timestamp}

@socketio.on("ping_server", namespace="/chat")
def handle_ping(data):
    """
    Lightweight ping-pong to check latency and connectivity.
    client sends: { ts: <client timestamp> }
    server responds with: { ts: <client ts>, server_ts: <server ts> }
    """
    sid = request.sid
    client_ts = data.get("ts")
    server_ts = _now_iso()
    emit("pong_server", {"ts": client_ts, "server_ts": server_ts})

@socketio.on("disconnect", namespace="/chat")
def handle_disconnect():
    sid = request.sid
    user = connected_users.get(sid)
    if user:
        username = user.get("username", "مستخدم")
        room = user.get("room", "main")
        logger.info(f"[disconnect] sid={sid} username={username} room={room}")
        # Broadcast that the user left
        system_msg = {
            "type": "system",
            "text": f"{username} فقد الاتصال أو غادر.",
            "time": _now_iso()
        }
        emit("system_message", system_msg, room=room)
        try:
            del connected_users[sid]
        except KeyError:
            pass
    else:
        logger.info(f"[disconnect] sid={sid} (unknown user)")

if __name__ == "__main__":
    # Production note: use an async worker (eventlet/gevent) for heavy load and enable message queue (Redis)
    logger.info(f"Starting Flask-SocketIO server (async_mode={async_mode})")
    socketio.run(app, host="0.0.0.0", port=5000)
