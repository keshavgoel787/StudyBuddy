"""
Debug script to check bus schedule and test bus finding logic.
"""

import sys
from pathlib import Path
from datetime import datetime, time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.bus_schedule import BusSchedule, Direction

def main():
    db = SessionLocal()

    try:
        # Check what day of week today is
        today = datetime.now()
        day_of_week = today.isoweekday()
        print(f"Today: {today.strftime('%A, %Y-%m-%d')}")
        print(f"Day of week: {day_of_week} (1=Mon, 7=Sun)")
        print()

        # Check outbound buses for today
        print("=== OUTBOUND BUSES (Main & Murray → UDC) ===")
        outbound = db.query(BusSchedule).filter(
            BusSchedule.direction == Direction.outbound,
            BusSchedule.day_of_week == day_of_week
        ).order_by(BusSchedule.departure_time).limit(10).all()

        for bus in outbound:
            print(f"Departs: {bus.departure_time.strftime('%I:%M %p')} → Arrives: {bus.arrival_time.strftime('%I:%M %p')}")

        print()
        print("=== Testing bus finding for 10:00 AM class ===")

        # Simulate finding a bus for 10:00 AM class with 15 min buffer
        target_time = time(9, 45)  # Should arrive by 9:45 AM
        print(f"Target arrival time: {target_time.strftime('%I:%M %p')}")

        buses_before = db.query(BusSchedule).filter(
            BusSchedule.direction == Direction.outbound,
            BusSchedule.day_of_week == day_of_week,
            BusSchedule.arrival_time <= target_time
        ).order_by(BusSchedule.arrival_time.desc()).all()

        print(f"Found {len(buses_before)} buses that arrive before {target_time.strftime('%I:%M %p')}")
        if buses_before:
            best = buses_before[0]
            print(f"Best bus: Depart {best.departure_time.strftime('%I:%M %p')} → Arrive {best.arrival_time.strftime('%I:%M %p')}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
