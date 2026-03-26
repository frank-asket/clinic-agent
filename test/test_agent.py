from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.booking_agent import create_initial_state, process_message  # noqa: E402
from data.db import init_db  # noqa: E402

if __name__ == "__main__":
    init_db()

    state = create_initial_state()
    state = process_message(state, "Hi", thread_id="session_1")
    print(state["messages"][-1]["content"])
    print("Options:", state.get("available_options"))

    state = process_message(state, "Yes, book an appointment", thread_id="session_1")
    print("After booking intent — options:", state.get("available_options"))
