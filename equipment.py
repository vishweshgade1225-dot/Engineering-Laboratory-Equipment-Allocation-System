
# ==========================================
# Engineering Laboratory Equipment
# Allocation System
# ==========================================

# 1. Import Required Modules
import threading
import uuid
from datetime import datetime
from equipment_catalog import EQUIPMENT_CATALOG

# 2. Define Laboratory Equipment

# Build equipment inventory from all six departments.
# Each equipment gets a unique ID based on department and lab.

equipment = {}

for department, laboratories in EQUIPMENT_CATALOG.items():
    for laboratory, items in laboratories.items():
        for equipment_name, quantity in items.items():

            equipment_id = (
                f"{department}|{laboratory}|{equipment_name}"
            )

            equipment[equipment_id] = quantity

# 3. Create Counting Semaphores
semaphores = {
    name: threading.BoundedSemaphore(value=quantity)
    for name, quantity in equipment.items()
}


# 4. Create Mutex Lock
mutex = threading.Lock()


# 5. Initialize Shared Data
bookings = []

waiting = {
    name: [] for name in equipment
}


# ==========================================
# 6. Equipment Booking Function
# ==========================================

def book_equipment(
    student,
    equipment_name,
    enrollment="",
    department="",
    laboratory="",
    purpose=""
):
    if equipment_name not in equipment:
        return {"error": "Invalid equipment selected"}

    if not isinstance(student, str) or not student.strip():
        return {"error": "Student name is required"}

    student = student.strip()

    student_details = {
        "student": student,
        "enrollment": enrollment,
        "department": department,
        "laboratory": laboratory,
        "purpose": purpose
    }

    with mutex:
        semaphore = semaphores[equipment_name]
        acquired = semaphore.acquire(blocking=False)

        if not acquired:
            waiting[equipment_name].append(student_details)

            return {
                "status": "waiting",
                "message": (
                    f"{student} is waiting for "
                    f"{equipment_name.split('|')[-1]}"
                )
            }

        booking = {
            "id": str(uuid.uuid4()),
            **student_details,
            "equipment": equipment_name,
            "status": "allocated",
            "time": datetime.now().strftime("%H:%M:%S")
        }

        bookings.append(booking)

        return {
            "status": "success",
            "message": (
                f"{equipment_name.split('|')[-1]} "
                f"allocated to {student}"
            ),
            "booking": booking
        }

# ==========================================
# 7. Equipment Return Function
# ==========================================

def return_equipment(booking_id):
    with mutex:
        booking = next(
            (
                b for b in bookings
                if b["id"] == booking_id
                and b["status"] == "allocated"
            ),
            None
        )

        if booking is None:
            return {"error": "Active booking not found"}

        equipment_name = booking["equipment"]

        # Mark the existing booking as returned
        booking["status"] = "returned"

        # FIFO: Allocate to the first waiting student
        if waiting[equipment_name]:
            next_student = waiting[equipment_name].pop(0)

            new_booking = {
                "id": str(uuid.uuid4()),
                **next_student,
                "equipment": equipment_name,
                "status": "allocated",
                "time": datetime.now().strftime("%H:%M:%S")
            }

            bookings.append(new_booking)

            return {
                "status": "success",
                "message": (
                    f"{equipment_name.split('|')[-1]} "
                    f"automatically allocated to "
                    f"{next_student['student']}"
                ),
                "booking": new_booking
            }

        # No waiting students: release the semaphore
        semaphores[equipment_name].release()

        return {
            "status": "success",
            "message": (
                f"{equipment_name.split('|')[-1]} "
                "returned successfully"
            )
        }
