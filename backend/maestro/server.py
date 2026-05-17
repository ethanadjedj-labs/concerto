import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from maestro import db
from maestro.stripe_webhook import router as stripe_router
from maestro.provision_router import router as provision_router
from maestro.status_router import router as status_router
from maestro.terminal_router import router as terminal_router
from maestro.oauth_status_router import router as oauth_status_router
from maestro.first_call_detector import router as first_call_router
from maestro.customer_portal import router as customer_portal_router

_MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "migrations")
_MIGRATIONS = [
    "001_init.sql",
    "002_ttyd_credentials.sql",
    "003_hosted_plan.sql",
    "004_operator_kit.sql",
    "005_stripe_customer_id.sql",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    for fname in _MIGRATIONS:
        with open(os.path.join(_MIGRATIONS_DIR, fname)) as f:
            await db.run_migration(f.read())
    yield


app = FastAPI(title="Maestro Backend", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://maestro.run", "https://www.maestro.run"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "maestro-backend"}


app.include_router(stripe_router)
app.include_router(provision_router)
app.include_router(status_router)
app.include_router(terminal_router)
app.include_router(oauth_status_router)
app.include_router(first_call_router)
app.include_router(customer_portal_router)
