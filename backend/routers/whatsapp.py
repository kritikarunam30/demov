"""
WhatsApp router for MediFlow OS
Handles incoming WhatsApp messages and webhook endpoints
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import re
import logging

from database.connection import get_db
from services.whatsapp_service import whatsapp_service
from crud.patient import patient as patient_crud
from crud.doctor import doctor as doctor_crud
from crud.appointment import appointment as appointment_crud

logger = logging.getLogger(__name__)

router = APIRouter()


def parse_phone_number(phone: str) -> str:
    """
    Parse and normalize phone number from WhatsApp format
    
    Args:
        phone: Phone number in format like 'whatsapp:+919876543210'
        
    Returns:
        Normalized phone number with country code
    """
    # Remove 'whatsapp:' prefix if present
    phone = phone.replace("whatsapp:", "").strip()
    
    # Ensure it starts with +
    if not phone.startswith("+"):
        phone = "+" + phone
    
    return phone


def parse_appointment_request(message: str) -> Optional[dict]:
    """
    Parse appointment booking request from message
    
    Expected format: BOOK <Doctor Name> <Date> <Time>
    Example: BOOK Dr. Smith 2026-05-20 10:00
    
    Returns:
        Dict with doctor_name, date, time if valid, None otherwise
    """
    # Pattern: BOOK <doctor name> <YYYY-MM-DD> <HH:MM>
    pattern = r"BOOK\s+(.+?)\s+(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})"
    match = re.search(pattern, message, re.IGNORECASE)
    
    if match:
        return {
            "doctor_name": match.group(1).strip(),
            "date": match.group(2),
            "time": match.group(3)
        }
    return None


def parse_cancel_request(message: str) -> Optional[int]:
    """
    Parse appointment cancellation request
    
    Expected format: CANCEL <appointment_id>
    Example: CANCEL 123
    
    Returns:
        Appointment ID if valid, None otherwise
    """
    pattern = r"CANCEL\s+(\d+)"
    match = re.search(pattern, message, re.IGNORECASE)
    
    if match:
        return int(match.group(1))
    return None


@router.post("/webhook")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook endpoint for receiving incoming WhatsApp messages from Twilio
    
    Twilio sends POST requests with form data containing:
    - From: Sender's WhatsApp number
    - To: Your WhatsApp business number
    - Body: Message content
    """
    try:
        # Get form data from Twilio
        form_data = await request.form()
        
        from_number = form_data.get("From", "")
        message_body = form_data.get("Body", "").strip()
        
        logger.info(f"Received WhatsApp message from {from_number}: {message_body}")
        
        # Parse phone number
        patient_phone = parse_phone_number(from_number)
        
        # Find patient by phone number
        patient = patient_crud.get_by_phone(db, patient_phone)
        
        if not patient:
            # Patient not registered
            response_message = """🏥 *Welcome to MediFlow OS!*

You are not registered in our system. Please visit our hospital or website to register first.

Once registered, you can:
📅 Book appointments via WhatsApp
💊 Receive prescriptions
📝 Get consultation summaries

Thank you! 🙏"""
            whatsapp_service.send_message(from_number, response_message)
            return Response(content="", status_code=200)
        
        # Process different types of messages
        message_upper = message_body.upper()
        
        # Help command
        if message_upper == "HELP":
            help_message = f"""🏥 *MediFlow OS - Help*

Hello {patient.name}!

*Available Commands:*

📅 *Book Appointment:*
BOOK <Doctor Name> <Date> <Time>
Example: BOOK Dr. Smith 2026-05-20 10:00

❌ *Cancel Appointment:*
CANCEL <Appointment ID>
Example: CANCEL 123

📋 *List Doctors:*
DOCTORS

📆 *My Appointments:*
APPOINTMENTS

Need more help? Call us at the hospital.

Thank you! 🙏"""
            whatsapp_service.send_message(from_number, help_message)
        
        # List doctors
        elif message_upper == "DOCTORS":
            doctors = doctor_crud.get_available(db)
            if doctors:
                doctors_message = f"""👨‍⚕️ *Available Doctors*

"""
                for doc in doctors:
                    doctors_message += f"• Dr. {doc.name}"
                    if doc.specialization:
                        doctors_message += f" - {doc.specialization}"
                    doctors_message += "\n"
                
                doctors_message += """\nTo book an appointment:
BOOK <Doctor Name> <Date> <Time>
Example: BOOK Dr. Smith 2026-05-20 10:00"""
                
                whatsapp_service.send_message(from_number, doctors_message)
            else:
                whatsapp_service.send_message(from_number, "No doctors available at the moment. Please try again later.")
        
        # List appointments
        elif message_upper == "APPOINTMENTS":
            appointments = appointment_crud.get_by_patient(db, patient.id)
            if appointments:
                appt_message = f"""📅 *Your Appointments*

"""
                for appt in appointments[:5]:  # Show last 5 appointments
                    status_emoji = "✅" if appt.status == "Completed" else "📅" if appt.status == "Scheduled" else "⏳"
                    appt_message += f"{status_emoji} *ID #{appt.id}*\n"
                    appt_message += f"   Doctor: Dr. {appt.doctor.name if appt.doctor else 'N/A'}\n"
                    appt_message += f"   Time: {appt.scheduled_time.strftime('%Y-%m-%d %H:%M') if appt.scheduled_time else 'N/A'}\n"
                    appt_message += f"   Status: {appt.status}\n\n"
                
                appt_message += "To cancel: CANCEL <ID>"
                whatsapp_service.send_message(from_number, appt_message)
            else:
                whatsapp_service.send_message(from_number, "You have no appointments. Book one with: BOOK <Doctor> <Date> <Time>")
        
        # Book appointment
        elif message_upper.startswith("BOOK"):
            booking_data = parse_appointment_request(message_body)
            
            if not booking_data:
                whatsapp_service.send_message(
                    from_number,
                    "❌ Invalid format. Use: BOOK <Doctor Name> <Date> <Time>\nExample: BOOK Dr. Smith 2026-05-20 10:00"
                )
            else:
                # Find doctor
                doctor = doctor_crud.get_by_name(db, booking_data["doctor_name"])
                
                if not doctor:
                    whatsapp_service.send_message(
                        from_number,
                        f"❌ Doctor '{booking_data['doctor_name']}' not found. Reply DOCTORS to see available doctors."
                    )
                else:
                    try:
                        # Parse datetime
                        appointment_datetime = datetime.strptime(
                            f"{booking_data['date']} {booking_data['time']}",
                            "%Y-%m-%d %H:%M"
                        )
                        
                        # Check if date is in the future
                        if appointment_datetime < datetime.now():
                            whatsapp_service.send_message(
                                from_number,
                                "❌ Cannot book appointments in the past. Please choose a future date and time."
                            )
                        else:
                            # Create appointment
                            new_appointment = appointment_crud.create_appointment(
                                db=db,
                                patient_id=patient.id,
                                doctor_id=doctor.id,
                                scheduled_time=appointment_datetime,
                                complaint="Booked via WhatsApp"
                            )
                            
                            # Send confirmation
                            whatsapp_service.send_appointment_confirmation(
                                patient_phone=from_number,
                                patient_name=patient.name,
                                doctor_name=doctor.name,
                                appointment_time=appointment_datetime.strftime("%Y-%m-%d %H:%M"),
                                appointment_id=new_appointment.id
                            )
                            
                            logger.info(f"Appointment {new_appointment.id} created via WhatsApp for patient {patient.id}")
                    
                    except ValueError:
                        whatsapp_service.send_message(
                            from_number,
                            "❌ Invalid date/time format. Use: YYYY-MM-DD HH:MM\nExample: 2026-05-20 10:00"
                        )
        
        # Cancel appointment
        elif message_upper.startswith("CANCEL"):
            appointment_id = parse_cancel_request(message_body)
            
            if not appointment_id:
                whatsapp_service.send_message(
                    from_number,
                    "❌ Invalid format. Use: CANCEL <Appointment ID>\nExample: CANCEL 123"
                )
            else:
                # Get appointment
                appt = appointment_crud.get(db, appointment_id)
                
                if not appt:
                    whatsapp_service.send_message(from_number, f"❌ Appointment #{appointment_id} not found.")
                elif appt.patient_id != patient.id:
                    whatsapp_service.send_message(from_number, "❌ You can only cancel your own appointments.")
                elif appt.status == "Cancelled":
                    whatsapp_service.send_message(from_number, f"ℹ️ Appointment #{appointment_id} is already cancelled.")
                else:
                    # Cancel appointment
                    appointment_crud.cancel_appointment(db, appointment_id)
                    
                    cancel_message = f"""✅ *Appointment Cancelled*

Appointment #{appointment_id} has been cancelled successfully.

Doctor: Dr. {appt.doctor.name if appt.doctor else 'N/A'}
Time: {appt.scheduled_time.strftime('%Y-%m-%d %H:%M') if appt.scheduled_time else 'N/A'}

You can book a new appointment anytime! 🙏"""
                    
                    whatsapp_service.send_message(from_number, cancel_message)
                    logger.info(f"Appointment {appointment_id} cancelled via WhatsApp by patient {patient.id}")
        
        # Unknown command
        else:
            whatsapp_service.send_message(
                from_number,
                f"Hello {patient.name}! I didn't understand that command. Reply HELP to see available commands."
            )
        
        # Return empty 200 response to Twilio
        return Response(content="", status_code=200)
    
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}")
        return Response(content="", status_code=200)


@router.get("/webhook")
async def whatsapp_webhook_verify(request: Request):
    """
    Webhook verification endpoint for Twilio
    This is called by Twilio to verify the webhook URL
    """
    return Response(content="Webhook verified", status_code=200)


@router.post("/send-test")
async def send_test_message(phone: str, message: str):
    """
    Test endpoint to send a WhatsApp message
    
    Args:
        phone: Phone number with country code (e.g., +919876543210)
        message: Message to send
    """
    if not whatsapp_service.is_available():
        raise HTTPException(status_code=503, detail="WhatsApp service is not configured")
    
    result = whatsapp_service.send_message(phone, message)
    
    if result:
        return {"status": "success", "message": "Message sent", "details": result}
    else:
        raise HTTPException(status_code=500, detail="Failed to send message")


# Made with Bob