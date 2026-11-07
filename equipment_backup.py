
# ==========================================
# Engineering Laboratory Equipment
# Allocation System
# ==========================================

# 1. Import Required Modules
import threading
import uuid
from datetime import datetime


# 2. Define Laboratory Equipment
equipment = {
    "oscilloscope": 2,
    "multimeter": 3,
    "function_generator": 2,
    "power_supply": 1
}


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

def book_equipment(student, equipment_name):

    # Validate equipment
    if equipment_name not in equipment:
        return {"error": "Invalid equipment selected"}

    # Validate student name
    if not isinstance(student, str) or not student.strip():
        return {"error": "Student name is required"}

    student = student.strip()

    # Protect the allocation decision and records
    with mutex:

        semaphore = semaphores[equipment_name]

        # Check whether equipment is available
        acquired = semaphore.acquire(blocking=False)

        if not acquired:

            # Add student to waiting queue
            waiting[equipment_name].append(student)

            return {
                "status": "waiting",
                "message": f"{student} is waiting for {equipment_name}"
            }

        # Create booking record
        booking = {
            "id": str(uuid.uuid4()),
            "student": student,
            "equipment": equipment_name,
            "status": "allocated",
            "time": datetime.now().strftime("%H:%M:%S")
        }

        # Save booking
        bookings.append(booking)

        return {
            "status": "success",
            "message": f"{equipment_name} allocated to {student}",
            "booking": booking
        }


# ==========================================
# 7. Equipment Return Function
# ==========================================

def return_equipment(booking_id):

    # Protect shared data using mutex
    with mutex:

        # Find active booking
        booking = next(
            (
                b for b in bookings
                if b["id"] == booking_id
                and b["status"] == "allocated"
            ),
            None
        )

        if booking is None:
            return {
                "error": "Active booking not found"
            }

        equipment_name = booking["equipment"]

        # Mark equipment as returned
        booking["status"] = "returned"

        # Check waiting queue
        if waiting[equipment_name]:

            # Get next waiting student
            next_student = waiting[equipment_name].pop(0)

            # Create new booking
            new_booking = {
                "id": str(uuid.uuid4()),
                "student": next_student,
                "equipment": equipment_name,
                "status": "allocated",
                "time": datetime.now().strftime("%H:%M:%S")
            }

            bookings.append(new_booking)

            return {
                "status": "success",
                "message": f"Equipment transferred to {next_student}",
                "booking": new_booking
            }

        # Release semaphore if nobody is waiting
        semaphores[equipment_name].release()

        return {
            "status": "success",
            "message": f"{equipment_name} returned successfully"
        }
