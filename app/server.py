"""A dependency-free HTTP application backed by SQLite, for local release testing."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SHANGHAI = ZoneInfo("Asia/Shanghai")
UTC = timezone.utc
SESSION_SECONDS = 8 * 60 * 60
EQUIPMENT = {"显示屏", "白板", "视频会议", "电话会议"}
SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS teams (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, team_id INTEGER NOT NULL REFERENCES teams(id),
 email TEXT UNIQUE NOT NULL, name TEXT NOT NULL, role TEXT NOT NULL,
 password_hash TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), expires REAL NOT NULL);
CREATE TABLE IF NOT EXISTS rooms (
 id INTEGER PRIMARY KEY, team_id INTEGER NOT NULL REFERENCES teams(id),
 name TEXT NOT NULL, location TEXT NOT NULL, capacity INTEGER NOT NULL,
 equipment TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1,
 UNIQUE(team_id, name));
CREATE TABLE IF NOT EXISTS bookings (
 id INTEGER PRIMARY KEY, team_id INTEGER NOT NULL REFERENCES teams(id),
 room_id INTEGER NOT NULL REFERENCES rooms(id), user_id INTEGER NOT NULL REFERENCES users(id),
 title TEXT NOT NULL, start TEXT NOT NULL, end TEXT NOT NULL, attendees INTEGER NOT NULL,
 status TEXT NOT NULL DEFAULT 'confirmed', created_at TEXT NOT NULL, cancelled_at TEXT,
 idempotency_key TEXT NOT NULL, request_hash TEXT NOT NULL, UNIQUE(user_id, idempotency_key));
CREATE INDEX IF NOT EXISTS booking_room_time ON bookings(room_id, status, start, end);
CREATE TABLE IF NOT EXISTS notifications (
 id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
 booking_id INTEGER NOT NULL REFERENCES bookings(id), message TEXT NOT NULL,
 created_at TEXT NOT NULL, read INTEGER NOT NULL DEFAULT 0);
"""


