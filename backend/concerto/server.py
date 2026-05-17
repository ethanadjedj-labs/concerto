import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from concerto import db
from concerto.stripe_webhook import router as stripe_router
from concerto.provision_router import router as provision_router
from concerto.status_router import router as status_router
from concerto.terminal_router import router as terminal_router
from concerto.oauth_status_router import router as oauth_status_router
from concerto.first_call_detector import router as first_call_router
from concerto.customer_portal import router as customer_portal_router
from concerto.preflight_router import router as preflight_router
from concerto.trial_router import router as trial_router

_MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "migrations")
_MIGRATIONS = [
    "001_init.sql",
    "002_ttyd_credentials.sql",
    "003_hosted_plan.sql",
    "004_operator_kit.sql",
    "005_stripe_customer_id.sql",
    "006_drip_tracking.sql",
    "007_recovery.sql",
    "007_pricing_tiers_v2.sql",
    "008_rename_maestro_to_concerto.sql",
    "009_trial_mode.sql",
    "010_email_dead_letter.sql",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    for fname in _MIGRATIONS:
        with open(os.path.join(_MIGRATIONS_DIR, fname)) as f:
            await db.run_migration(f.read())
    yield


app = FastAPI(title="Concerto Backend", version="1.0.0", lifespan=lifespan)

_CORS_ORIGINS = ["https://concerto.run", "https://www.concerto.run"]
_extra = os.getenv("CONCERTO_EXTRA_ORIGINS", "")
if _extra:
    _CORS_ORIGINS.extend(o.strip() for o in _extra.split(",") if o.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "concerto-backend"}


app.include_router(stripe_router)
app.include_router(provision_router)
app.include_router(status_router)
app.include_router(terminal_router)
app.include_router(oauth_status_router)
app.include_router(first_call_router)
app.include_router(customer_portal_router)
app.include_router(preflight_router)
app.include_router(trial_router)
