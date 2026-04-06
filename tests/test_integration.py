import random
import string
import time

import httpx

BASE = "http://127.0.0.1:8006"

HEADERS = {"X-Request-Id": "test-request"}


def _rnd(n: int = 6) -> str:
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def test_health():
    last_error = None

    for _ in range(30):
        try:
            r = httpx.get(f"{BASE}/health", timeout=5, headers=HEADERS)
            assert r.status_code == 200
            return
        except Exception as exc:
            last_error = exc
            time.sleep(1)

    raise AssertionError(f"Health check failed after waiting: {last_error}")


def test_auth_flow_refresh_logout_history_rbac():
    login = f"user_{_rnd()}"
    password = f"Pass_{_rnd()}!"
    email = f"{login}@test.local"

    r = httpx.post(
        f"{BASE}/api/v1/auth/signup",
        json={"login": login, "password": password, "email": email},
        timeout=10,
        headers=HEADERS,
    )
    assert r.status_code in (200, 201), r.text

    r = httpx.post(
        f"{BASE}/api/v1/auth/login",
        json={"login": login, "password": password},
        timeout=10,
        headers=HEADERS,
    )
    assert r.status_code == 200, r.text
    tokens = r.json()

    access = tokens["access_token"]
    refresh1 = tokens["refresh_token"]
    headers = {**HEADERS, "Authorization": f"Bearer {access}"}

    r = httpx.get(f"{BASE}/api/v1/auth/profile", headers=headers, timeout=10)
    assert r.status_code == 200, r.text
    user_id = r.json()["id"]

    r = httpx.post(
        f"{BASE}/api/v1/auth/refresh",
        json={"refresh_token": refresh1},
        timeout=10,
        headers=HEADERS,
    )
    assert r.status_code == 200, r.text
    refresh2 = r.json().get("refresh_token")
    assert refresh2 and refresh2 != refresh1

    r = httpx.post(
        f"{BASE}/api/v1/auth/refresh",
        json={"refresh_token": refresh1},
        timeout=10,
        headers=HEADERS,
    )
    assert r.status_code in (401, 403), r.text

    r = httpx.post(
        f"{BASE}/api/v1/auth/logout",
        json={"refresh_token": refresh2},
        timeout=10,
        headers=HEADERS,
    )
    assert r.status_code == 200, r.text

    r = httpx.post(
        f"{BASE}/api/v1/auth/refresh",
        json={"refresh_token": refresh2},
        timeout=10,
        headers=HEADERS,
    )
    assert r.status_code in (401, 403), r.text

    r = httpx.get(f"{BASE}/api/v1/auth/login-history", headers=headers, timeout=10)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 1

    r = httpx.get(f"{BASE}/api/v1/roles", headers=headers, timeout=10)
    assert r.status_code in (401, 403), r.text

    admin_login = "admin"
    admin_password = "Admin_123!"

    r = httpx.post(
        f"{BASE}/api/v1/auth/login",
        json={"login": admin_login, "password": admin_password},
        timeout=10,
        headers=HEADERS,
    )
    assert r.status_code == 200, r.text
    admin_access = r.json()["access_token"]
    admin_headers = {**HEADERS, "Authorization": f"Bearer {admin_access}"}

    role_name = f"role_{_rnd()}"
    r = httpx.post(f"{BASE}/api/v1/roles", json={"name": role_name}, headers=admin_headers, timeout=10)
    assert r.status_code in (200, 201), r.text

    r = httpx.post(
        f"{BASE}/api/v1/roles/assign",
        json={"user_id": user_id, "role_name": role_name},
        headers=admin_headers,
        timeout=10,
    )
    assert r.status_code == 200, r.text

    r = httpx.post(
        f"{BASE}/api/v1/roles/check",
        json={"user_id": user_id, "role_name": role_name},
        headers=admin_headers,
        timeout=10,
    )
    assert r.status_code == 200, r.text
    assert r.json().get("has_role") is True

    r = httpx.post(
        f"{BASE}/api/v1/roles/revoke",
        json={"user_id": user_id, "role_name": role_name},
        headers=admin_headers,
        timeout=10,
    )
    assert r.status_code == 200, r.text


def test_change_password():
    login = f"user_pw_{_rnd()}"
    password_old = f"Old_{_rnd()}!"
    password_new = f"New_{_rnd()}!"
    email = f"{login}@test.local"

    r = httpx.post(
        f"{BASE}/api/v1/auth/signup",
        json={"login": login, "password": password_old, "email": email},
        timeout=10,
        headers=HEADERS,
    )
    assert r.status_code in (200, 201)

    r = httpx.post(
        f"{BASE}/api/v1/auth/login",
        json={"login": login, "password": password_old, "email": email},
        timeout=10,
        headers=HEADERS,
    )
    assert r.status_code == 200
    access = r.json()["access_token"]

    r = httpx.put(
        f"{BASE}/api/v1/users/me/password",
        headers={**HEADERS, "Authorization": f"Bearer {access}"},
        json={"old_password": password_old, "new_password": password_new},
        timeout=10,
    )
    assert r.status_code == 204

    r = httpx.post(
        f"{BASE}/api/v1/auth/login",
        json={"login": login, "password": password_old, "email": email},
        timeout=10,
        headers=HEADERS,
    )
    assert r.status_code == 401

    r = httpx.post(
        f"{BASE}/api/v1/auth/login",
        json={"login": login, "password": password_new, "email": email},
        timeout=10,
        headers=HEADERS,
    )
    assert r.status_code == 200


def test_change_login():
    login_old = f"user_login_{_rnd()}"
    login_new = f"user_login_new_{_rnd()}"
    password = f"Pass_{_rnd()}!"
    email = f"{login_old}@test.local"

    r = httpx.post(
        f"{BASE}/api/v1/auth/signup",
        json={"login": login_old, "password": password, "email": email},
        timeout=10,
        headers=HEADERS,
    )
    assert r.status_code in (200, 201)

    r = httpx.post(
        f"{BASE}/api/v1/auth/login",
        json={"login": login_old, "password": password, "email": email},
        timeout=10,
        headers=HEADERS,
    )
    assert r.status_code == 200
    access = r.json()["access_token"]

    r = httpx.put(
        f"{BASE}/api/v1/users/me/login",
        headers={**HEADERS, "Authorization": f"Bearer {access}"},
        json={"new_login": login_new},
        timeout=10,
    )
    assert r.status_code == 204

    r = httpx.post(
        f"{BASE}/api/v1/auth/login",
        json={"login": login_old, "password": password, "email": email},
        timeout=10,
        headers=HEADERS,
    )
    assert r.status_code == 401

    r = httpx.post(
        f"{BASE}/api/v1/auth/login",
        json={"login": login_new, "password": password, "email": email},
        timeout=10,
        headers=HEADERS,
    )
    assert r.status_code == 200

