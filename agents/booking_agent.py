# agents/booking_agent.py - LangGraph agent implementation

from __future__ import annotations

import os
from typing import List, Optional, TypedDict

from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import Command, interrupt
from openai import OpenAI

from data.db import init_db
from services.booking_service import confirm_booking, get_available_slots, next_open_dates
from services.doctor_service import get_doctor_info, get_specialities_list

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class BookingState(TypedDict):
    """State for the booking conversation."""

    messages: List[dict]
    stage: str
    selected_speciality: Optional[str]
    selected_doctor: Optional[dict]
    selected_date: Optional[str]
    selected_slot: Optional[str]
    customer_name: Optional[str]
    customer_phone: Optional[str]
    booking_id: Optional[str]
    available_options: List[str]


def create_initial_state() -> BookingState:
    return {
        "messages": [],
        "stage": "greeting",
        "selected_speciality": None,
        "selected_doctor": None,
        "selected_date": None,
        "selected_slot": None,
        "customer_name": None,
        "customer_phone": None,
        "booking_id": None,
        "available_options": [],
    }


def call_llm(
    system_prompt: str,
    user_prompt: str,
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0,
    max_tokens: int = 120,
) -> str:
    """Centralized helper for LLM calls; returns assistant text or empty string."""
    if not os.getenv("OPENAI_API_KEY"):
        return ""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = response.choices[0].message.content
        return (choice or "").strip()
    except Exception as exc:
        print(f"LLM call error: {exc}")
        return ""


def _wants_to_book(text: str) -> Optional[bool]:
    """Return True/False if intent is clear; None if unclear."""
    t = text.lower()
    if any(k in t for k in ("no", "not now", "don't", "dont", "later", "cancel")):
        return False
    if any(
        k in t
        for k in (
            "yes",
            "book",
            "appointment",
            "schedule",
            "reserve",
            "sure",
            "ok",
            "okay",
        )
    ):
        return True
    return None


def greeting_node(state: BookingState) -> BookingState:
    init_db()
    prompt = (
        "Welcome to **CarePlus Clinic**. I can help you book an appointment. "
        "Would you like to continue?"
    )
    choice = interrupt(
        {"content": prompt, "available_options": ["Yes, book an appointment", "No, thanks"]}
    )
    intent = _wants_to_book(choice)
    if intent is False:
        return {
            **state,
            "stage": "cancelled",
            "messages": state["messages"] + [{"role": "user", "content": choice}],
        }
    if intent is None and os.getenv("OPENAI_API_KEY"):
        sys_msg = (
            "Classify if the user wants to book a medical appointment. "
            "Reply with exactly YES or NO."
        )
        out = call_llm(sys_msg, choice, max_tokens=5).upper()
        if "NO" in out and "YES" not in out:
            return {
                **state,
                "stage": "cancelled",
                "messages": state["messages"] + [{"role": "user", "content": choice}],
            }

    return {
        **state,
        "stage": "select_speciality",
        "messages": state["messages"] + [{"role": "user", "content": choice}],
    }


def route_after_greeting(state: BookingState) -> str:
    if state.get("stage") == "cancelled":
        return "cancelled"
    return "select_speciality"


def select_speciality_node(state: BookingState) -> BookingState:
    specs = get_specialities_list()
    prompt = "Great! Please choose a **medical specialty**."
    choice = interrupt({"content": prompt, "available_options": specs})
    if choice not in specs:
        normalized = next((s for s in specs if s.lower() in choice.lower()), specs[0])
        choice = normalized

    return {
        **state,
        "selected_speciality": choice,
        "stage": "select_doctor",
        "messages": state["messages"] + [{"role": "user", "content": choice}],
    }


def select_doctor_node(state: BookingState) -> BookingState:
    info = get_doctor_info(state["selected_speciality"] or "")
    if not info:
        msg = "Sorry, no doctor is available for that specialty right now."
        return {
            **state,
            "stage": "cancelled",
            "messages": state["messages"] + [{"role": "assistant", "content": msg}],
        }

    text = (
        f"You'll meet **{info['doctor_name']}** — {info['speciality']}.\n\n"
        f"**Office hours:** {info['office_timing']}"
    )
    return {
        **state,
        "selected_doctor": info,
        "stage": "select_date",
        "messages": state["messages"] + [{"role": "assistant", "content": text}],
    }