class AppError(Exception):
    def __init__(self, status: int, message: str, code: str = "invalid_request"):
        super().__init__(message)
        self.status, self.message, self.code = status, message, code


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def password_hash(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    value = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
    return f"{salt}:{value}"


def password_matches(password: str, stored: str) -> bool:
    return hmac.compare_digest(password_hash(password, stored.split(":")[0]), stored)


def integer(value, name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise AppError(400, f"{name}须为 {minimum}–{maximum} 的整数")
    return value


def text_field(data: dict, key: str, label: str, maximum: int) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
        raise AppError(400, f"请填写{label}，最多 {maximum} 个字符")
    return value.strip()


def date_time(value) -> datetime:
    try:
        result = datetime.fromisoformat(value)
        if result.tzinfo is None or result.utcoffset() is None:
            raise ValueError
        return result.astimezone(UTC)
    except (ValueError, TypeError, OverflowError):
        raise AppError(400, "预约时间须包含时区", "invalid_time") from None


class Store:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript(SCHEMA)
        self.seed()

    @contextmanager
    def connect(self, write: bool = False):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def seed(self):
        with self.connect(write=True) as db:
            if db.execute("SELECT count(*) FROM teams").fetchone()[0]:
                return
            db.executemany("INSERT INTO teams VALUES (?, ?)", [(1, "见山设计"), (2, "远岸工作室")])
            accounts = [
                (1, 1, "admin@meetspace.test", "林可", "admin"),
                (2, 1, "alice@meetspace.test", "陈悦", "member"),
                (3, 1, "bob@meetspace.test", "周言", "member"),
                (4, 2, "other@meetspace.test", "许宁", "admin"),
            ]
            db.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
                           [(*user, password_hash("MeetSpace!2026")) for user in accounts])
            rooms = [
                (1, 1, "云杉", "3F · 东侧", 8, ["显示屏", "白板", "视频会议"], 1),
                (2, 1, "白桦", "3F · 西侧", 4, ["显示屏", "白板"], 1),
                (3, 1, "银杏", "2F · 开放区", 12, ["显示屏", "白板", "视频会议", "电话会议"], 1),
                (4, 1, "青松", "2F · 北侧", 6, ["白板", "电话会议"], 1),
                (5, 2, "海风", "1F · 靠窗", 6, ["白板"], 1),
            ]
            db.executemany("INSERT INTO rooms VALUES (?, ?, ?, ?, ?, ?, ?)",
                           [(*row[:5], json.dumps(row[5], ensure_ascii=False), row[6]) for row in rooms])
            tomorrow = datetime.now(SHANGHAI).date() + timedelta(days=1)
            for index, room_id, user_id, hour, title, attendees in [
                (1, 1, 2, 10, "品牌方向讨论", 6),
                (2, 3, 3, 14, "产品周会", 10),
                (3, 2, 1, 11, "设计评审", 3),
            ]:
                start = datetime(tomorrow.year, tomorrow.month, tomorrow.day, hour, tzinfo=SHANGHAI)
                db.execute("""INSERT INTO bookings
                    (id, team_id, room_id, user_id, title, start, end, attendees, created_at,
                     idempotency_key, request_hash) VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                           (index, room_id, user_id, title, start.astimezone(UTC).isoformat(timespec="seconds"),
                            (start + timedelta(hours=1)).astimezone(UTC).isoformat(timespec="seconds"),
                            attendees, now_iso(), f"seed-{index}", "seed"))


class ApplicationServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, store: Store):
        self.store = store
        self.login_attempts: dict[str, list[float]] = {}
        self.login_lock = threading.Lock()
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    server_version = "MeetSpace/1.0-rc1"

    def do_GET(self):
        self.dispatch()

    def do_POST(self):
        self.dispatch()

    def do_PATCH(self):
        self.dispatch()

    def do_HEAD(self):
        self.dispatch()

    def send_error(self, code, message=None, explain=None):
        if getattr(self, "path", "").startswith("/api/"):
            self.send_json(code, {
                "error": "请求方法不受支持" if code == 501 else "HTTP 请求无效",
                "code": "method_not_allowed" if code == 501 else "invalid_request",
            })
        else:
            super().send_error(code, message, explain)

    def send_json(self, status: int, data: dict, cookie: str | None = None):
        payload = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    def read_json(self) -> dict:
        if self.headers.get("X-Meeting-App") != "1":
            raise AppError(403, "请求来源无效", "invalid_origin")
        origin = self.headers.get("Origin")
        if origin and origin != f"http://{self.headers.get('Host')}":
            raise AppError(403, "请求来源无效", "invalid_origin")
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            raise AppError(415, "请使用 JSON 请求")
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 65536:
                raise ValueError
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError
            return data
        except (ValueError, UnicodeDecodeError):
            raise AppError(400, "请求内容无效") from None

    def current_user(self, db) -> dict:
        cookies = SimpleCookie()
        try:
            cookies.load(self.headers.get("Cookie", ""))
            token = cookies["meetspace_session"].value
        except (KeyError, ValueError):
            raise AppError(401, "请先登录", "unauthenticated") from None
        row = db.execute("""SELECT u.id, u.team_id, u.email, u.name, u.role, t.name AS team_name
            FROM sessions s JOIN users u ON u.id=s.user_id JOIN teams t ON t.id=u.team_id
            WHERE s.token_hash=? AND s.expires>?""",
                         (hashlib.sha256(token.encode()).hexdigest(), time.time())).fetchone()
        if not row:
            raise AppError(401, "登录已过期，请重新登录", "unauthenticated")
        return dict(row)

    @staticmethod
    def admin(user):
        if user["role"] != "admin":
            raise AppError(403, "仅管理员可以执行此操作", "forbidden")

    def dispatch(self):
        try:
            path = urlparse(self.path).path
            query = parse_qs(urlparse(self.path).query, keep_blank_values=True)
            if not path.startswith("/api/"):
                return self.static_file(path)
            if self.command == "GET" and path == "/api/health":
                with self.server.store.connect() as db:
                    db.execute("SELECT 1").fetchone()
                return self.send_json(200, {"status": "ok", "version": "1.0.0-rc.1", "timezone": "Asia/Shanghai"})
            data = self.read_json() if self.command in {"POST", "PATCH"} else {}
            if self.command == "POST" and path == "/api/login":
                return self.login(data)
            with self.server.store.connect(write=self.command in {"POST", "PATCH"}) as db:
                user = self.current_user(db)
                status, response, cookie = self.api(db, user, path, query, data)
            return self.send_json(status, response, cookie)
        except AppError as exc:
            self.send_json(exc.status, {"error": exc.message, "code": exc.code})
        except sqlite3.IntegrityError:
            self.send_json(409, {"error": "数据与现有记录冲突，请刷新后重试", "code": "data_conflict"})
        except sqlite3.OperationalError:
            self.send_json(503, {"error": "数据服务暂时不可用，请稍后重试", "code": "storage_unavailable"})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as exc:
            self.log_error("Unexpected application error: %s", type(exc).__name__)
            self.send_json(500, {"error": "服务发生错误，请稍后重试", "code": "internal_error"})

    def static_file(self, path: str):
        files = {"/": ("index.html", "text/html; charset=utf-8"),
                 "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                 "/style.css": ("style.css", "text/css; charset=utf-8")}
        if self.command not in {"GET", "HEAD"} or path not in files:
            raise AppError(404, "页面不存在", "not_found")
        filename, content_type = files[path]
        payload = (ROOT / "web" / filename).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    def login(self, data):
        email = text_field(data, "email", "邮箱", 160).lower()
        password = text_field(data, "password", "密码", 256)
        attempt_key = self.client_address[0]
        with self.server.login_lock:
            attempts = [stamp for stamp in self.server.login_attempts.get(attempt_key, []) if stamp > time.time() - 60]
            if len(attempts) >= 8:
                raise AppError(429, "登录尝试过于频繁，请一分钟后重试", "rate_limited")
            attempts.append(time.time())
            self.server.login_attempts[attempt_key] = attempts
        with self.server.store.connect(write=True) as db:
            row = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            if not row or not password_matches(password, row["password_hash"]):
                raise AppError(401, "邮箱或密码不正确", "invalid_credentials")
            token = secrets.token_urlsafe(32)
            db.execute("DELETE FROM sessions WHERE expires<=?", (time.time(),))
            # Replace this browser's previous session when switching accounts.
            cookies = SimpleCookie()
            cookies.load(self.headers.get("Cookie", ""))
            if "meetspace_session" in cookies:
                db.execute("DELETE FROM sessions WHERE token_hash=?",
                           (hashlib.sha256(cookies["meetspace_session"].value.encode()).hexdigest(),))
            db.execute("INSERT INTO sessions VALUES (?, ?, ?)",
                       (hashlib.sha256(token.encode()).hexdigest(), row["id"], time.time() + SESSION_SECONDS))
        cookie = f"meetspace_session={token}; HttpOnly; SameSite=Lax; Path=/; Max-Age={SESSION_SECONDS}"
        self.send_json(200, {"ok": True}, cookie)

    def api(self, db, user, path, query, data):
        method = self.command
        if method == "GET" and path == "/api/session":
            return 200, {"user": user, "timezone": "Asia/Shanghai", "version": "1.0.0-rc.1"}, None
        if method == "POST" and path == "/api/logout":
            cookies = SimpleCookie(self.headers.get("Cookie", ""))
            db.execute("DELETE FROM sessions WHERE token_hash=?",
                       (hashlib.sha256(cookies["meetspace_session"].value.encode()).hexdigest(),))
            return 200, {"ok": True}, "meetspace_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0"
        if method == "GET" and path == "/api/rooms":
            rooms = [self.room_data(row) for row in db.execute("SELECT * FROM rooms WHERE team_id=? ORDER BY id", (user["team_id"],))]
            day = query.get("date", [datetime.now(SHANGHAI).date().isoformat()])[0]
            start, end = self.day_range(day)
            for room in rooms:
                reservations = db.execute("""SELECT b.id, b.user_id, b.title, b.start, b.end, u.name AS owner
                    FROM bookings b JOIN users u ON u.id=b.user_id WHERE b.room_id=?
                    AND b.status='confirmed' AND b.start<? AND b.end>? ORDER BY b.start""", (room["id"], end, start))
                room["bookings"] = [dict(row) for row in reservations]
                for booking in room["bookings"]:
                    if booking["user_id"] != user["id"] and user["role"] != "admin":
                        booking["title"] = "已预约"
            return 200, {"rooms": rooms, "date": day}, None
        if method == "GET" and path == "/api/bookings":
            scope = query.get("scope", ["mine"])[0]
            if scope not in {"mine", "team"}:
                raise AppError(400, "预约范围无效")
            if scope == "team":
                self.admin(user)
            sql = """SELECT b.*, r.name AS room_name, r.location, u.name AS owner
                     FROM bookings b JOIN rooms r ON r.id=b.room_id JOIN users u ON u.id=b.user_id
                     WHERE b.team_id=?"""
            parameters = [user["team_id"]]
            if scope == "mine":
                sql += " AND b.user_id=?"
                parameters.append(user["id"])
            rows = db.execute(sql + " ORDER BY b.start DESC, b.id DESC", parameters)
            return 200, {"bookings": [self.booking_data(row) for row in rows]}, None
        if method == "POST" and path == "/api/bookings":
            return 201, {"booking": self.create_booking(db, user, data)}, None
        match = re.fullmatch(r"/api/bookings/(\d+)/cancel", path)
        if method == "POST" and match:
            booking = db.execute("SELECT * FROM bookings WHERE id=? AND team_id=?", (int(match[1]), user["team_id"])).fetchone()
            if not booking:
                raise AppError(404, "预约不存在", "not_found")
            if booking["user_id"] != user["id"] and user["role"] != "admin":
                raise AppError(403, "只能取消自己的预约", "forbidden")
            if booking["status"] != "cancelled":
                if date_time(booking["start"]) <= datetime.now(UTC):
                    raise AppError(409, "已经开始的预约不能取消", "booking_started")
                db.execute("UPDATE bookings SET status='cancelled', cancelled_at=? WHERE id=?", (now_iso(), booking["id"]))
                self.notify(db, booking["user_id"], booking["id"], f"「{booking['title']}」已取消，会议室时段已释放。")
            return 200, {"ok": True}, None
        if method == "GET" and path == "/api/notifications":
            rows = db.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 100", (user["id"],))
            return 200, {"notifications": [dict(row) for row in rows]}, None
        if method == "POST" and path == "/api/notifications/read":
            db.execute("UPDATE notifications SET read=1 WHERE user_id=?", (user["id"],))
            return 200, {"ok": True}, None
        if method == "GET" and path == "/api/members":
            self.admin(user)
            rows = db.execute("SELECT id, email, name, role FROM users WHERE team_id=? ORDER BY id", (user["team_id"],))
            return 200, {"members": [dict(row) for row in rows]}, None
        match = re.fullmatch(r"/api/members/(\d+)", path)
        if method == "PATCH" and match:
            self.admin(user)
            role = data.get("role")
            if not isinstance(role, str) or role not in {"admin", "member"}:
                raise AppError(400, "角色无效")
            member = db.execute("SELECT * FROM users WHERE id=? AND team_id=?", (int(match[1]), user["team_id"])).fetchone()
            if not member:
                raise AppError(404, "成员不存在", "not_found")
            if member["role"] == "admin" and role == "member":
                count = db.execute("SELECT count(*) FROM users WHERE team_id=? AND role='admin'", (user["team_id"],)).fetchone()[0]
                if count <= 1:
                    raise AppError(409, "团队至少需要保留一位管理员", "last_admin")
            db.execute("UPDATE users SET role=? WHERE id=?", (role, member["id"]))
            return 200, {"ok": True}, None
        if method == "POST" and path == "/api/rooms":
            self.admin(user)
            values = self.room_values(data)
            cursor = db.execute("INSERT INTO rooms (team_id, name, location, capacity, equipment, active) VALUES (?, ?, ?, ?, ?, ?)", (user["team_id"], *values))
            return 201, {"room": self.room_data(db.execute("SELECT * FROM rooms WHERE id=?", (cursor.lastrowid,)).fetchone())}, None
        match = re.fullmatch(r"/api/rooms/(\d+)", path)
        if method == "PATCH" and match:
            self.admin(user)
            row = db.execute("SELECT * FROM rooms WHERE id=? AND team_id=?", (int(match[1]), user["team_id"])).fetchone()
            if not row:
                raise AppError(404, "会议室不存在", "not_found")
            values = self.room_values(data)
            db.execute("UPDATE rooms SET name=?, location=?, capacity=?, equipment=?, active=? WHERE id=?", (*values, row["id"]))
            return 200, {"ok": True}, None
        raise AppError(404, "接口不存在", "not_found")

    @staticmethod
    def room_data(row):
        room = dict(row)
        room["equipment"] = json.loads(room["equipment"])
        room["active"] = bool(room["active"])
        return room

    @staticmethod
    def booking_data(row):
        return {key: row[key] for key in ("id", "room_id", "user_id", "title", "start", "end", "attendees", "status", "created_at", "cancelled_at", "room_name", "location", "owner")}

    @staticmethod
    def day_range(day):
        try:
            value = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=SHANGHAI)
        except (ValueError, TypeError):
            raise AppError(400, "日期格式无效") from None
        return (value.astimezone(UTC).isoformat(timespec="seconds"),
                (value + timedelta(days=1)).astimezone(UTC).isoformat(timespec="seconds"))

    @staticmethod
    def room_values(data):
        name = text_field(data, "name", "会议室名称", 40)
        location = text_field(data, "location", "位置", 80)
        capacity = integer(data.get("capacity"), "容量", 1, 100)
        equipment = data.get("equipment")
        if not isinstance(equipment, list) or any(not isinstance(item, str) or item not in EQUIPMENT for item in equipment):
            raise AppError(400, "会议室设备无效")
        active = data.get("active", True)
        if not isinstance(active, bool):
            raise AppError(400, "会议室状态无效")
        return name, location, capacity, json.dumps(sorted(set(equipment)), ensure_ascii=False), int(active)

    def create_booking(self, db, user, data):
        room_id = integer(data.get("room_id"), "会议室编号", 1, 2147483647)
        title = text_field(data, "title", "会议主题", 100)
        attendees = integer(data.get("attendees"), "参会人数", 1, 100)
        key = text_field(data, "idempotency_key", "请求标识", 100)
        start, end = date_time(data.get("start")), date_time(data.get("end"))
        start_iso, end_iso = start.isoformat(timespec="seconds"), end.isoformat(timespec="seconds")
        fingerprint = hashlib.sha256(json.dumps([room_id, title, start.isoformat(), end.isoformat(), attendees], ensure_ascii=False).encode()).hexdigest()
        previous = db.execute("SELECT * FROM bookings WHERE user_id=? AND idempotency_key=?", (user["id"], key)).fetchone()
        if previous:
            if previous["request_hash"] != fingerprint:
                raise AppError(409, "同一请求标识不能用于不同预约", "idempotency_conflict")
            return {"id": previous["id"], "status": previous["status"], "replayed": True}
        current_time = datetime.now(UTC)
        if start <= current_time or start > current_time + timedelta(days=30):
            raise AppError(400, "请预约未来 30 天内的时段", "invalid_time")
        if not timedelta(minutes=15) <= end - start <= timedelta(hours=8):
            raise AppError(400, "预约时长须在 15 分钟至 8 小时之间", "invalid_duration")
        local_start, local_end = start.astimezone(SHANGHAI), end.astimezone(SHANGHAI)
        if local_start.date() != local_end.date() or local_start.hour < 8 or local_end.hour > 20 or (local_end.hour == 20 and (local_end.minute or local_end.second)):
            raise AppError(400, "预约须在同一天的 08:00–20:00 之间", "outside_hours")
        if any(value.minute % 15 or value.second or value.microsecond for value in (start, end)):
            raise AppError(400, "预约时间须以 15 分钟为间隔", "invalid_interval")
        room = db.execute("SELECT * FROM rooms WHERE id=? AND team_id=?", (room_id, user["team_id"])).fetchone()
        if not room:
            raise AppError(404, "会议室不存在", "not_found")
        if not room["active"]:
            raise AppError(409, "会议室已停用，请选择其他会议室", "room_inactive")
        if attendees > room["capacity"]:
            raise AppError(400, "参会人数超过会议室容量", "capacity_exceeded")
        conflict = db.execute("SELECT id FROM bookings WHERE room_id=? AND status='confirmed' AND start<? AND end>?", (room_id, end_iso, start_iso)).fetchone()
        if conflict:
            raise AppError(409, "这个时段已被预约，请选择其他时段", "time_conflict")
        cursor = db.execute("""INSERT INTO bookings
            (team_id, room_id, user_id, title, start, end, attendees, created_at, idempotency_key, request_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (user["team_id"], room_id, user["id"], title, start_iso, end_iso, attendees, now_iso(), key, fingerprint))
        meeting_time = (f"{local_start.month:02d}月{local_start.day:02d}日 "
                        f"{local_start.hour:02d}:{local_start.minute:02d}–"
                        f"{local_end.hour:02d}:{local_end.minute:02d}")
        self.notify(db, user["id"], cursor.lastrowid, f"「{title}」预约成功：{room['name']} · {meeting_time}。")
        return {"id": cursor.lastrowid, "status": "confirmed", "replayed": False}

    @staticmethod
    def notify(db, user_id, booking_id, message):
        db.execute("INSERT INTO notifications (user_id, booking_id, message, created_at) VALUES (?, ?, ?, ?)", (user_id, booking_id, message, now_iso()))


def main():
    parser = argparse.ArgumentParser(description="Run the local MeetSpace release candidate")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--db", type=Path, default=ROOT / "data" / "meetspace.sqlite")
    args = parser.parse_args()
    server = ApplicationServer((args.host, args.port), Store(args.db))
    print(f"MeetSpace 1.0.0-rc.1 · http://{args.host}:{server.server_port} · Asia/Shanghai", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
