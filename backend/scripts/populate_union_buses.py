"""
Script to populate Union ↔ Main & Murray bus schedules.
Run this with: python -m scripts.populate_union_buses
"""

from datetime import time
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.bus_schedule import BusSchedule, Direction, Route


def add_union_outbound_buses(db: Session):
    """Add Union → Main & Murray buses (outbound to Main & Murray for return to campus)"""

    # Monday-Friday buses (regular schedule from screenshot)
    regular_buses = [
        ("07:15", "07:24"),  # Leaves Union 7:15 AM, arrives Main & Murray 7:24 AM
        ("07:30", "07:39"),
        ("07:50", "07:59"),
        ("08:05", "08:14"),
        ("08:55", "09:04"),
        ("09:10", "09:19"),
        ("09:30", "09:39"),
        ("09:45", "09:54"),
        ("10:35", "10:44"),
        ("10:50", "10:59"),
        ("11:10", "11:19"),
        ("11:25", "11:34"),
        ("12:00", "12:09"),
        ("12:15", "12:24"),
        ("13:05", "13:14"),  # 1:05 PM
        ("14:30", "14:39"),  # 2:30 PM
        ("14:45", "14:54"),  # 2:45 PM
        ("15:45", "15:54"),  # 3:45 PM
        ("16:10", "16:19"),  # 4:10 PM
        ("17:10", "17:19"),  # 5:10 PM
        ("17:50", "17:59"),  # 5:50 PM
        ("18:35", "18:44"),  # 6:35 PM
        ("18:45", "18:54"),  # 6:45 PM
        ("19:30", "19:39"),  # 7:30 PM
        ("19:45", "19:54"),  # 7:45 PM
        ("20:30", "20:39"),  # 8:30 PM
    ]

    # Monday-Thursday only (RED in screenshot)
    monday_thursday = [
        ("21:45", "21:54"),  # 9:45 PM
        ("22:45", "22:54"),  # 10:45 PM
    ]

    # Friday only (GREEN in screenshot)
    friday_only = [
        ("21:15", "21:24"),  # 9:15 PM
        ("23:00", "23:09"),  # 11:00 PM
        ("23:45", "23:54"),  # 11:45 PM
    ]

    # Add regular Monday-Friday buses
    for depart, arrive in regular_buses:
        depart_time = time.fromisoformat(depart)
        arrive_time = time.fromisoformat(arrive)
        duration = 9  # 9 minutes travel time

        for day in range(1, 6):  # Monday (1) to Friday (5)
            bus = BusSchedule(
                route=Route.union,
                direction=Direction.outbound,  # To Main & Murray (for return to campus)
                departure_time=depart_time,
                arrival_time=arrive_time,
                day_of_week=day,
                duration_minutes=duration,
                is_late_night=(depart_time.hour >= 21)  # After 9 PM
            )
            db.add(bus)

    # Add Monday-Thursday only buses
    for depart, arrive in monday_thursday:
        depart_time = time.fromisoformat(depart)
        arrive_time = time.fromisoformat(arrive)
        duration = 9

        for day in range(1, 5):  # Monday (1) to Thursday (4)
            bus = BusSchedule(
                route=Route.union,
                direction=Direction.outbound,
                departure_time=depart_time,
                arrival_time=arrive_time,
                day_of_week=day,
                duration_minutes=duration,
                is_late_night=True
            )
            db.add(bus)

    # Add Friday only buses
    for depart, arrive in friday_only:
        depart_time = time.fromisoformat(depart)
        arrive_time = time.fromisoformat(arrive)
        duration = 9

        bus = BusSchedule(
            route=Route.union,
            direction=Direction.outbound,
            departure_time=depart_time,
            arrival_time=arrive_time,
            day_of_week=5,  # Friday
            duration_minutes=duration,
            is_late_night=True
        )
        db.add(bus)


