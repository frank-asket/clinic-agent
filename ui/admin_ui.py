"""Staff-only Streamlit UI for doctor booking alerts (run via admin_app.py)."""

from __future__ import annotations

import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from data.db import init_db, list_doctor_booking_alerts, mark_doctor_alert_notified

load_dotenv()
from services.notification_service import suggested_message_for_doctor


def _admin_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --adm-bg: #0f172a;
            --adm-card: #1e293b;
            --adm-accent: #38bdf8;
            --adm-muted: #94a3b8;
            --adm-border: #334155;
        }
        .stApp {
            background: linear-gradient(165deg, #0b1220 0%, #111827 45%, #0f172a 100%);
        }
        [data-testid="stHeader"] { background-color: rgba(15, 23, 42, 0.92); border-bottom: 1px solid var(--adm-border); }
        h1 { color: #f1f5f9 !important; letter-spacing: -0.02em; }
        h2, h3 { color: #e2e8f0 !important; }
        .staff-banner {
            background: linear-gradient(90deg, #0ea5e9 0%, #6366f1 100%);
            color: white;
            padding: 0.65rem 1rem;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.9rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 14px rgba(14, 165, 233, 0.25);
        }
        section[data-testid="stSidebar"] > div {
            background-color: #0f172a;
        }
        div[data-testid="stExpander"] {
            background-color: var(--adm-card);
            border: 1px solid var(--adm-border);
            border-radius: 10px;
        }
        .stMarkdown, .stCaption, label { color: #cbd5e1; }
        hr { border-color: var(--adm-border); }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _check_staff_access() -> bool:
    """Optional gate: set ADMIN_ACCESS_PASSWORD in .env for production."""
    password = (os.getenv("ADMIN_ACCESS_PASSWORD") or "").strip()
    if not password:
        return True
    if st.session_state.get("_staff_ok"):
        return True
    st.markdown('<div class="staff-banner">CarePlus · Staff sign-in</div>', unsafe_allow_html=True)
    st.subheader("Sign in")
    entered = st.text_input("Staff password", type="password", autocomplete="current-password")
    if st.button("Unlock", type="primary"):
        if entered == password:
            st.session_state._staff_ok = True
            st.rerun()
        st.error("Incorrect password.")
    return False


def run_admin_ui() -> None:
    st.set_page_config(
        page_title="CarePlus Staff · Doctor alerts",
        page_icon="🔒",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _admin_styles()

    if not _check_staff_access():
        return

    init_db()

    if not (os.getenv("ADMIN_ACCESS_PASSWORD") or "").strip():
        st.warning(
            "This admin URL is **not** password-protected. Set `ADMIN_ACCESS_PASSWORD` in `.env` "
            "before you expose `admin_app.py` on a network."
        )

    st.markdown('<div class="staff-banner">CarePlus · Staff portal — doctor booking alerts</div>', unsafe_allow_html=True)
    st.caption(
        "Confidential: patient names and phone numbers. Do not share this browser session with patients. "
        "Patients use the public booking app only (`streamlit run app.py`)."
    )

    pending = list_doctor_booking_alerts("pending")
    recent_done = list_doctor_booking_alerts("notified")[:30]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Pending alerts", len(pending))
    with c2:
        st.metric("Resolved (shown)", len(recent_done))
    with c3:
        st.metric("Database", "clinic.db")

    st.markdown("---")

    if not pending:
        st.success("No pending alerts — all listed doctors have been notified (or no bookings yet).")
    else:
        st.subheader(f"Action required ({len(pending)})")
        for row in pending:
            (
                notification_id,
                booking_id,
                _doctor_id,
                doctor_name,
                patient_name,
                patient_phone,
                appointment_date,
                appointment_time_display,
                _status,
                created_at,
                _notified_at,
            ) = row
            title = f"{doctor_name} · {appointment_date} {appointment_time_display} · {patient_name}"
            with st.expander(title, expanded=len(pending) <= 4):
                msg = suggested_message_for_doctor(
                    doctor_name,
                    patient_name,
                    patient_phone,
                    appointment_date,
                    appointment_time_display,
                    booking_id,
                )
                st.code(msg, language=None)
                st.caption(f"Queued at {created_at} · Alert `{notification_id}` · Booking `{booking_id}`")
                if st.button(
                    "Mark as notified to doctor",
                    key=f"notify_{notification_id}",
                    type="primary",
                ):
                    mark_doctor_alert_notified(
                        notification_id,
                        datetime.now().isoformat(timespec="seconds"),
                    )
                    st.rerun()

    st.markdown("---")
    st.subheader("Recently notified")
    if recent_done:
        st.dataframe(
            [
                {
                    "Doctor": r[3],
                    "Patient": r[4],
                    "Phone": r[5],
                    "Date": r[6],
                    "Time": r[7],
                    "Booking": r[1],
                    "Notified at": r[10],
                }
                for r in recent_done
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No completed notifications yet.")
