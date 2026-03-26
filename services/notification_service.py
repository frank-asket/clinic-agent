# services/notification_service.py - Staff / doctor alerts for new bookings

import uuid
from datetime import datetime

from data.db import get_doctor_by_id, insert_doctor_booking_alert


def queue_doctor_alert_for_new_booking(
    booking_id: str,
    doctor_id: str,
    patient_name: str,
    patient_phone: str,
    appointment_date: str,
    appointment_time_display: str,
) -> None:
    """Record an alert for admin staff to inform the doctor (email/call/SMS outside this app)."""
    doctor = get_doctor_by_id(doctor_id)
    if not doctor:
        return
    notification_id = f"ALT-{uuid.uuid4().hex[:8].upper()}"
    insert_doctor_booking_alert(
        notification_id=notification_id,
        booking_id=booking_id,
        doctor_id=doctor_id,
        doctor_name=doctor[1],
        patient_name=patient_name,
        patient_phone=patient_phone,
        appointment_date=appointment_date,
        appointment_time_display=appointment_time_display,
        created_at=datetime.now().isoformat(timespec="seconds"),
    )


def suggested_message_for_doctor(
    doctor_name: str,
    patient_name: str,
    patient_phone: str,
    appointment_date: str,
    appointment_time_display: str,
    booking_id: str,
) -> str:
    """Plain-text blurb staff can paste into email or SMS."""
    return (
        f"New appointment — {booking_id}\n"
        f"Doctor: {doctor_name}\n"
        f"Patient: {patient_name}\n"
        f"Phone: {patient_phone}\n"
        f"Date: {appointment_date}\n"
        f"Time: {appointment_time_display}\n"
    )
