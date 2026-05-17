"""
WhatsApp service for MediFlow OS using Twilio
Handles sending messages and managing WhatsApp interactions
"""

from typing import Optional, Dict, Any
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from config import config
import logging

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service for managing WhatsApp communications via Twilio"""
    
    def __init__(self):
        """Initialize Twilio client"""
        if not config.is_twilio_configured():
            logger.warning("Twilio WhatsApp is not configured. WhatsApp features will be disabled.")
            self.client = None
            self.whatsapp_number = None
        else:
            self.client = Client(config.twilio_account_sid, config.twilio_auth_token)
            self.whatsapp_number = config.twilio_whatsapp_number
    
    def is_available(self) -> bool:
        """Check if WhatsApp service is available"""
        return self.client is not None
    
    def send_message(self, to_number: str, message: str) -> Optional[Dict[str, Any]]:
        """
        Send a WhatsApp message to a patient
        
        Args:
            to_number: Patient's phone number (with country code, e.g., +919876543210)
            message: Message content to send
            
        Returns:
            Dict with message details if successful, None otherwise
        """
        if not self.is_available():
            logger.error("WhatsApp service is not available")
            return None
        
        try:
            # Ensure phone number has whatsapp: prefix
            if not to_number.startswith("whatsapp:"):
                to_number = f"whatsapp:{to_number}"
            
            # Ensure from number has whatsapp: prefix
            from_number = self.whatsapp_number
            if not from_number.startswith("whatsapp:"):
                from_number = f"whatsapp:{from_number}"
            
            message_obj = self.client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )
            
            logger.info(f"WhatsApp message sent successfully. SID: {message_obj.sid}")
            return {
                "sid": message_obj.sid,
                "status": message_obj.status,
                "to": to_number,
                "from": from_number
            }
        
        except TwilioRestException as e:
            logger.error(f"Twilio error sending WhatsApp message: {e}")
            return None
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return None
    
    def send_appointment_confirmation(
        self,
        patient_phone: str,
        patient_name: str,
        doctor_name: str,
        appointment_time: str,
        appointment_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Send appointment confirmation message
        
        Args:
            patient_phone: Patient's phone number
            patient_name: Patient's name
            doctor_name: Doctor's name
            appointment_time: Formatted appointment time
            appointment_id: Appointment ID
            
        Returns:
            Dict with message details if successful, None otherwise
        """
        message = f"""🏥 *MediFlow OS - Appointment Confirmed*

Hello {patient_name}!

Your appointment has been successfully booked:

👨‍⚕️ Doctor: Dr. {doctor_name}
📅 Date & Time: {appointment_time}
🔢 Appointment ID: #{appointment_id}

Please arrive 10 minutes early for registration.

Reply with "CANCEL {appointment_id}" to cancel this appointment.

Thank you for choosing MediFlow OS! 🙏"""
        
        return self.send_message(patient_phone, message)
    
    def send_prescription(
        self,
        patient_phone: str,
        patient_name: str,
        doctor_name: str,
        medications: list,
        consultation_notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send prescription details after consultation
        
        Args:
            patient_phone: Patient's phone number
            patient_name: Patient's name
            doctor_name: Doctor's name
            medications: List of medication dicts with name, dosage, frequency, duration
            consultation_notes: Optional consultation notes
            
        Returns:
            Dict with message details if successful, None otherwise
        """
        message = f"""💊 *MediFlow OS - Your Prescription*

Hello {patient_name}!

Dr. {doctor_name} has prescribed the following medications:

"""
        
        # Add medications
        for idx, med in enumerate(medications, 1):
            message += f"{idx}. *{med.get('medication', 'N/A')}*\n"
            message += f"   💊 Dosage: {med.get('dosage', 'N/A')}\n"
            message += f"   ⏰ Frequency: {med.get('frequency', 'N/A')}\n"
            message += f"   📆 Duration: {med.get('duration', 'N/A')}\n"
            if med.get('instructions'):
                message += f"   📝 Instructions: {med.get('instructions')}\n"
            message += "\n"
        
        # Add consultation notes if available
        if consultation_notes:
            message += f"📋 *Additional Notes:*\n{consultation_notes}\n\n"
        
        message += """⚠️ *Important Reminders:*
- Take medications as prescribed
- Complete the full course
- Contact us if you experience any side effects

Get well soon! 🙏"""
        
        return self.send_message(patient_phone, message)
    
    def send_ai_scribe_summary(
        self,
        patient_phone: str,
        patient_name: str,
        soap_notes: str
    ) -> Optional[Dict[str, Any]]:
        """
        Send AI-generated consultation summary (SOAP notes)
        
        Args:
            patient_phone: Patient's phone number
            patient_name: Patient's name
            soap_notes: SOAP format consultation notes
            
        Returns:
            Dict with message details if successful, None otherwise
        """
        message = f"""📝 *MediFlow OS - Consultation Summary*

Hello {patient_name}!

Here is your consultation summary:

{soap_notes}

This summary has been generated by our AI Medical Scribe for your records.

Thank you for visiting MediFlow OS! 🙏"""
        
        return self.send_message(patient_phone, message)
    
    def send_appointment_reminder(
        self,
        patient_phone: str,
        patient_name: str,
        doctor_name: str,
        appointment_time: str,
        appointment_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Send appointment reminder message
        
        Args:
            patient_phone: Patient's phone number
            patient_name: Patient's name
            doctor_name: Doctor's name
            appointment_time: Formatted appointment time
            appointment_id: Appointment ID
            
        Returns:
            Dict with message details if successful, None otherwise
        """
        message = f"""⏰ *MediFlow OS - Appointment Reminder*

Hello {patient_name}!

This is a reminder for your upcoming appointment:

👨‍⚕️ Doctor: Dr. {doctor_name}
📅 Date & Time: {appointment_time}
🔢 Appointment ID: #{appointment_id}

Please arrive 10 minutes early for registration.

See you soon! 🙏"""
        
        return self.send_message(patient_phone, message)
    
    def send_welcome_message(self, patient_phone: str, patient_name: str) -> Optional[Dict[str, Any]]:
        """
        Send welcome message to new patient
        
        Args:
            patient_phone: Patient's phone number
            patient_name: Patient's name
            
        Returns:
            Dict with message details if successful, None otherwise
        """
        message = f"""🏥 *Welcome to MediFlow OS!*

Hello {patient_name}!

Thank you for registering with MediFlow OS. You can now:

📅 Book appointments via WhatsApp
💊 Receive prescriptions after consultation
📝 Get AI-generated consultation summaries

*How to book an appointment:*
Reply with: BOOK <Doctor Name> <Date> <Time>
Example: BOOK Dr. Smith 2026-05-20 10:00

*Need help?*
Reply with: HELP

We're here to serve you! 🙏"""
        
        return self.send_message(patient_phone, message)


# Create global instance
whatsapp_service = WhatsAppService()


# Made with Bob