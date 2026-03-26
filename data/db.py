# data/db.py - Database initialization and operations

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "clinic.db")


def get_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize the database with tables and sample data."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS doctors (
            doctor_id TEXT PRIMARY KEY,
            doctor_name TEXT NOT NULL,
            speciality TEXT NOT NULL,
            office_timing TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id TEXT PRIMARY KEY,
            doctor_id TEXT NOT NULL,
            customer_id TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (doctor_id) REFERENCES doctors (doctor_id),
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS doctor_booking_alerts (
            notification_id TEXT PRIMARY KEY,
            booking_id TEXT NOT NULL,
            doctor_id TEXT NOT NULL,
            doctor_name TEXT NOT NULL,
            patient_name TEXT NOT NULL,
            patient_phone TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time_display TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            notified_at TEXT,
            FOREIGN KEY (booking_id) REFERENCES bookings (booking_id),
            FOREIGN KEY (doctor_id) REFERENCES doctors (doctor_id)
        )
        """
    )

    doctors = [
        ("D1", "Dr. Anil Sharma", "General Physician", "10:00-14:00"),
        ("D2", "Dr. Neha Verma", "Dermatologist", "11:00-16:00"),
        ("D3", "Dr. Rohit Mehta", "Orthopedic", "09:00-13:00"),
        ("D4", "Dr. Kavita Rao", "Pediatrician", "10:00-15:00"),
        ("D5", "Dr. Sanjay Iyer", "ENT Specialist", "12:00-17:00"),
    ]

    for doctor in doctors:
        cursor.execute(
            """
            INSERT OR IGNORE INTO doctors (doctor_id, doctor_name, speciality, office_timing)
            VALUES (?, ?, ?, ?)
            """,
            doctor,
        )

    conn.commit()
    conn.close()


def get_all_doctors():
    """Return all doctors as list of tuples (doctor_id, doctor_name, speciality, office_timing)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT doctor_id, doctor_name, speciality, office_timing FROM doctors ORDER BY doctor_id"
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_doctor_by_speciality(speciality: str):
    """Return first matching doctor tuple or None."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT doctor_id, doctor_name, speciality, office_timing
        FROM doctors
        WHERE speciality = ?
        LIMIT 1
        """,
        (speciality,),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def get_doctor_by_id(doctor_id: str):
    """Return doctor tuple or None."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT doctor_id, doctor_name, speciality, office_timing
        FROM doctors
        WHERE doctor_id = ?
        """,
        (doctor_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def create_customer(customer_id: str, name: str, phone: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO customers (customer_id, name, phone)
        VALUES (?, ?, ?)
        """,
        (customer_id, name, phone),
    )
    conn.commit()
    conn.close()


def get_customer_by_phone(phone: str):
    """Return (customer_id, name, phone) or None."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT customer_id, name, phone FROM customers WHERE phone = ? LIMIT 1",
        (phone,),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def create_booking(
    booking_id: str,
    doctor_id: str,
    customer_id: str,
    appointment_date: str,
    appointment_time: str,
    status: str = "Confirmed",
) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO bookings (booking_id, doctor_id, customer_id, appointment_date, appointment_time, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (booking_id, doctor_id, customer_id, appointment_date, appointment_time, status),
    )
    conn.commit()
    conn.close()


def get_bookings_by_doctor_and_date(doctor_id: str, appointment_date: str):
    """Return list of booked times (HH:MM) for that doctor on that date."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT appointment_time FROM bookings
        WHERE doctor_id = ? AND appointment_date = ? AND status = 'Confirmed'
        """,
        (doctor_id, appointment_date),
    )
    times = [row[0] for row in cursor.fetchall()]
    conn.close()
    return times


def get_booking_by_id(booking_id: str):
    """Return full booking row or None."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT booking_id, doctor_id, customer_id, appointment_date, appointment_time, status
        FROM bookings
        WHERE booking_id = ?
        """,
        (booking_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def insert_doctor_booking_alert(
    notification_id: str,
    booking_id: str,
    doctor_id: str,
    doctor_name: str,
    patient_name: str,
    patient_phone: str,
    appointment_date: str,
    appointment_time_display: str,
    created_at: str,
) -> None:
    """Queue an alert for clinic staff to inform the doctor about a new booking."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO doctor_booking_alerts (
            notification_id, booking_id, doctor_id, doctor_name,
            patient_name, patient_phone, appointment_date, appointment_time_display,
            status, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        """,
        (
            notification_id,
            booking_id,
            doctor_id,
            doctor_name,
            patient_name,
            patient_phone,
            appointment_date,
            appointment_time_display,
            created_at,
        ),
    )
    conn.commit()
    conn.close()


def list_doctor_booking_alerts(status: str | None = "pending"):
    """Return alert rows. N newest first. status: 'pending', 'notified', or None for all."""
    conn = get_connection()
    cursor = conn.cursor()
    if status is None:
        cursor.execute(
            """
            SELECT notification_id, booking_id, doctor_id, doctor_name, patient_name,
                   patient_phone, appointment_date, appointment_time_display, status,
                   created_at, notified_at
            FROM doctor_booking_alerts
            ORDER BY created_at DESC
            """
        )
    else:
        cursor.execute(
            """
            SELECT notification_id, booking_id, doctor_id, doctor_name, patient_name,
                   patient_phone, appointment_date, appointment_time_display, status,
                   created_at, notified_at
            FROM doctor_booking_alerts
            WHERE status = ?
            ORDER BY created_at DESC
            """,
            (status,),
        )
    rows = cursor.fetchall()
    conn.close()
    return rows


def mark_doctor_alert_notified(notification_id: str, notified_at: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE doctor_booking_alerts
        SET status = 'notified', notified_at = ?
        WHERE notification_id = ? AND status = 'pending'
        """,
        (notified_at, notification_id),
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialized successfully.")
