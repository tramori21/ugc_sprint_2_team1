import random
import string
import time

import httpx

BASE = "http://127.0.0.1:8006"
HEADERS = {"X-Request-Id": "ugc-crud-test"}


def _rnd(n: int = 6) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(n))


def wait_auth(timeout: int = 60) -> None:
    last_error = None

    for _ in range(timeout):
        try:
            response = httpx.get(f"{BASE}/health", timeout=5, headers=HEADERS)
            if response.status_code == 200:
                return
        except Exception as exc:
            last_error = exc
        time.sleep(1)

    raise AssertionError(f"Auth API is not ready: {last_error}")


def _signup_and_login() -> dict:
    login = f"ugc_user_{_rnd()}"
    password = f"Pass_{_rnd()}!"

    response = httpx.post(
        f"{BASE}/api/v1/auth/signup",
        json={"login": login, "password": password},
        timeout=10,
        headers=HEADERS,
    )
    assert response.status_code in (200, 201), response.text

    payload = response.json()
    token = payload["access_token"]
    auth_headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    return auth_headers


def test_ugc_crud_flow():
    wait_auth()
    auth_headers = _signup_and_login()

    movie_id = f"film_{_rnd()}"
    review_movie_id = f"film_{_rnd()}"

    response = httpx.post(
        f"{BASE}/api/v1/ugc/bookmarks",
        json={"movie_id": movie_id},
        timeout=10,
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text

    response = httpx.get(
        f"{BASE}/api/v1/ugc/bookmarks",
        timeout=10,
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    assert any(item["movie_id"] == movie_id for item in response.json())

    response = httpx.post(
        f"{BASE}/api/v1/ugc/likes",
        json={"movie_id": movie_id},
        timeout=10,
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text

    response = httpx.get(
        f"{BASE}/api/v1/ugc/likes/{movie_id}",
        timeout=10,
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["movie_id"] == movie_id

    response = httpx.post(
        f"{BASE}/api/v1/ugc/reviews",
        json={"movie_id": review_movie_id, "text": "good movie", "rating": 8},
        timeout=10,
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text
    review_id = response.json()["id"]

    response = httpx.put(
        f"{BASE}/api/v1/ugc/reviews/{review_id}",
        json={"text": "very good movie", "rating": 9},
        timeout=10,
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["rating"] == 9

    response = httpx.get(
        f"{BASE}/api/v1/ugc/reviews",
        timeout=10,
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    assert any(item["id"] == review_id for item in response.json())

    response = httpx.delete(
        f"{BASE}/api/v1/ugc/reviews/{review_id}",
        timeout=10,
        headers=auth_headers,
    )
    assert response.status_code == 204, response.text

    response = httpx.delete(
        f"{BASE}/api/v1/ugc/likes/{movie_id}",
        timeout=10,
        headers=auth_headers,
    )
    assert response.status_code == 204, response.text

    response = httpx.delete(
        f"{BASE}/api/v1/ugc/bookmarks/{movie_id}",
        timeout=10,
        headers=auth_headers,
    )
    assert response.status_code == 204, response.text
