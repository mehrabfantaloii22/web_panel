import hashlib
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

AUTH_FILE = DATA_DIR / "users.json"
SESSION_FILE = DATA_DIR / "sessions.json"
ARCHIVE_FILE = DATA_DIR / "music_archive.json"
LOGS_FILE = DATA_DIR / "logs.json"
SETTINGS_FILE = BASE_DIR / "settings.json"


def _now():
    return datetime.now(timezone.utc).isoformat()


def _load_json(path, default):
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return default


def _save_json(path, data):
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)


def read_panel_settings():
    if not SETTINGS_FILE.exists():
        return {"modules": {}}
    try:
        with SETTINGS_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception:
        return {"modules": {}}
    data.setdefault("modules", {})
    return data


def write_panel_settings(data):
    _save_json(SETTINGS_FILE, data)


def ensure_defaults():
    users_data = _load_json(AUTH_FILE, {"users": []})
    if not users_data.get("users"):
        users_data = {
            "users": [
                {
                    "id": "admin",
                    "username": "admin",
                    "password": hashlib.sha256(b"admin123").hexdigest(),
                    "role": "admin",
                    "created_at": _now(),
                }
            ]
        }
        _save_json(AUTH_FILE, users_data)

    sessions_data = _load_json(SESSION_FILE, {"sessions": []})
    sessions_data.setdefault("sessions", [])
    _save_json(SESSION_FILE, sessions_data)

    archive_data = _load_json(ARCHIVE_FILE, {"songs": []})
    archive_data.setdefault("songs", [])
    _save_json(ARCHIVE_FILE, archive_data)

    logs_data = _load_json(LOGS_FILE, {"logs": []})
    logs_data.setdefault("logs", [])
    _save_json(LOGS_FILE, logs_data)

    return users_data, sessions_data, archive_data, logs_data


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def authenticate_user(username: str, password: str):
    users_data, _, _, _ = ensure_defaults()
    for user in users_data.get("users", []):
        if user.get("username") == username and user.get("password") == hash_password(password):
            return user
    return None


def list_users():
    users_data, _, _, _ = ensure_defaults()
    return users_data.get("users", [])


def create_user(username: str, password: str, role: str = "user"):
    users_data, _, _, _ = ensure_defaults()
    users = users_data.setdefault("users", [])
    if any(item.get("username") == username for item in users):
        return None
    user = {
        "id": secrets.token_hex(4),
        "username": username,
        "password": hash_password(password),
        "role": role,
        "created_at": _now(),
    }
    users.append(user)
    _save_json(AUTH_FILE, users_data)
    append_log("security", f"Created user {username}", {"role": role}, user=username)
    return user


def update_password(username: str, password: str):
    users_data, _, _, _ = ensure_defaults()
    users = users_data.setdefault("users", [])
    for user in users:
        if user.get("username") == username:
            user["password"] = hash_password(password)
            _save_json(AUTH_FILE, users_data)
            return True
    return False


def delete_user(username: str):
    users_data, _, _, _ = ensure_defaults()
    users = users_data.setdefault("users", [])
    new_users = [user for user in users if user.get("username") != username]
    if len(new_users) == len(users):
        return False
    users_data["users"] = new_users
    _save_json(AUTH_FILE, users_data)
    append_log("security", f"Deleted user {username}", {}, user=username)
    return True


def create_session(username: str, role: str):
    sessions_data = _load_json(SESSION_FILE, {"sessions": []})
    sessions_data.setdefault("sessions", [])
    token = secrets.token_urlsafe(24)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    sessions_data["sessions"].append(
        {
            "token": token,
            "username": username,
            "role": role,
            "expires_at": expires_at,
        }
    )
    _save_json(SESSION_FILE, sessions_data)
    return token


def get_session_user(token: str):
    sessions_data = _load_json(SESSION_FILE, {"sessions": []})
    sessions_data.setdefault("sessions", [])
    now = datetime.now(timezone.utc)
    valid_sessions = []
    for session in sessions_data.get("sessions", []):
        expires_at = datetime.fromisoformat(session.get("expires_at", _now()))
        if expires_at > now:
            valid_sessions.append(session)
            if session.get("token") == token:
                return session
    sessions_data["sessions"] = valid_sessions
    _save_json(SESSION_FILE, sessions_data)
    return None


def destroy_session(token: str):
    sessions_data = _load_json(SESSION_FILE, {"sessions": []})
    sessions_data.setdefault("sessions", [])
    sessions_data["sessions"] = [s for s in sessions_data["sessions"] if s.get("token") != token]
    _save_json(SESSION_FILE, sessions_data)


def record_music_archive(title: str, url: str | None = None, file_path: str | None = None, source: str = "telegram"):
    archive_data = _load_json(ARCHIVE_FILE, {"songs": []})
    archive_data.setdefault("songs", [])
    song = {
        "id": secrets.token_hex(6),
        "title": title or "Untitled track",
        "source": source,
        "url": url,
        "file_path": file_path,
        "added_at": _now(),
    }
    archive_data["songs"].append(song)
    archive_data["songs"] = archive_data["songs"][-120:]
    _save_json(ARCHIVE_FILE, archive_data)
    append_log("music", "Archived music entry", {"title": song["title"], "source": source}, user="system")
    return song


def list_music_archive(search: str | None = None):
    archive_data = _load_json(ARCHIVE_FILE, {"songs": []})
    songs = archive_data.get("songs", [])
    if search:
        query = search.lower()
        songs = [song for song in songs if query in str(song.get("title", "")).lower() or query in str(song.get("source", "")).lower()]
    return sorted(songs, key=lambda item: item.get("added_at", ""), reverse=True)


def append_log(category: str, message: str, details: dict | None = None, user: str | None = None):
    logs_data = _load_json(LOGS_FILE, {"logs": []})
    logs_data.setdefault("logs", [])
    entry = {
        "id": secrets.token_hex(5),
        "timestamp": _now(),
        "category": category,
        "message": message,
        "details": details or {},
        "user": user or "system",
    }
    logs_data["logs"].append(entry)
    logs_data["logs"] = logs_data["logs"][-300:]
    _save_json(LOGS_FILE, logs_data)
    return entry


def get_logs(category: str | None = None, search: str | None = None, limit: int = 120):
    logs_data = _load_json(LOGS_FILE, {"logs": []})
    logs = logs_data.get("logs", [])
    if category:
        logs = [entry for entry in logs if entry.get("category") == category]
    if search:
        needle = search.lower()
        logs = [entry for entry in logs if needle in str(entry.get("message", "")).lower() or needle in str(entry.get("category", "")).lower()]
    return sorted(logs, key=lambda item: item.get("timestamp", ""), reverse=True)[:limit]
