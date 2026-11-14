"""Exercise rendered deployment settings without reading developer .env files."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient

from openentitlement_service.main import Settings, build_app

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("deployment", ["memory", "postgres"])
@pytest.mark.parametrize("mode", ["default", "tls", "unsafe_app", "unsafe_issuer", "http_disabled"])
def test_compose_sign_in_settings(deployment: str, mode: str) -> None:
    if shutil.which("docker") is None:
        pytest.skip("Docker Compose is needed to render the actual deployment environment")
    # Deliberately exclude inherited OE_* variables and disable Compose's .env discovery.
    env = {key: os.environ[key] for key in ("PATH", "HOME") if key in os.environ}
    env.update(POSTGRES_PASSWORD="compose-test-only", OE_PLATFORM_ADMIN_SUBJECT="test-admin",
               OE_OIDC_ISSUER="https://issuer.example.test")
    if mode == "tls":
        env.update(OE_APP_URL="https://console.example.test", OE_OIDC_LOCAL_HTTP="false")
    elif mode == "unsafe_app":
        env["OE_APP_URL"] = "http://console.example.test"
    elif mode == "unsafe_issuer":
        env["OE_OIDC_ISSUER"] = "http://issuer.example.test"
    elif mode == "http_disabled":
        env["OE_OIDC_LOCAL_HTTP"] = "false"
    result = subprocess.run(
        ["docker", "compose", "--env-file", os.devnull, "-f", str(ROOT / "deploy" / f"compose.{deployment}.yaml"),
         "config", "--format", "json"],
        env=env, capture_output=True, text=True, check=True,
    )
    rendered = json.loads(result.stdout)["services"]["openentitlement"]["environment"]
    if mode in {"unsafe_app", "unsafe_issuer", "http_disabled"}:
        with pytest.raises(SystemExit, match="requires HTTPS"):
            Settings.from_env(rendered)
        return
    settings = Settings.from_env(rendered)
    assert settings.sign_in is not None
    assert settings.sign_in.oidc.app_url == (
        "https://console.example.test" if mode == "tls" else "http://localhost:8787"
    )
    assert settings.sign_in.oidc.secure_cookies == (mode == "tls")
    # Compose's Postgres host need not be running to construct the real app and routes.
    app = build_app(settings, migrate_at_startup=False)
    assert TestClient(app).get("/auth/logout").status_code == 405
