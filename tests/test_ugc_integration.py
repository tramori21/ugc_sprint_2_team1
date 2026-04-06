import subprocess
import time
from uuid import uuid4

import pytest
import requests
from jose import jwt

UGC_API_URL = "http://127.0.0.1:8010"
CLICKHOUSE_CONTAINER = "clickhouse"
CLICKHOUSE_USER = "app"
CLICKHOUSE_PASSWORD = "app_pass"
JWT_SECRET = "change_me"
JWT_ALGORITHM = "HS256"


def wait_ugc_api(timeout: int = 60) -> None:
    last_error = None

    for _ in range(timeout):
        try:
            response = requests.get(f"{UGC_API_URL}/health", timeout=5)
            if response.status_code == 200:
                return
        except Exception as exc:
            last_error = exc
        time.sleep(1)

    raise AssertionError(f"UGC API is not ready: {last_error}")


def clickhouse_query(query: str) -> str:
    result = subprocess.run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "clickhouse",
            "clickhouse-client",
            "--user",
            "app",
            "--password",
            "app_pass",
            "--query",
            query,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


@pytest.mark.integration
def test_ugc_event_flows_to_clickhouse() -> None:
    wait_ugc_api()

    request_id = f"req-test-{uuid4()}"
    movie_id = f"film-test-{uuid4()}"
    user_id = f"user-test-{uuid4()}"
    event_time = "2026-03-25T13:00:00+00:00"

    token = jwt.encode({"sub": user_id}, JWT_SECRET, algorithm=JWT_ALGORITHM)

    response = requests.post(
        f"{UGC_API_URL}/api/v1/events",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Request-Id": request_id,
            "Content-Type": "application/json",
        },
        json={
            "movie_id": movie_id,
            "event_type": "view",
            "progress_seconds": 777,
            "event_time": event_time,
        },
        timeout=10,
    )

    assert response.status_code == 202, response.text
    payload = response.json()
    assert payload["status"] == "accepted"
    assert payload["event_id"]

    found = False
    last_result = ""

    for _ in range(30):
        last_result = clickhouse_query(
            "SELECT user_id, movie_id, event_type, progress_seconds, request_id "
            "FROM ugc.views "
            f"WHERE request_id = '{request_id}' "
            "ORDER BY event_time DESC LIMIT 1"
        )
        if last_result:
            found = True
            break
        time.sleep(1)

    assert found, f"Row was not written to ClickHouse. Last result: {last_result}"

    parts = last_result.split()
    assert parts[0] == user_id
    assert parts[1] == movie_id
    assert parts[2] == "view"
    assert parts[3] == "777"
    assert parts[4] == request_id

