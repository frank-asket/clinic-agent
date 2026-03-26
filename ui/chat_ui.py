"""Streamlit UI for the clinic booking chatbot."""

import uuid

import streamlit as st

from agents.booking_agent import create_initial_state, process_message
from data.db import init_db


def initialize_session():
    """Initialize session state."""
    if "state" not in st.session_state:
        st.session_state.state = create_initial_state()
    if "initialized" not in st.session_state:
        st.session_state.initialized = False
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())


def handle_user_input(user_input: str):
    """Handle user input and process through agent."""
    st.session_state.state = process_message(
        st.session_state.state,
        user_input,
        thread_id=st.session_state.session_id,
    )
    st.rerun()


def display_chat_history():
    """Display the chat history with persistent options and styling."""
    messages = st.session_state.state.get("messages", [])
    terminal_stages = ("completed", "cancelled")
    for i, message in enumerate(messages):
        if message["role"] == "assistant":
            with st.chat_message("assistant"):
                st.markdown(message["content"])
                options = message.get("options", [])
                if options:
                    last = i == len(messages) - 1
                    stage = st.session_state.state.get("stage", "")
                    if last and stage not in terminal_stages:
                        st.markdown("---")
                        cols = st.columns(min(len(options), 3))
                        for idx, option in enumerate(options):
                            with cols[idx % 3]:
                                if st.button(
                                    option,
                                    key=f"btn_{i}_{idx}",
                                    use_container_width=True,
                                ):
                                    handle_user_input(option)
                    else:
                        joined = "  ".join([f"`{opt}`" for opt in options])
                        st.markdown(f"**Choices:** {joined}")
        else:
            with st.chat_message("user"):
                st.markdown(message["content"])


def run_chat_ui():
    """Run the chat UI."""
    st.set_page_config(
        page_title="CarePlus Clinic - Book Appointment",
        page_icon="🏥",
        layout="centered",
    )

    st.markdown(
        """
        <style>
        [data-testid="stChatMessageUser"] {
            flex-direction: row-reverse;
            text-align: right;
            background-color: #e0f2f1;
            border-radius: 15px 15px 0 15px;
        }
        [data-testid="stChatMessageAssistant"] {
            background-color: #f5f5f5;
            border-radius: 15px 15px 15px 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    init_db()
    initialize_session()

    st.title("CarePlus Clinic")
    st.markdown("*Book your doctor appointment easily*")
    st.markdown("---")

    if not st.session_state.initialized:
        st.session_state.state = process_message(
            st.session_state.state,
            "Hi",
            thread_id=st.session_state.session_id,
        )
        st.session_state.initialized = True
        st.rerun()

    display_chat_history()

    stage = st.session_state.state.get("stage", "")
    if stage not in ("completed", "cancelled"):
        if prompt := st.chat_input("Type your message here..."):
            handle_user_input(prompt)
    else:
        st.markdown("---")
        if st.button("Start New Booking", use_container_width=True):
            st.session_state.state = create_initial_state()
            st.session_state.initialized = False
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()
