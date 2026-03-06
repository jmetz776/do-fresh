import os

from dotenv import load_dotenv

# Load env before importing routers that read os.getenv at import time.
load_dotenv('.env')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.api.routes_mvp import router as mvp_router
from app.api.routes_relay import router as relay_router
from app.api.routes_integrations import router as integrations_router
from app.api.routes_auth import router as auth_router
from app.api.routes_intelligence import router as intelligence_router

try:
    from app.api.routes_consent import router as consent_router
except Exception:
    consent_router = None  # type: ignore

try:
    from app.api.routes_voice import router as voice_router
except Exception:
    voice_router = None  # type: ignore
from app.db import init_db

app = FastAPI(title="DemandOrchestrator API", version="0.1.0")

cors_origins = [o.strip() for o in os.getenv('CORS_ORIGINS', 'http://127.0.0.1:3000,http://localhost:3000').split(',') if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PATCH', 'OPTIONS'],
    allow_headers=['Authorization', 'Content-Type'],
)


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(router)
app.include_router(mvp_router)
app.include_router(relay_router)
app.include_router(integrations_router)
if consent_router is not None:
    app.include_router(consent_router)
if voice_router is not None:
    app.include_router(voice_router)
app.include_router(auth_router)
app.include_router(intelligence_router)
