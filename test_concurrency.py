
import threading
from equipment import (
    equipment,
    bookings,
    waiting,
    mutex,
    book_equipment
)

# Students requesting equipment simultaneously
students = [
    "Rahul",
    "Priya",
    "Ravi",
    "Tinku",
    "Sai",
    "Chandhu",
    "Usman",
    "Anjali",
    "Kiran",
    "Arjun"
]

results = []
results_lock = threading.Lock()

# All students request the same equipment
equipment_name = "oscilloscope"

# Synchronize thread start times
start_barrier = threading.Barrier(len(students))


def request_equipment(student):
    start_barrier.wait()

    result = book_equipment(student, equipment_name)

    with results_lock:
        results.append((student, result["status"]))


# Create 10 threads
threads = []

for student in students:
    thread = threading.Thread(
        target=request_equipment,
        args=(student,)
    )
    threads.append(thread)


print("\nStarting 10 simultaneous equipment requests...\n")

# Start all threads
for thread in threads:
    thread.start()

# Wait for all threads to finish
for thread in threads:
    thread.join()


# Check final results
with mutex:
    allocated = [
        booking for booking in bookings
        if booking["equipment"] == equipment_name
        and booking["status"] == "allocated"
    ]

    waiting_students = list(waiting[equipment_name])

print("RESULTS")
print("-" * 45)

for student, status in results:
    print(f"{student:12} -> {status.upper()}")

print("-" * 45)
print(f"Total Students    : {len(students)}")
print(f"Equipment Capacity: {equipment[equipment_name]}")
print(f"Allocated         : {len(allocated)}")
print(f"Waiting           : {len(waiting_students)}")

# Verify that overbooking did not occur
assert len(allocated) == 2, "Unexpected allocation count!"
assert len(waiting_students) == 8, "Unexpected waiting count!"

print("\nTEST PASSED: No equipment overbooking occurred!")


# Test independent equipment semaphores
print("\nTESTING INDEPENDENT SEMAPHORES")
print("-" * 45)

result = book_equipment("Vikram", "multimeter")

print("Student  : Vikram")
print("Equipment: Multimeter")
print("Result   :", result["status"].upper())

assert result["status"] == "success", (
    "Multimeter allocation failed!"
)

print("\nTEST PASSED: Equipment semaphores are independent!")
