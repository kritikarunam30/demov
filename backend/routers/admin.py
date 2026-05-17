from datetime import date, datetime
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database.connection import get_db
from database.models import AdminUser
from services.admin_service import AdminService
from services.predictive_emergency_service import PredictiveEmergencyService

router = APIRouter()


def _require_admin_access(
    db: Session,
    x_user_role: str,
    x_user_id: str,
    require_pharmacy: bool = False,
) -> AdminUser:
    if not x_user_role or not x_user_id:
        raise HTTPException(status_code=401, detail="Missing authentication headers")
    if x_user_role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        admin_id = int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user id header")

    admin = db.query(AdminUser).filter(AdminUser.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin account not found")

    if require_pharmacy and admin.department != "Pharmacy":
        raise HTTPException(status_code=403, detail="Pharmacy access required")

    return admin


class SurgeForecastCustomRequest(BaseModel):
    days: int = 7


class CreatePatientRequest(BaseModel):
    name: str
    date_of_birth: date
    age: int
    blood_group: str | None = None
    allergies: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None


class CreateDoctorRequest(BaseModel):
    name: str
    department_id: int
    specialization: str | None = None
    is_available: bool = True


@router.get("/stats")
def get_admin_stats(db: Session = Depends(get_db)):
    return AdminService.get_admin_stats(db)


@router.get("/queue")
def get_queue(db: Session = Depends(get_db)):
    return AdminService.get_queue(db)


@router.get("/surge-forecast")
def get_surge_forecast():
    return AdminService.get_surge_forecast()


@router.post("/surge-forecast/custom")
def get_surge_forecast_custom(payload: SurgeForecastCustomRequest):
    days = payload.days if payload.days >= 1 else 7
    return AdminService.get_surge_forecast(days)


@router.get("/live-map")
def get_live_map(db: Session = Depends(get_db)):
    return AdminService.get_live_map(db)


@router.get("/departments")
def get_departments(
    db: Session = Depends(get_db),
    x_user_role: str = Header(None),
    x_user_id: str = Header(None),
):
    _require_admin_access(db, x_user_role, x_user_id)
    return AdminService.get_departments(db)


@router.post("/patients")
def create_patient(
    payload: CreatePatientRequest,
    db: Session = Depends(get_db),
    x_user_role: str = Header(None),
    x_user_id: str = Header(None),
):
    _require_admin_access(db, x_user_role, x_user_id)
    return AdminService.create_patient(db, payload.model_dump())


@router.post("/doctors")
def create_doctor(
    payload: CreateDoctorRequest,
    db: Session = Depends(get_db),
    x_user_role: str = Header(None),
    x_user_id: str = Header(None),
):
    _require_admin_access(db, x_user_role, x_user_id)
    return AdminService.create_doctor(db, payload.model_dump())


@router.get("/medicine-inventory")
def get_medicine_inventory(
    db: Session = Depends(get_db),
    x_user_role: str = Header(None),
    x_user_id: str = Header(None),
):
    _require_admin_access(db, x_user_role, x_user_id, require_pharmacy=True)
    return AdminService.get_medicine_inventory()


class SendChatMessageRequest(BaseModel):
    department: str
    sender_username: str
    message_text: str


@router.get("/chat/all")
def get_all_chat(db: Session = Depends(get_db)):
    """Get all chat messages across all departments"""
    return AdminService.get_all_chat_messages(db)


@router.get("/chat/{department}")
def get_department_chat(department: str, db: Session = Depends(get_db)):
    """Get chat messages for a specific department"""
    return AdminService.get_chat_messages(db, department)


@router.post("/chat")
def send_chat_message(request: SendChatMessageRequest, db: Session = Depends(get_db)):
    """Send a new chat message to a department"""
    return AdminService.send_chat_message(
        db, 
        request.department, 
        request.sender_username, 
        request.message_text
    )



# --- Emergency endpoints ---

@router.get("/emergency/alerts")
def get_emergency_alerts():
    """Return mock active emergency alerts for the dashboard"""
    now = datetime.utcnow().isoformat()
    return {
        "alerts": [
            {
                "id": 1,
                "title": "ER Capacity Critical",
                "description": "Emergency room has exceeded 95% capacity.",
                "level": "critical",
                "type": "capacity",
                "department": "Emergency",
                "status": "active",
                "timestamp": now,
                "affected_areas": ["Triage", "Waiting Room"],
                "recommended_actions": [
                    "Divert non-critical patients to urgent care",
                    "Activate surge protocol",
                    "Alert on-call staff",
                ],
            },
            {
                "id": 2,
                "title": "Staffing Shortage - ICU",
                "description": "ICU nurse-to-patient ratio below minimum threshold.",
                "level": "high",
                "type": "staffing",
                "department": "ICU",
                "status": "active",
                "timestamp": now,
                "affected_areas": ["ICU Ward A"],
                "recommended_actions": [
                    "Contact agency staff",
                    "Reassign from lower-acuity wards",
                ],
            },
        ]
    }


@router.get("/emergency/protocols")
def get_emergency_protocols():
    """Return emergency protocol definitions"""
    return {
        "protocols": {
            "surge": {
                "name": "Surge Protocol",
                "estimated_activation_time": "15 minutes",
                "steps": [
                    "Notify department heads",
                    "Open overflow waiting area",
                    "Call in off-duty staff",
                    "Suspend elective procedures",
                    "Implement discharge acceleration",
                ],
            },
            "mass_casualty": {
                "name": "Mass Casualty Incident (MCI)",
                "estimated_activation_time": "10 minutes",
                "steps": [
                    "Activate hospital command centre",
                    "Deploy triage teams to ER entrance",
                    "Clear trauma bays",
                    "Contact blood bank for emergency supply",
                    "Alert OR for emergency surgeries",
                    "Coordinate with local EMS",
                ],
            },
            "evacuation": {
                "name": "Evacuation Protocol",
                "estimated_activation_time": "20 minutes",
                "steps": [
                    "Sound evacuation alarm",
                    "Assign floor wardens",
                    "Move ambulatory patients first",
                    "Use evacuation chairs for mobility-impaired",
                    "Account for all patients at muster point",
                ],
            },
        }
    }


@router.get("/emergency/contacts")
def get_emergency_contacts():
    """Return emergency contact list"""
    return {
        "contacts": [
            {
                "name": "Dr. Priya Sharma",
                "role": "Chief Medical Officer",
                "phone": "+91-98765-00001",
                "email": "cmo@mediflow.in",
                "availability": "24/7",
            },
            {
                "name": "Rajan Mehta",
                "role": "Hospital Administrator",
                "phone": "+91-98765-00002",
                "email": "admin@mediflow.in",
                "availability": "24/7",
            },
            {
                "name": "Fire & Safety Dept.",
                "role": "Safety Officer",
                "phone": "101",
                "email": "safety@mediflow.in",
                "availability": "24/7",
            },
            {
                "name": "State Ambulance Control",
                "role": "EMS Coordinator",
                "phone": "108",
                "email": "ems@state.gov.in",
                "availability": "24/7",
            },
        ]
    }


@router.get("/emergency/incidents")
def get_emergency_incidents():
    """Return recent emergency incidents log"""
    return {
        "incidents": [
            {
                "id": 1,
                "date": "2026-05-15",
                "type": "surge",
                "description": "Unexpected patient surge following road accident on NH-8.",
                "severity": "high",
                "patients_affected": 24,
                "status": "resolved",
            },
            {
                "id": 2,
                "date": "2026-05-10",
                "type": "equipment_failure",
                "description": "Ventilator #3 malfunction in ICU.",
                "severity": "medium",
                "patients_affected": 1,
                "status": "resolved",
            },
            {
                "id": 3,
                "date": "2026-05-03",
                "type": "staffing",
                "description": "Night shift understaffed due to flu outbreak among nurses.",
                "severity": "medium",
                "patients_affected": 0,
                "status": "resolved",
            },
        ]
    }

@router.get("/emergency/predictions")
def get_emergency_predictions(
    db: Session = Depends(get_db),
    x_user_role: str = Header(None),
    x_user_id: str = Header(None),
):
    _require_admin_access(db, x_user_role, x_user_id)
    predictions = PredictiveEmergencyService.generate_mock_vitals()
    return {"predictions": predictions}

@router.post("/emergency/predictions/{patient_id}/acknowledge")
def acknowledge_emergency_prediction(
    patient_id: int,
    db: Session = Depends(get_db),
    x_user_role: str = Header(None),
    x_user_id: str = Header(None),
):
    _require_admin_access(db, x_user_role, x_user_id)
    return PredictiveEmergencyService.acknowledge_alert(patient_id)