def select_date_node(state: BookingState) -> BookingState:
    pairs = next_open_dates(5)
    options = [lbl for _, lbl in pairs]
    label_to_iso = {lbl: iso for iso, lbl in pairs}
    prompt = "Which **day** works best for you?"
    choice = interrupt({"content": prompt, "available_options": options})
    selected = label_to_iso.get(choice)
    if not selected:
        selected = pairs[0][0]

    return {
        **state,
        "selected_date": selected,
        "stage": "select_slot",
        "messages": state["messages"] + [{"role": "user", "content": choice}],
    }


def select_slot_node(state: BookingState) -> BookingState:
    doc = state["selected_doctor"] or {}
    doctor_id = doc.get("doctor_id", "")
    timing = doc.get("office_timing", "09:00-17:00")
    date_str = state["selected_date"] or ""

    slots = get_available_slots(doctor_id, timing, date_str)
    if not slots:
        msg = (
            "There are **no open slots** on that day. Let's pick another day "
            "from the list."
        )
        return {
            **state,
            "stage": "select_date",
            "messages": state["messages"] + [{"role": "assistant", "content": msg}],
        }

    prompt = "Here are **available times**. Tap one to continue."
    choice = interrupt({"content": prompt, "available_options": slots})
    picked = choice
    if picked not in slots:
        picked = next((s for s in slots if s in choice), slots[0])

    return {
        **state,
        "selected_slot": picked,
        "stage": "confirm",
        "messages": state["messages"] + [{"role": "user", "content": picked}],
    }


def route_after_slot(state: BookingState) -> str:
    if state.get("stage") == "select_date":
        return "select_date"
    return "confirm"


def confirm_node(state: BookingState) -> BookingState:
    d = state["selected_doctor"] or {}
    summary = (
        "Please **confirm** your appointment:\n\n"
        f"- **Doctor:** {d.get('doctor_name')} ({d.get('speciality')})\n"
        f"- **Date:** {state.get('selected_date')}\n"
        f"- **Time:** {state.get('selected_slot')}\n"
    )
    ans = interrupt(
        {"content": summary, "available_options": ["Confirm booking", "Cancel request"]}
    )
    lower = ans.lower()
    if "cancel" in lower:
        return {
            **state,
            "stage": "cancelled",
            "messages": state["messages"] + [{"role": "user", "content": ans}],
        }

    return {
        **state,
        "stage": "collect_details",
        "messages": state["messages"] + [{"role": "user", "content": ans}],
    }


def route_after_confirm(state: BookingState) -> str:
    if state.get("stage") == "cancelled":
        return "cancelled"
    return "collect_details"


def collect_details_node(state: BookingState) -> BookingState:
    name_msg = "What is the **patient's full name**?"
    name = interrupt({"content": name_msg, "available_options": []})
    phone_msg = "Thanks. What **phone number** should we use for this booking?"
    phone = interrupt({"content": phone_msg, "available_options": []})

    return {
        **state,
        "customer_name": name.strip(),
        "customer_phone": phone.strip(),
        "stage": "finalize",
        "messages": state["messages"]
        + [
            {"role": "user", "content": name.strip()},
            {"role": "user", "content": phone.strip()},
        ],
    }


def finalize_booking_node(state: BookingState) -> BookingState:
    doc = state["selected_doctor"] or {}
    booking_id = confirm_booking(
        doc["doctor_id"],
        state.get("customer_name") or "",
        state.get("customer_phone") or "",
        state.get("selected_slot") or "",
        state.get("selected_date"),
    )
    msg = (
        "You're all set — your appointment is **confirmed**.\n\n"
        f"- **Booking ID:** `{booking_id}`\n"
        f"- **Doctor:** {doc.get('doctor_name')}\n"
        f"- **Date:** {state.get('selected_date')}\n"
        f"- **Time:** {state.get('selected_slot')}\n"
    )
    return {
        **state,
        "booking_id": booking_id,
        "stage": "completed",
        "messages": state["messages"] + [{"role": "assistant", "content": msg}],
    }


