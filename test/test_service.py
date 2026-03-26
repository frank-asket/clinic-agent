from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.db import init_db  # noqa: E402
from services.booking_service import confirm_booking  # noqa: E402
from services.doctor_service import generate_time_slots, get_specialities_list  # noqa: E402

if __name__ == "__main__":
    init_db()

    specialities = get_specialities_list()
    print("Available specialities:", specialities)

    slots = generate_time_slots("11:00-16:00")
    print("Available slots:", slots)

    booking_id = confirm_booking(
        doctor_id="D1",
        customer_name="John Doe",
        customer_phone="9876543210",
        time_slot="2:00 PM",
    )
    print(f"Booking confirmed: {booking_id}")
