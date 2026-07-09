"""Backend tests for Serenity Farmhouse Phase 2 API.
Tests: health, property, media, reviews, pricing rules, blocked dates,
auth (JWT), bookings (create/list/status), admin CRUD, iCal export.
"""
import os
from datetime import date, timedelta

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Fallback to frontend/.env
    from pathlib import Path
    envp = Path("/app/frontend/.env")
    if envp.exists():
        for line in envp.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@serenityfarm.com"
ADMIN_PASSWORD = "admin123"


# ---------- Fixtures ----------
@pytest.fixture(scope="session")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def admin_token(api_client):
    r = api_client.post(f"{API}/auth/login",
                        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    tok = r.json().get("access_token")
    assert tok
    return tok


@pytest.fixture(scope="session")
def auth_client(api_client, admin_token):
    s = requests.Session()
    s.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {admin_token}",
    })
    return s


def d(offset):
    return (date.today() + timedelta(days=offset)).isoformat()


# ---------- Health ----------
class TestHealth:
    def test_health(self, api_client):
        r = api_client.get(f"{API}/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


# ---------- Public content ----------
class TestPublicContent:
    def test_property_seed(self, api_client):
        r = api_client.get(f"{API}/property")
        assert r.status_code == 200
        p = r.json()
        assert p["name"] == "Serenity Farmhouse"
        assert p["maxGuests"] == 14
        assert p["basePricePerNight"] == 18500
        assert "tagline" in p and p["tagline"]
        assert "amenities" in p and len(p["amenities"]) > 0
        assert "faqs" in p and len(p["faqs"]) > 0

    def test_media_seed(self, api_client):
        r = api_client.get(f"{API}/media")
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 12, f"expected 12 media items, got {len(items)}"
        hero_items = [m for m in items if m.get("isHero")]
        assert len(hero_items) == 1, f"expected exactly 1 hero, got {len(hero_items)}"
        cats = {m["category"] for m in items}
        for c in ["Exterior", "Pool", "Rooms"]:
            assert c in cats

    def test_reviews_seed(self, api_client):
        r = api_client.get(f"{API}/reviews")
        assert r.status_code == 200
        reviews = r.json()
        assert len(reviews) == 3
        for rv in reviews:
            assert "name" in rv and "rating" in rv and "quote" in rv

    def test_pricing_rules_seed(self, api_client):
        r = api_client.get(f"{API}/pricing-rules")
        assert r.status_code == 200
        rules = r.json()
        assert len(rules) >= 3

    def test_blocked_dates_seed(self, api_client):
        r = api_client.get(f"{API}/blocked-dates")
        assert r.status_code == 200
        blocked = r.json()
        # 7 seeded dates minimum; other tests may add. Verify sources contain both direct + airbnb
        sources = {b["source"] for b in blocked}
        assert "direct" in sources
        assert "airbnb" in sources


# ---------- Auth ----------
class TestAuth:
    def test_login_success(self, api_client):
        r = api_client.post(f"{API}/auth/login",
                            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        assert r.status_code == 200
        j = r.json()
        assert "access_token" in j and isinstance(j["access_token"], str)
        assert j["user"]["email"] == ADMIN_EMAIL
        assert j["user"]["role"] == "admin"

    def test_login_wrong_password(self, api_client):
        r = api_client.post(f"{API}/auth/login",
                            json={"email": ADMIN_EMAIL, "password": "wrong-pass"})
        assert r.status_code == 401

    def test_me_with_token(self, auth_client):
        r = auth_client.get(f"{API}/auth/me")
        assert r.status_code == 200
        assert r.json()["email"] == ADMIN_EMAIL

    def test_me_without_token(self, api_client):
        r = api_client.get(f"{API}/auth/me")
        assert r.status_code == 401

    def test_bookings_requires_auth(self, api_client):
        r = api_client.get(f"{API}/bookings")
        assert r.status_code == 401

    def test_bookings_list_authed(self, auth_client):
        r = auth_client.get(f"{API}/bookings")
        assert r.status_code == 200
        bookings = r.json()
        assert len(bookings) >= 5


# ---------- Booking Creation (public) ----------
class TestBookingCreation:
    def test_create_online_confirmed(self, api_client):
        # Use dates far in the future to avoid blocked / other bookings
        ci, co = d(200), d(202)
        payload = {
            "guestName": "TEST_Online Guest",
            "guestEmail": "test_online@example.com",
            "guestPhone": "+91 99999 00001",
            "checkIn": ci, "checkOut": co,
            "guests": 4, "totalAmount": 45000,
            "paymentMode": "online",
        }
        r = api_client.post(f"{API}/bookings", json=payload)
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["id"].startswith("BK-")
        assert j["bookingStatus"] == "confirmed"
        assert j["paymentStatus"] == "paid"

    def test_create_offline_pending(self, api_client):
        ci, co = d(210), d(212)
        payload = {
            "guestName": "TEST_Offline Guest",
            "guestEmail": "test_offline@example.com",
            "guestPhone": "+91 99999 00002",
            "checkIn": ci, "checkOut": co,
            "guests": 3, "totalAmount": 40000,
            "paymentMode": "offline",
        }
        r = api_client.post(f"{API}/bookings", json=payload)
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["bookingStatus"] == "pending"
        assert j["paymentStatus"] == "pending"

    def test_create_invalid_dates(self, api_client):
        r = api_client.post(f"{API}/bookings", json={
            "guestName": "TEST_Bad",
            "guestEmail": "test_bad@example.com",
            "guestPhone": "+91 99999 00003",
            "checkIn": d(220), "checkOut": d(220),  # same day
            "guests": 2, "totalAmount": 20000, "paymentMode": "offline",
        })
        assert r.status_code == 400

    def test_create_conflicts_with_blocked(self, api_client):
        # Use one of seeded blocked dates. Seed has date_offset(7) as blocked (direct).
        r = api_client.post(f"{API}/bookings", json={
            "guestName": "TEST_Conflict",
            "guestEmail": "test_conflict@example.com",
            "guestPhone": "+91 99999 00004",
            "checkIn": d(7), "checkOut": d(9),
            "guests": 2, "totalAmount": 20000, "paymentMode": "offline",
        })
        assert r.status_code == 409, f"expected 409 got {r.status_code}: {r.text}"


# ---------- Booking Status update ----------
class TestBookingStatus:
    def test_status_requires_auth(self, api_client):
        r = api_client.patch(f"{API}/bookings/BK-2043/status",
                             json={"bookingStatus": "confirmed"})
        assert r.status_code == 401

    def test_confirm_pending_auto_blocks(self, auth_client):
        # Fetch bookings, find pending
        r = auth_client.get(f"{API}/bookings")
        pending = [b for b in r.json() if b["bookingStatus"] == "pending"]
        if not pending:
            # Create one to confirm
            ci, co = d(250), d(252)
            cr = auth_client.post(f"{API}/bookings", json={
                "guestName": "TEST_ToConfirm",
                "guestEmail": "test_toconfirm@example.com",
                "guestPhone": "+91 99999 00099",
                "checkIn": ci, "checkOut": co,
                "guests": 2, "totalAmount": 22000, "paymentMode": "offline",
            })
            assert cr.status_code == 200
            bid = cr.json()["id"]
            ci_use = ci
        else:
            bid = pending[0]["id"]
            ci_use = pending[0]["checkIn"]

        r = auth_client.patch(f"{API}/bookings/{bid}/status",
                              json={"bookingStatus": "confirmed"})
        assert r.status_code == 200, r.text
        assert r.json()["bookingStatus"] == "confirmed"

        # Verify blocked date now exists
        br = auth_client.get(f"{API}/blocked-dates")
        assert br.status_code == 200
        blocked_dates = {b["date"] for b in br.json()}
        assert ci_use in blocked_dates


# ---------- Pricing Rules CRUD ----------
class TestPricingRules:
    def test_create_and_delete(self, auth_client):
        r = auth_client.post(f"{API}/pricing-rules", json={
            "startDate": d(100), "endDate": d(103),
            "pricePerNight": 22222, "label": "TEST_Rule",
        })
        assert r.status_code == 200, r.text
        rid = r.json()["id"]
        assert rid

        # Verify listed
        lr = auth_client.get(f"{API}/pricing-rules")
        assert any(x["id"] == rid for x in lr.json())

        dr = auth_client.delete(f"{API}/pricing-rules/{rid}")
        assert dr.status_code == 200

    def test_create_requires_auth(self, api_client):
        r = api_client.post(f"{API}/pricing-rules", json={
            "startDate": d(105), "endDate": d(106),
            "pricePerNight": 20000, "label": "TEST_NoAuth",
        })
        assert r.status_code == 401


# ---------- Blocked Dates toggle ----------
class TestBlockedDates:
    def test_toggle_idempotent(self, auth_client):
        target = d(365)
        # Ensure not blocked
        r1 = auth_client.post(f"{API}/blocked-dates/toggle", json={"date": target})
        assert r1.status_code == 200
        # Toggle back
        r2 = auth_client.post(f"{API}/blocked-dates/toggle", json={"date": target})
        assert r2.status_code == 200
        assert r1.json()["blocked"] != r2.json()["blocked"]


# ---------- Media CRUD ----------
class TestMedia:
    def test_create_set_hero_delete(self, auth_client):
        cr = auth_client.post(f"{API}/media", json={
            "type": "image",
            "category": "Exterior",
            "url": "https://example.com/test_media.jpg",
            "alt": "TEST_media",
            "isHero": False,
        })
        assert cr.status_code == 200, cr.text
        mid = cr.json()["id"]

        # Set as hero
        hr = auth_client.patch(f"{API}/media/{mid}/hero")
        assert hr.status_code == 200

        # Verify sole hero
        listr = auth_client.get(f"{API}/media")
        heroes = [m for m in listr.json() if m.get("isHero")]
        assert len(heroes) == 1 and heroes[0]["id"] == mid

        # Delete
        dr = auth_client.delete(f"{API}/media/{mid}")
        assert dr.status_code == 200


# ---------- iCal export ----------
class TestICal:
    def test_export_ical(self, api_client):
        r = api_client.get(f"{API}/ical/export.ics")
        assert r.status_code == 200
        ctype = r.headers.get("content-type", "")
        assert "text/calendar" in ctype, ctype
        body = r.text
        assert "BEGIN:VCALENDAR" in body
        assert "END:VCALENDAR" in body
        assert "BEGIN:VEVENT" in body