def add_union_inbound_buses(db: Session):
    """Add Main & Murray → Union buses (inbound from Main & Murray back home)"""

    # Monday-Friday buses (regular schedule from screenshot)
    regular_buses = [
        ("07:20", "07:23"),  # Very short trip - 3 minutes
        ("07:33", "07:36"),
        ("08:25", "08:28"),
        ("08:40", "08:43"),
        ("09:00", "09:03"),
        ("10:05", "10:08"),
        ("10:40", "10:43"),
        ("11:00", "11:03"),
        ("12:00", "12:03"),
        ("12:35", "12:38"),
        ("13:10", "13:13"),  # 1:10 PM
        ("15:05", "15:08"),  # 3:05 PM
        ("15:40", "15:43"),  # 3:40 PM
        ("15:55", "15:58"),  # 3:55 PM
        ("16:55", "16:58"),  # 4:55 PM
        ("17:20", "17:23"),  # 5:20 PM
        ("17:45", "17:48"),  # 5:45 PM
        ("18:05", "18:08"),  # 6:05 PM
        ("18:35", "18:38"),  # 6:35 PM
        ("19:00", "19:03"),  # 7:00 PM
        ("19:55", "19:58"),  # 7:55 PM
        ("20:35", "20:38"),  # 8:35 PM
        ("21:05", "21:08"),  # 9:05 PM
        ("21:35", "21:38"),  # 9:35 PM
        ("22:40", "22:43"),  # 10:40 PM
    ]

    # Special colored times
    teal_buses = [("09:15", "09:18")]  # Teal - all weekdays
    maroon_monday_thursday = [
        ("10:20", "10:23"),
        ("11:45", "11:48"),
        ("13:30", "13:33"),  # 1:30 PM
        ("14:15", "14:18"),  # 2:15 PM
    ]

    # Monday-Thursday only (RED in screenshot)
    red_monday_thursday = [
        ("23:20", "23:23"),  # 11:20 PM
        ("00:05", "00:08"),  # 12:05 AM (next day)
    ]

    # Friday only (GREEN in screenshot)
    green_friday = [
        ("23:35", "23:38"),  # 11:35 PM
    ]

    # Add regular Monday-Friday buses
    for depart, arrive in regular_buses:
        depart_time = time.fromisoformat(depart)
        arrive_time = time.fromisoformat(arrive)
        duration = 3

        for day in range(1, 6):  # Monday (1) to Friday (5)
            bus = BusSchedule(
                route=Route.union,
                direction=Direction.inbound,  # From Main & Murray back home
                departure_time=depart_time,
                arrival_time=arrive_time,
                day_of_week=day,
                duration_minutes=duration,
                is_late_night=(depart_time.hour >= 21)
            )
            db.add(bus)

    # Add teal buses (all weekdays)
    for depart, arrive in teal_buses:
        depart_time = time.fromisoformat(depart)
        arrive_time = time.fromisoformat(arrive)

        for day in range(1, 6):
            bus = BusSchedule(
                route=Route.union,
                direction=Direction.inbound,
                departure_time=depart_time,
                arrival_time=arrive_time,
                day_of_week=day,
                duration_minutes=3,
                is_late_night=False
            )
            db.add(bus)

    # Add maroon Monday-Thursday buses
    for depart, arrive in maroon_monday_thursday:
        depart_time = time.fromisoformat(depart)
        arrive_time = time.fromisoformat(arrive)

        for day in range(1, 5):
            bus = BusSchedule(
                route=Route.union,
                direction=Direction.inbound,
                departure_time=depart_time,
                arrival_time=arrive_time,
                day_of_week=day,
                duration_minutes=3,
                is_late_night=False
            )
            db.add(bus)

    # Add red Monday-Thursday buses
    for depart, arrive in red_monday_thursday:
        depart_time = time.fromisoformat(depart)
        arrive_time = time.fromisoformat(arrive)

        for day in range(1, 5):
            bus = BusSchedule(
                route=Route.union,
                direction=Direction.inbound,
                departure_time=depart_time,
                arrival_time=arrive_time,
                day_of_week=day,
                duration_minutes=3,
                is_late_night=True
            )
            db.add(bus)

    # Add green Friday buses
    for depart, arrive in green_friday:
        depart_time = time.fromisoformat(depart)
        arrive_time = time.fromisoformat(arrive)

        bus = BusSchedule(
            route=Route.union,
            direction=Direction.inbound,
            departure_time=depart_time,
            arrival_time=arrive_time,
            day_of_week=5,  # Friday
            duration_minutes=3,
            is_late_night=True
        )
        db.add(bus)


def main():
    """Main function to populate Union bus schedules"""
    db = SessionLocal()

    try:
        print("Populating Union → Main & Murray buses...")
        add_union_outbound_buses(db)

        print("Populating Main & Murray → Union buses...")
        add_union_inbound_buses(db)

        db.commit()
        print("✅ Successfully added Union route bus schedules!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
