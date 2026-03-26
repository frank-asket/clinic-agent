# services/booking_service.py - Booking operations

import uuid
from datetime import datetime, timedelta

from data.db import (
    create_booking,
    create_customer,
    get_bookings_by_doctor_and_date,
    get_customer_by_phone,
)
from services.doctor_service import generate_time_slots, parse_time_slot
from services.notification_service import queue_doctor_alert_for_new_booking


def get_or_create_customer(name: str, phone: str) -> str:
    """Get existing customer or create new one."""
    customer = get_customer_by_phone(phone)
    if customer:
        return customer[0]

    customer_id = f"CUST-{uuid.uuid4().hex[:6].upper()}"
    create_customer(customer_id, name, phone)
    return customer_id


def get_available_slots(doctor_id: str, office_timing: str, appointment_date: str | None = None):
    """Get available time slots for a doctor on a given date.

    Args:
        doctor_id: Doctor ID
        office_timing: Office timing string like "11:00-16:00"
        appointment_date: Date in YYYY-MM-DD; defaults to today.

    Returns:
        List of available display time slots
    """
    if not appointment_date:
        appointment_date = datetime.now().strftime("%Y-%m-%d")

    all_slots = generate_time_slots(office_timing)
    booked_times = set(get_bookings_by_doctor_and_date(doctor_id, appointment_date))

    available = []
    for slot in all_slots:
        slot_24h = parse_time_slot(slot)
        if slot_24h not in booked_times:
            available.append(slot)

    return available


def confirm_booking(
    doctor_id: str,
    customer_name: str,
    customer_phone: str,
    time_slot: str,
    appointment_date: str | None = None,
) -> str:
    """Confirm a booking.

    Args:
        doctor_id: Doctor ID
        customer_name: Customer name
        customer_phone: Customer phone
        time_slot: Time slot like "1:00 PM"
        appointment_date: Optional date in YYYY-MM-DD format. Defaults to today.

    Returns:
        Booking ID
    """
    customer_id = get_or_create_customer(customer_name, customer_phone)
    booking_id = f"BKG-{uuid.uuid4().hex[:6].upper()}"

    if not appointment_date:
        appointment_date = datetime.now().strftime("%Y-%m-%d")
    appointment_time = parse_time_slot(time_slot)

    create_booking(booking_id, doctor_id, customer_id, appointment_date, appointment_time)
    queue_doctor_alert_for_new_booking(
        booking_id=booking_id,
        doctor_id=doctor_id,
        patient_name=customer_name,
        patient_phone=customer_phone,
        appointment_date=appointment_date,
        appointment_time_display=time_slot,
    )
    return booking_id


def next_open_dates(days: int = 5) -> list[tuple[str, str]]:
    """Return (iso_date, label) for upcoming days, e.g. ('2025-03-27', 'Tomorrow')."""
    today = datetime.now().date()
    labels_first = ["Today", "Tomorrow"]
    out: list[tuple[str, str]] = []
    for i in range(days):
        d = today + timedelta(days=i)
        iso = d.strftime("%Y-%m-%d")
        label = labels_first[i] if i < len(labels_first) else d.strftime("%A, %b %d")
        out.append((iso, label))
    return out
