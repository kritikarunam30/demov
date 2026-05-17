from sqlalchemy.orm import Session
from crud import department as dept_crud, queue as queue_crud, department_chat as chat_crud
from crud import patient as patient_crud, doctor as doctor_crud
from database.models import Department, QueueEntry
from mock_data.medicine_inventory import MEDICINE_INVENTORY
from ml.surge_model import generate_forecast


class AdminService:
    @staticmethod
    def get_admin_stats(db: Session):
        """Get admin dashboard statistics"""
        total_patients = sum(dept.current_patients for dept in dept_crud.get_all(db))
        queue_entries = queue_crud.get_waiting(db)
        avg_wait = sum(q.wait_time_minutes for q in queue_entries) / len(queue_entries) if queue_entries else 0
        high_congestion_depts = dept_crud.get_high_congestion(db)
        
        return {
            "total_patients_today": total_patients,
            "avg_wait_time_min": int(avg_wait),
            "beds_available": 38,  # This could be calculated from department capacity
            "departments_on_alert": len(high_congestion_depts),
        }

    @staticmethod
    def get_queue(db: Session):
        """Get all queue entries"""
        queue_entries = queue_crud.get_waiting(db)
        return {"queue": [q.to_dict() for q in queue_entries]}

    @staticmethod
    def get_surge_forecast(days: int = 7):
        """Get surge prediction forecast using Prophet ML"""
        return generate_forecast(days)

    @staticmethod
    def get_live_map(db: Session):
        """Get live department map with congestion data"""
        departments = dept_crud.get_all(db)
        return {"departments": [dept.to_dict() for dept in departments]}

    @staticmethod
    def get_departments(db: Session):
        """Get departments for admin create forms"""
        departments = dept_crud.get_all(db)
        return {
            "departments": [
                {
                    "id": dept.id,
                    "name": dept.name,
                    "patients": dept.current_patients,
                    "congestion": dept.congestion_level,
                }
                for dept in departments
            ]
        }

    @staticmethod
    def create_patient(db: Session, payload: dict):
        """Create a patient account from the admin dashboard"""
        if payload.get("email") and patient_crud.get_by_email(db, payload["email"]):
            return {"error": "A patient with this email already exists"}

        if payload.get("phone") and patient_crud.get_by_phone(db, payload["phone"]):
            return {"error": "A patient with this phone already exists"}

        patient = patient_crud.create(
            db,
            name=payload["name"],
            date_of_birth=payload.get("date_of_birth"),
            age=payload.get("age"),
            blood_group=payload.get("blood_group"),
            allergies=payload.get("allergies"),
            phone=payload.get("phone"),
            email=payload.get("email"),
            address=payload.get("address"),
        )

        return {
            "success": True,
            "message": f"Patient account created for {patient.name}",
            "patient": patient.to_dict(),
        }

    @staticmethod
    def create_doctor(db: Session, payload: dict):
        """Create a doctor account from the admin dashboard"""
        department_id = payload.get("department_id")
        department = dept_crud.get(db, department_id)
        if not department:
            return {"error": "Department not found"}

        if payload.get("name") and doctor_crud.get_by_name(db, payload["name"]):
            return {"error": "A doctor with this name already exists"}

        doctor = doctor_crud.create(
            db,
            name=payload["name"],
            department_id=department_id,
            specialization=payload.get("specialization"),
            is_available=payload.get("is_available", True),
            appointments_today=payload.get("appointments_today", 0),
        )

        return {
            "success": True,
            "message": f"Doctor account created for {doctor.name}",
            "doctor": doctor.to_dict(),
        }

    @staticmethod
    def get_medicine_inventory():
        """Return pharmacy inventory mock data"""
        return {"inventory": MEDICINE_INVENTORY}

    @staticmethod
    def get_all_chat_messages(db: Session, limit: int = 100):
        """Get all chat messages across all departments"""
        messages = chat_crud.get_all(db, limit)
        # Reverse to show oldest first
        messages.reverse()
        return {"messages": [msg.to_dict() for msg in messages]}

    @staticmethod
    def get_chat_messages(db: Session, department: str, limit: int = 100):
        """Get chat messages for a specific department"""
        messages = chat_crud.get_by_department(db, department, limit)
        # Reverse to show oldest first
        messages.reverse()
        return {"messages": [msg.to_dict() for msg in messages]}

    @staticmethod
    def send_chat_message(db: Session, department: str, sender_username: str, message_text: str):
        """Send a new chat message"""
        message = chat_crud.create_message(db, department, sender_username, message_text)
        return {
            "success": True,
            "message": message.to_dict()
        }


# Made with Bob