def cancelled_node(state: BookingState) -> BookingState:
    msg = (
        "Okay — we have not booked an appointment. "
        "If you change your mind, start again anytime. Take care!"
    )
    return {
        **state,
        "stage": "cancelled",
        "messages": state["messages"] + [{"role": "assistant", "content": msg}],
    }


def build_booking_graph():
    """Build the LangGraph workflow."""
    workflow = StateGraph(BookingState)

    workflow.add_node("greeting", greeting_node)
    workflow.add_node("select_speciality", select_speciality_node)
    workflow.add_node("select_doctor", select_doctor_node)
    workflow.add_node("select_date", select_date_node)
    workflow.add_node("select_slot", select_slot_node)
    workflow.add_node("confirm", confirm_node)
    workflow.add_node("collect_details", collect_details_node)
    workflow.add_node("finalize_booking", finalize_booking_node)
    workflow.add_node("cancelled", cancelled_node)

    workflow.set_entry_point("greeting")
    workflow.add_conditional_edges(
        "greeting",
        route_after_greeting,
        {"cancelled": "cancelled", "select_speciality": "select_speciality"},
    )

    workflow.add_edge("select_speciality", "select_doctor")
    workflow.add_edge("select_doctor", "select_date")
    workflow.add_edge("select_date", "select_slot")

    workflow.add_conditional_edges(
        "select_slot",
        route_after_slot,
        {"select_date": "select_date", "confirm": "confirm"},
    )

    workflow.add_conditional_edges(
        "confirm",
        route_after_confirm,
        {"cancelled": "cancelled", "collect_details": "collect_details"},
    )

    workflow.add_edge("collect_details", "finalize_booking")
    workflow.add_edge("finalize_booking", END)
    workflow.add_edge("cancelled", END)

    return workflow.compile(checkpointer=MemorySaver())


booking_graph = build_booking_graph()


def _snapshot_interrupt_value(snap) -> dict | str | None:
    """Return pending interrupt payload from a LangGraph state snapshot, if any."""
    if getattr(snap, "interrupts", None):
        intr = snap.interrupts[0]
        return intr.value if hasattr(intr, "value") else intr
    if snap.tasks and snap.tasks[0].interrupts:
        intr = snap.tasks[0].interrupts[0]
        return intr.value if hasattr(intr, "value") else intr
    return None


def _has_pending_interrupt(snap) -> bool:
    return _snapshot_interrupt_value(snap) is not None


def _merge_interrupt_into_messages(result: BookingState, msg_content: str, options: list) -> BookingState:
    if not msg_content:
        return result
    messages = list(result.get("messages") or [])
    last = messages[-1] if messages else None
    if last and last.get("content") == msg_content:
        last["options"] = options
    else:
        messages.append({"role": "assistant", "content": msg_content, "options": options})
    out = {**result, "messages": messages, "available_options": options}
    return out


def process_message(
    state: BookingState,
    user_message: str,
    thread_id: str = "default_session",
) -> BookingState:
    """Process a user message through the booking graph."""
    config = {"configurable": {"thread_id": thread_id}}
    init_db()

    snapshot = booking_graph.get_state(config)
    has_interrupt = _has_pending_interrupt(snapshot)

    if has_interrupt:
        result = booking_graph.invoke(Command(resume=user_message), config=config)
    else:
        if user_message.lower() != "hi" or state["messages"]:
            if not state["messages"] or state["messages"][-1].get("content") != user_message:
                state = {
                    **state,
                    "messages": state["messages"] + [{"role": "user", "content": user_message}],
                }
        result = booking_graph.invoke(state, config=config)

    snap = booking_graph.get_state(config)
    intr = _snapshot_interrupt_value(snap)
    if intr is not None:
        if isinstance(intr, dict):
            msg_content = intr.get("content", "")
            options = intr.get("available_options", [])
        else:
            msg_content = str(intr)
            options = []
        result = _merge_interrupt_into_messages(result, msg_content, options)
    else:
        result = {**result, "available_options": result.get("available_options") or []}

    return result
