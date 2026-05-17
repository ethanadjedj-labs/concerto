import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from maestro import db
from maestro.stripe_webhook import router as stripe_router
from maestro.provision_router import router as provision_router
from maestro.status_router import router as status_router
from maestro.terminal_router import router as terminal_router

_MIGRATION_PATH = os.path.join(os.path.dirname(__file__), "..", "migrations", "001_init.sql")


@asynccontextmanager
async def lifespan(app: FastAPI):
    with open(_MIGRATION_PATH) as f:
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
