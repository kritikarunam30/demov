import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import admin, doctor, patient, websocket_scribe, auth, whatsapp

app = FastAPI()

allowed_origins = [
    "https://demov-final.vercel.app",
    "http://localhost:3000",
]

env_origins = os.getenv("ALLOWED_ORIGINS")
if env_origins:
    allowed_origins.extend([o.strip() for o in env_origins.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(doctor.router, prefix="/api/doctor", tags=["doctor"])
app.include_router(patient.router, prefix="/api/patient", tags=["patient"])
app.include_router(websocket_scribe.router, prefix="/api", tags=["websocket"])
app.include_router(whatsapp.router, prefix="/api/whatsapp", tags=["whatsapp"])


@app.get("/")
def read_root():
    return {"status": "MediFlow-OS API running"}


@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        from config import config
        return {
            "status": "healthy",
            "api_configured": config.is_configured()
        }
    except:
        return {
            "status": "healthy",
            "api_configured": False
        }
