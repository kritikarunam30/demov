from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import admin, doctor, patient, websocket_scribe, auth, whatsapp

app = FastAPI(title="MediFlow-OS API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
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
