"""Real HTTP regression checks for defects found by acceptance scenarios."""
import json
import sqlite3
import unittest
from datetime import datetime, timedelta
from urllib.request import Request
from urllib.error import HTTPError
import test_smoke as smoke


class ReleaseRegressionTests(unittest.TestCase):
    setUp = smoke.ExistingSmokeTests.setUp
    tearDown = smoke.ExistingSmokeTests.tearDown
    request = smoke.ExistingSmokeTests.request
    login = smoke.ExistingSmokeTests.login

    def booking_payload(self):
        day = (datetime.now(smoke.SHANGHAI).date() + timedelta(days=2)).isoformat()
        return {"room_id": 4, "title": "完整时段与重放回归", "attendees": 2,
                "start": f"{day}T10:00:00+08:00", "end": f"{day}T11:00:00+08:00",
                "idempotency_key": "release-regression"}

    def test_explicit_empty_date_is_rejected(self):
        self.login("alice")
        self.assertEqual(self.request("/api/rooms")[0], 200)
        self.assertEqual(self.request("/api/rooms?date=")[0], 400)

    def test_subsecond_replay_differs_but_equivalent_time_replays(self):
        self.login("alice")
        payload = self.booking_payload()
        status, created = self.request("/api/bookings", "POST", payload)
        self.assertEqual(status, 201)
        for field in ("start", "end"):
            changed = {**payload, field: payload[field].replace(":00+08:00", ":00.000001+08:00")}
            status, rejected = self.request("/api/bookings", "POST", changed)
            self.assertEqual((status, rejected["code"]), (409, "idempotency_conflict"))
        equivalent = {**payload, "title": "  " + payload["title"] + "  ",
                      "start": datetime.fromisoformat(payload["start"]).isoformat(timespec="microseconds")}
        status, replay = self.request("/api/bookings", "POST", equivalent)
        self.assertEqual(status, 201)
        self.assertEqual(replay["booking"]["id"], created["booking"]["id"])
        self.assertTrue(replay["booking"]["replayed"])
        self.assertEqual(len(self.request("/api/notifications")[1]["notifications"]), 1)

    def test_notification_has_numeric_date_and_full_interval(self):
        self.login("alice")
        payload = self.booking_payload()
        self.assertEqual(self.request("/api/bookings", "POST", payload)[0], 201)
        message = self.request("/api/notifications")[1]["notifications"][0]["message"]
        day = payload["start"][:10]
        self.assertIn(day[5:7] + "月" + day[8:10] + "日 10:00–11:00", message)

    def test_inherited_unsupported_methods_use_json_without_writes(self):
        self.login("alice")
        before = self.request("/api/bookings")[1]
        for method in ("DELETE", "OPTIONS", "PUT", "TRACE"):
            request = Request(self.base + "/api/bookings", method=method)
            with self.assertRaises(HTTPError) as caught:
                self.client.open(request)
            with caught.exception as response:
                self.assertEqual(response.status, 501)
                self.assertEqual(response.headers.get_content_type(), "application/json")
                self.assertEqual(json.loads(response.read())["code"], "method_not_allowed")
        self.assertEqual(self.request("/api/bookings")[1], before)

    def test_invalid_role_types_reject_without_writes_and_preserve_permissions(self):
        self.login("admin")

        def snapshot():
            with sqlite3.connect(self.temp.name + "/smoke.sqlite") as db:
                return {name: db.execute(f"SELECT * FROM {name} ORDER BY rowid").fetchall()
                        for name in ("teams", "users", "sessions", "rooms", "bookings", "notifications")}

        before = snapshot()
        for role in ([], {}, ["admin"], {"role": "admin"}, None, 0, True, "", "Admin", " admin", "member "):
            with self.subTest(role=role):
                status, body = self.request("/api/members/3", "PATCH", {"role": role})
                self.assertEqual((status, body["code"]), (400, "invalid_request"))
                self.assertEqual(snapshot(), before)
        self.assertEqual(self.request("/api/members/3", "PATCH", {})[0], 400)
        self.assertEqual(snapshot(), before)
        self.assertEqual(self.request("/api/members/1", "PATCH", {"role": "member"})[0], 409)
        for member in (4, 999):
            self.assertEqual(self.request(f"/api/members/{member}", "PATCH", {"role": "admin"})[0], 404)
        self.assertEqual(snapshot(), before)
        for role in ("admin", "member"):
            self.assertEqual(self.request("/api/members/3", "PATCH", {"role": role})[0], 200)
            members = self.request("/api/members")[1]["members"]
            self.assertEqual(next(m["role"] for m in members if m["id"] == 3), role)
        self.login("alice")
        before = snapshot()
        self.assertEqual(self.request("/api/members/3", "PATCH", {"role": []})[0], 403)
        self.assertEqual(snapshot(), before)
