"""Over HTTP on Postgres: data and sessions survive a service restart, and a terminated idle
database connection does not take the service down (carried over from the Node service's API test)."""
import httpx
import psycopg
import pytest
from fake_issuer import APP, CLIENT_ID, ISSUER, FakeIssuer
from openentitlement_service.interfaces.http import OidcSettings, SignInSettings, create_app
from openentitlement_service.repositories.postgres import PostgresStore, create_engine
from sqlalchemy.engine import make_url
from test_http_tiers import _privilege, _sign_in

pytestmark = pytest.mark.anyio


def _app(engine, issuer):
    return create_app(
        PostgresStore(engine),
        sign_in=SignInSettings(oidc=OidcSettings(app_url=APP, issuer=ISSUER, client_id=CLIENT_ID)),
        oidc_transport=issuer.transport,
    )


async def test_restart_keeps_data_and_sessions_and_survives_terminated_connections(clean_postgres_url):
    issuer = FakeIssuer()
    # The service's own engine options (main.build_app).
    engine = create_engine(clean_postgres_url, pool_pre_ping=True)
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=_app(engine, issuer)), base_url=APP) as client:
            product = await _sign_in(client, issuer, "alice")
            entry = {"key": "seats", "type": "integer", "title": "Seats", "default": 5}
            assert (await _privilege(client, product, entry)).status_code == 200
            cookies, headers = client.cookies, dict(client.headers)
    finally:
        await engine.dispose()

    engine = create_engine(clean_postgres_url, pool_pre_ping=True)
    try:
        transport = httpx.ASGITransport(app=_app(engine, issuer))
        async with httpx.AsyncClient(transport=transport, base_url=APP, cookies=cookies, headers=headers) as client:
            # A new process on the same database: the session and the Catalog are still there.
            catalog = (await client.get(f"{product}/catalog")).json()
            assert catalog["catalog"]["privileges"][0]["default"] == 5

            # Postgres terminates every idle connection (a restart, a failover, an idle timeout).
            name = make_url(clean_postgres_url).database
            admin = make_url(clean_postgres_url).set(drivername="postgresql").render_as_string(hide_password=False)
            with psycopg.connect(admin, autocommit=True) as conn:
                terminated = conn.execute(
                    "select count(pg_terminate_backend(pid)) from pg_stat_activity"
                    " where datname = %s and pid <> pg_backend_pid()",
                    (name,),
                ).fetchone()
            assert terminated is not None and terminated[0] >= 1
            # The next requests get new connections.
            assert (await client.get(f"{product}/catalog")).status_code == 200
            assert (await client.get("/healthz")).status_code == 200
    finally:
        await engine.dispose()
