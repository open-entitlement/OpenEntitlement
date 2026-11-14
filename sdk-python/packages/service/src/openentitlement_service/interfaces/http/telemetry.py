"""Opt-in PostHog for the console, and the browser policy of the console's pages.

Off unless the operator sets ``OE_POSTHOG_KEY``: a self-hosted installation sends nothing anywhere
by default. The key is a PostHog project API key, public by design (it can only ingest events).
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlsplit

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

DEFAULT_HOST = "https://us.i.posthog.com"


@dataclass(frozen=True)
class Telemetry:
    #: PostHog project API key (``phc_…``).
    key: str
    #: Ingestion origin, for example ``https://eu.i.posthog.com``.
    host: str = DEFAULT_HOST

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> Telemetry | None:
        """``None`` without ``OE_POSTHOG_KEY``; ``ValueError`` for an invalid key or host."""
        key = env.get("OE_POSTHOG_KEY", "").strip()
        if not key:
            return None
        if not re.fullmatch(r"phc_[A-Za-z0-9]+", key):
            raise ValueError("OE_POSTHOG_KEY must be a PostHog project API key (phc_…)")
        host = (env.get("OE_POSTHOG_HOST", "").strip() or DEFAULT_HOST).rstrip("/")
        url = urlsplit(host)
        if url.scheme != "https" or not url.hostname or url.path or url.query or url.fragment or url.username:
            raise ValueError("OE_POSTHOG_HOST must be an https origin, for example https://eu.i.posthog.com")
        return cls(key=key, host=f"https://{url.netloc}")


def console_headers(telemetry: Telemetry | None) -> dict[str, str]:
    """Headers of every console file: a strict Content-Security-Policy that allows PostHog only when configured."""
    # Session replay compresses recordings in a blob: worker; events go to the ingestion host.
    connect, worker = (f" {telemetry.host}", " blob:") if telemetry else ("", "")
    policy = (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
        f"connect-src 'self'{connect}; worker-src 'self'{worker}; frame-ancestors 'none'; "
        "base-uri 'self'; form-action 'self'"
    )
    return {
        "content-security-policy": policy,
        "x-content-type-options": "nosniff",
        "referrer-policy": "same-origin",
    }


router = APIRouter()


@router.get("/telemetry.json", include_in_schema=False)
async def telemetry_config(request: Request) -> JSONResponse:
    """What the console bundle should load. Never anything secret."""
    telemetry: Telemetry | None = request.app.state.telemetry
    body = {"posthog": {"key": telemetry.key, "host": telemetry.host}} if telemetry else {}
    return JSONResponse(body, headers={"cache-control": "no-store"})
