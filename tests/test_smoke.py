"""Existing smoke checks: core happy paths only, not a release acceptance suite."""

import http.cookiejar
import json
import tempfile
import threading
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener

from app.server import ApplicationServer, SHANGHAI, Store


class ExistingSmokeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.server = ApplicationServer(("127.0.0.1", 0), Store(Path(self.temp.name) / "smoke.sqlite"))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.client = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def request(self, path, method="GET", data=None):
        body = None if data is None else json.dumps(data).encode()
        request = Request(self.base + path, data=body, method=method,
                          headers={"Content-Type": "application/json", "X-Meeting-App": "1"})
        try:
            response = self.client.open(request, timeout=10)
        except HTTPError as error:
            response = error
        with response:
            return response.status, json.loads(response.read())

    def login(self, name):
        status, _ = self.request("/api/login", "POST", {"email": f"{name}@meetspace.test", "password": "MeetSpace!2026"})
        self.assertEqual(status, 200)

    def test_service_and_login_boundary(self):
        status, health = self.request("/api/health")
        self.assertEqual((status, health["status"]), (200, "ok"))
        status, _ = self.request("/api/rooms")
        self.assertEqual(status, 401)
        self.login("alice")
        status, session = self.request("/api/session")
        self.assertEqual((status, session["user"]["role"]), (200, "member"))
        self.assertEqual(self.request("/api/logout", "POST", {})[0], 200)
        self.assertEqual(self.request("/api/session")[0], 401)

    def test_member_booking_and_cancellation(self):
        self.login("alice")
        day = (datetime.now(SHANGHAI).date() + timedelta(days=1)).isoformat()
        status, rooms = self.request(f"/api/rooms?date={day}")
        self.assertEqual(status, 200)
        self.assertEqual(len(rooms["rooms"]), 4)
        payload = {"room_id": 4, "title": "冒烟测试：项目讨论", "attendees": 3,
                   "start": f"{day}T09:00:00+08:00", "end": f"{day}T10:00:00+08:00",
                   "idempotency_key": "existing-smoke-booking"}
        status, result = self.request("/api/bookings", "POST", payload)
        self.assertEqual(status, 201)
        booking_id = result["booking"]["id"]
        _, bookings = self.request("/api/bookings")
        self.assertTrue(any(b["id"] == booking_id and b["status"] == "confirmed" for b in bookings["bookings"]))
        self.assertEqual(self.request(f"/api/bookings/{booking_id}/cancel", "POST", {})[0], 200)
        _, bookings = self.request("/api/bookings")
        self.assertEqual(next(b for b in bookings["bookings"] if b["id"] == booking_id)["status"], "cancelled")
        _, notices = self.request("/api/notifications")
        self.assertEqual(len([n for n in notices["notifications"] if n["booking_id"] == booking_id]), 2)

    def test_admin_room_management(self):
        self.login("admin")
        payload = {"name": "冒烟测试空间", "location": "4F", "capacity": 5, "equipment": ["白板"], "active": True}
        status, result = self.request("/api/rooms", "POST", payload)
        self.assertEqual(status, 201)
        room_id = result["room"]["id"]
        self.assertEqual(self.request(f"/api/rooms/{room_id}", "PATCH", {**payload, "active": False})[0], 200)
        _, rooms = self.request("/api/rooms")
        self.assertFalse(next(r for r in rooms["rooms"] if r["id"] == room_id)["active"])
        status, members = self.request("/api/members")
        self.assertEqual(status, 200)
        self.assertEqual(len(members["members"]), 3)


if __name__ == "__main__":
    unittest.main()
