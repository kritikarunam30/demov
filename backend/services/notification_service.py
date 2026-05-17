"""
Notification service for MediFlow OS
Handles post-consultation notifications via WhatsApp
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import logging

from services.whatsapp_service import whatsapp_service
from database.models.consultation import Consultation
from database.models.prescription import Prescription
from database.models.patient import Patient

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing post-consultation notifications"""
    
    @staticmethod
    def send_consultation_summary(
        db: Session,
        consultation_id: int
    ) -> Dict[str, Any]:
        """
        Send consultation summary (AI scribe notes) to patient via WhatsApp
        
        Args:
            db: Database session
            consultation_id: Consultation ID
            
        Returns:
            Dict with status and message details
        """
        try:
            # Get consultation with related data
            consultation = db.query(Consultation).filter(
                Consultation.id == consultation_id
            ).first()
            
            if not consultation:
                logger.error(f"Consultation {consultation_id} not found")
                return {
                    "success": False,
                    "error": "Consultation not found"
                }
            
            # Get patient
            patient = consultation.patient
            if not patient or not patient.phone:
                logger.error(f"Patient phone not found for consultation {consultation_id}")
                return {
                    "success": False,
                    "error": "Patient phone number not available"
                }
            
            # Check if WhatsApp service is available
            if not whatsapp_service.is_available():
                logger.warning("WhatsApp service not configured")
                return {
                    "success": False,
                    "error": "WhatsApp service not configured"
                }
            
            # Send AI scribe summary if available
            if consultation.soap_notes:
                result = whatsapp_service.send_ai_scribe_summary(
                    patient_phone=patient.phone,
                    patient_name=patient.name,
                    soap_notes=consultation.soap_notes
                )
                
                if result:
                    logger.info(f"Consultation summary sent to patient {patient.id} for consultation {consultation_id}")
                    return {
                        "success": True,
                        "message": "Consultation summary sent successfully",
                        "details": result
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to send consultation summary"
                    }
            else:
                logger.warning(f"No SOAP notes available for consultation {consultation_id}")
                return {
                    "success": False,
                    "error": "No consultation notes available"
                }
        
        except Exception as e:
            logger.error(f"Error sending consultation summary: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def send_prescription_details(
        db: Session,
        prescription_id: int
    ) -> Dict[str, Any]:
        """
        Send prescription details to patient via WhatsApp
        
        Args:
            db: Database session
            prescription_id: Prescription ID
            
        Returns:
            Dict with status and message details
        """
        try:
            # Get prescription with related data
            prescription = db.query(Prescription).filter(
                Prescription.id == prescription_id
            ).first()
            
            if not prescription:
                logger.error(f"Prescription {prescription_id} not found")
                return {
                    "success": False,
                    "error": "Prescription not found"
                }
            
            # Get patient
            patient = prescription.patient
            if not patient or not patient.phone:
                logger.error(f"Patient phone not found for prescription {prescription_id}")
                return {
                    "success": False,
                    "error": "Patient phone number not available"
                }
            
            # Check if WhatsApp service is available
            if not whatsapp_service.is_available():
                logger.warning("WhatsApp service not configured")
                return {
                    "success": False,
                    "error": "WhatsApp service not configured"
                }
            
            # Get doctor name
            doctor_name = prescription.doctor.name if prescription.doctor else "Your Doctor"
            
            # Prepare medications list
            medications = []
            if prescription.items:
                for item in prescription.items:
                    medications.append({
                        "medication": item.medication_name,
                        "dosage": item.dosage,
                        "frequency": item.frequency,
                        "duration": item.duration,
                        "instructions": item.instructions
                    })
            
            if not medications:
                logger.warning(f"No medications found in prescription {prescription_id}")
                return {
                    "success": False,
                    "error": "No medications in prescription"
                }
            
            # Send prescription
            result = whatsapp_service.send_prescription(
                patient_phone=patient.phone,
                patient_name=patient.name,
                doctor_name=doctor_name,
                medications=medications,
                consultation_notes=prescription.notes
            )
            
            if result:
                logger.info(f"Prescription sent to patient {patient.id} for prescription {prescription_id}")
                return {
                    "success": True,
                    "message": "Prescription sent successfully",
                    "details": result
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to send prescription"
                }
        
        except Exception as e:
            logger.error(f"Error sending prescription: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def send_complete_consultation_package(
        db: Session,
        consultation_id: int
    ) -> Dict[str, Any]:
        """
        Send complete post-consultation package (AI scribe + prescription) to patient
        
        Args:
            db: Database session
            consultation_id: Consultation ID
            
        Returns:
            Dict with status and message details
        """
        results = {
            "consultation_summary": None,
            "prescription": None
        }
        
        # Send consultation summary
        summary_result = NotificationService.send_consultation_summary(db, consultation_id)
        results["consultation_summary"] = summary_result
        
        # Get consultation to find prescription
        consultation = db.query(Consultation).filter(
            Consultation.id == consultation_id
        ).first()
        
        if consultation and consultation.prescription:
            # Send prescription
            prescription_result = NotificationService.send_prescription_details(
                db,
                consultation.prescription.id
            )
            results["prescription"] = prescription_result
        else:
            results["prescription"] = {
                "success": False,
                "error": "No prescription available for this consultation"
            }
        
        # Determine overall success
        overall_success = (
            results["consultation_summary"].get("success", False) or
            results["prescription"].get("success", False)
        )
        
        return {
            "success": overall_success,
            "message": "Post-consultation notifications processed",
            "details": results
        }


# Create global instance
notification_service = NotificationService()


# Made with Bob