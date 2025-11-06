"""
Script to populate the bus_schedules table with Westside (WS) route data.
Run this once to seed the database with bus times.

Usage:
    python -m scripts.populate_bus_schedule
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from datetime import time
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.bus_schedule import BusSchedule, Direction


def calculate_duration(departure: time, arrival: time) -> int:
    """Calculate duration in minutes between two times."""
    dept_minutes = departure.hour * 60 + departure.minute
    arr_minutes = arrival.hour * 60 + arrival.minute

    # Handle overnight trips (arrival next day)
    if arr_minutes < dept_minutes:
        arr_minutes += 24 * 60

    return arr_minutes - dept_minutes


def populate_outbound_schedule(db: Session):
    """
    Populate outbound schedule (Main & Murray → UDC).
    Data from the Westside Outbound schedule image.
    """
    # Format: (main_and_murray_time, udc_arrival_time, is_late_night)
    outbound_times = [
        ("07:30", "07:40", False),
        ("07:45", "07:55", False),
        ("08:05", "08:15", False),
        ("08:20", "08:30", False),
        ("08:55", "09:05", False),  # Removed 9:10->9:20 (not in schedule)
        ("09:10", "09:20", False),  # This one exists
        ("09:25", "09:35", False),
        ("09:45", "09:55", False),
        ("10:00", "10:10", False),
        ("10:50", "11:00", False),
        ("11:05", "11:15", False),
        ("11:25", "11:35", False),
        ("11:40", "11:50", False),
        ("12:15", "12:25", False),
        ("12:30", "12:40", False),
        ("13:20", "13:30", False),
        ("14:45", "14:55", False),
        ("15:00", "15:10", False),
        ("16:00", "16:10", False),
        ("16:25", "16:35", False),
        ("17:25", "17:35", False),
        ("18:05", "18:15", False),
        ("18:50", "19:00", False),
        ("19:00", "19:10", False),
        ("19:45", "19:55", False),
        ("20:00", "20:10", False),
        ("20:45", "20:55", False),
        ("21:30", "21:40", True),   # Late night
        ("21:45", "21:55", True),
        ("22:30", "22:40", True),
        ("23:00", "23:10", True),
        ("23:15", "23:25", True),
    ]

    for main_murray_str, udc_str, is_late in outbound_times:
        dept_time = time.fromisoformat(main_murray_str)
        arr_time = time.fromisoformat(udc_str)
        duration = calculate_duration(dept_time, arr_time)

        # Create for Monday through Friday (1-5)
        for day in range(1, 6):
            bus = BusSchedule(
                direction=Direction.outbound,
                departure_time=dept_time,
                arrival_time=arr_time,
                day_of_week=day,
                duration_minutes=duration,
                is_late_night=is_late
            )
            db.add(bus)


def populate_inbound_schedule(db: Session):
    """
    Populate inbound schedule (UDC → Main & Murray).
    Data from the Westside Inbound schedule image.
    """
    # Format: (udc_departure_time, main_and_murray_time, is_late_night)
    inbound_times = [
        ("07:20", "07:23", False),
        ("07:33", "07:36", False),
        ("08:25", "08:28", False),
        ("08:40", "08:43", False),
        ("09:00", "09:03", False),
        ("09:15", "09:18", False),
        ("10:05", "10:08", False),
        ("10:20", "10:23", False),
        ("10:40", "10:43", False),
        ("11:00", "11:03", False),
        ("11:45", "11:48", False),
        ("12:00", "12:03", False),
        ("12:35", "12:38", False),
        ("13:10", "13:13", False),
        ("13:30", "13:33", False),
        ("14:15", "14:18", False),
        ("15:05", "15:08", False),
        ("15:40", "15:43", False),
        ("15:55", "15:58", False),
        ("16:55", "16:58", False),
        ("17:20", "17:23", False),
        ("17:45", "17:48", False),
        ("18:05", "18:08", False),
        ("18:35", "18:38", False),
        ("19:00", "19:03", False),
        ("19:55", "19:58", False),
        ("20:35", "20:38", True),   # Late night
        ("21:05", "21:08", True),
        ("21:35", "21:38", True),
        ("22:40", "22:43", True),
        ("23:35", "23:38", True),
        ("00:05", "00:08", True),   # Past midnight
    ]

    for udc_str, main_murray_str, is_late in inbound_times:
        dept_time = time.fromisoformat(udc_str)
        arr_time = time.fromisoformat(main_murray_str)
        duration = calculate_duration(dept_time, arr_time)

        # Create for Monday through Friday (1-5)
        for day in range(1, 6):
            bus = BusSchedule(
                direction=Direction.inbound,
                departure_time=dept_time,
                arrival_time=arr_time,
                day_of_week=day,
                duration_minutes=duration,
                is_late_night=is_late
            )
            db.add(bus)


def main():
    """Main function to populate bus schedules."""
    db = SessionLocal()

    try:
        # Clear existing bus schedules
        print("Clearing existing bus schedules...")
        db.query(BusSchedule).delete()
        db.commit()

        # Populate outbound schedule
        print("Populating outbound schedule (Main & Murray → UDC)...")
        populate_outbound_schedule(db)
        db.commit()

        # Populate inbound schedule
        print("Populating inbound schedule (UDC → Main & Murray)...")
        populate_inbound_schedule(db)
        db.commit()

        # Count and display results
        outbound_count = db.query(BusSchedule).filter(
            BusSchedule.direction == Direction.outbound
        ).count()
        inbound_count = db.query(BusSchedule).filter(
            BusSchedule.direction == Direction.inbound
        ).count()

        print(f"\n✓ Successfully populated bus schedules!")
        print(f"  - Outbound buses: {outbound_count}")
        print(f"  - Inbound buses: {inbound_count}")
        print(f"  - Total: {outbound_count + inbound_count}")

    except Exception as e:
        print(f"\n✗ Error populating bus schedules: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
