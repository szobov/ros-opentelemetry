#!/usr/bin/env python3
from __future__ import annotations

import json
import logging
import os
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

LOG_LEVEL = os.environ.get("SIGNOZ_BOOTSTRAP_LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(message)s")

BASE_URL = os.environ.get("SIGNOZ_BOOTSTRAP_BASE_URL", "http://localhost:8181")
HEALTH_PATH = os.environ.get("SIGNOZ_BOOTSTRAP_HEALTH_PATH", "/api/v1/health")
LOGIN_PATH = os.environ.get("SIGNOZ_BOOTSTRAP_LOGIN_PATH", "/api/v1/login")
REGISTER_PATH = os.environ.get("SIGNOZ_BOOTSTRAP_REGISTER_PATH", "/api/v1/register")
EMAIL = os.environ.get("SIGNOZ_BOOTSTRAP_EMAIL", "test@ros-opentelemetry")
PASSWORD = os.environ.get(
    "SIGNOZ_BOOTSTRAP_PASSWORD", "test-opentelemetry-123"
)
ORG_DISPLAY_NAME = os.environ.get(
    "SIGNOZ_BOOTSTRAP_NAME", "ROS Telemetry Default"
)
HEALTH_ATTEMPTS = int(os.environ.get("SIGNOZ_BOOTSTRAP_HEALTH_ATTEMPTS", "60"))
HEALTH_INTERVAL = float(os.environ.get("SIGNOZ_BOOTSTRAP_HEALTH_INTERVAL", "5"))


def build_url(base: str, path: str) -> str:
    return urljoin(base.rstrip("/") + "/", path.lstrip("/"))


def wait_for_health(base_url: str) -> None:
    """Block until the SigNoz health endpoint responds with HTTP 2xx."""

    health_url = build_url(base_url, HEALTH_PATH)
    logging.info("Waiting for SigNoz health endpoint at %s", health_url)

    for attempt in range(1, HEALTH_ATTEMPTS + 1):
        try:
            with urlopen(health_url, timeout=5) as resp:  # noqa: S310
                status = getattr(resp, "status", resp.getcode())
                if 200 <= status < 300:
                    logging.info(
                        "SigNoz health check succeeded on attempt %s (status %s)",
                        attempt,
                        status,
                    )
                    return
                logging.info(
                    "Health check attempt %s returned status %s",
                    attempt,
                    status,
                )
        except (HTTPError, URLError, OSError) as exc:
            logging.debug(
                "Health check attempt %s/%s failed: %s",
                attempt,
                HEALTH_ATTEMPTS,
                exc,
            )
        time.sleep(HEALTH_INTERVAL)

    raise RuntimeError(
        f"SigNoz health endpoint {health_url} did not become ready after "
        f"{HEALTH_ATTEMPTS} attempts"
    )


def post_json(base_url: str, path: str, payload: Any) -> tuple[int, str]:
    """Send a JSON POST request and return (status, response_text)."""

    url = build_url(base_url, path)
    body = json.dumps(payload).encode("utf-8")
    request_obj = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request_obj, timeout=10) as response:  # noqa: S310
            status = getattr(response, "status", response.getcode())
            text = response.read().decode("utf-8")
            return status, text
    except HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        logging.debug("Request to %s failed with %s: %s", url, exc.code, text)
        return exc.code, text
    except URLError as exc:  # pragma: no cover - network issues
        raise RuntimeError(f"Failed to reach {url}: {exc}") from exc


def login(base_url: str, email: str, password: str) -> bool:
    payload = {"email": email, "password": password}
    status, text = post_json(base_url, LOGIN_PATH, payload)
    if 200 <= status < 300:
        logging.info("SigNoz login succeeded for %s", email)
        return True

    logging.info(
        "SigNoz login failed for %s with status %s and response %s",
        email,
        status,
        text,
    )
    return False


def create_user(base_url: str, email: str, password: str, org_name: str) -> bool:
    payload = {
        "orgDisplayName": org_name,
        "email": email,
        "password": password,
    }
    status, text = post_json(base_url, REGISTER_PATH, payload)

    if 200 <= status < 300:
        logging.info("SigNoz user %s created (status %s)", email, status)
        return True

    if status in {400, 409} and "exist" in text.lower():
        logging.info(
            "SigNoz user %s already exists according to register API.", email
        )
        return True

    raise RuntimeError(
        f"Failed to create SigNoz user {email}: status={status} body={text}"
    )


def main() -> int:
    logging.info(
        "Starting SigNoz bootstrap: base_url=%s email=%s org=%s",
        BASE_URL,
        EMAIL,
        ORG_DISPLAY_NAME,
    )

    wait_for_health(BASE_URL)

    if login(BASE_URL, EMAIL, PASSWORD):
        logging.info("SigNoz bootstrap skipped; credentials already active.")
        return 0

    create_user(BASE_URL, EMAIL, PASSWORD, ORG_DISPLAY_NAME)

    if login(BASE_URL, EMAIL, PASSWORD):
        logging.info("Default SigNoz admin user is ready.")
        return 0

    raise RuntimeError(
        "SigNoz bootstrap could not verify credentials after creation."
    )


if __name__ == "__main__":
    sys.exit(main())
