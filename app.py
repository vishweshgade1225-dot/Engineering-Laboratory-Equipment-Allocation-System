
from flask import Flask, render_template, request, jsonify

from equipment import (
    equipment,
    mutex,
    bookings,
    waiting,
    book_equipment,
    return_equipment
)


from equipment_catalog import EQUIPMENT_CATALOG

app = Flask(__name__)


# 1. Display Dashboard

@app.route("/")
def home():
    return render_template(
        "index.html",
        equipment_catalog=EQUIPMENT_CATALOG
    )

# 2. Book Equipment

@app.route("/book", methods=["POST"])
def book():
    data = request.get_json(silent=True) or {}

    student = data.get("student", "")
    enrollment = data.get("enrollment", "")
    department = data.get("department", "")
    laboratory = data.get("laboratory", "")
    equipment_name = data.get("equipment", "")
    purpose = data.get("purpose", "")

    # Validate student information
    if not isinstance(student, str) or not student.strip():
        return jsonify({"error": "Student name is required"}), 400

    if not isinstance(enrollment, str) or not enrollment.strip():
        return jsonify({"error": "Enrollment number is required"}), 400

    # Validate department, laboratory, and equipment
    if not all(isinstance(value, str) for value in (
        department, laboratory, equipment_name, purpose
    )):
        return jsonify({"error": "Invalid booking information"}), 400

    if (
        department not in EQUIPMENT_CATALOG
        or laboratory not in EQUIPMENT_CATALOG[department]
    ):
        return jsonify({"error": "Invalid department or laboratory"}), 400

    equipment_prefix = f"{department}|{laboratory}|"

    if (
        not equipment_name.startswith(equipment_prefix)
        or equipment_name not in equipment
    ):
        return jsonify({"error": "Invalid equipment selection"}), 400

    if purpose not in ("Practical", "Experiment", "Project", "Research"):
        return jsonify({"error": "Invalid purpose of use"}), 400

    result = book_equipment(
        student=student,
        equipment_name=equipment_name,
        enrollment=enrollment.strip(),
        department=department,
        laboratory=laboratory,
        purpose=purpose
    )    

    if "error" in result:
        return jsonify(result), 400

    return jsonify(result)

# 3. Return Equipment
@app.route("/return", methods=["POST"])
def return_item():
    data = request.get_json(silent=True) or {}

    booking_id = data.get("booking_id", "")

    result = return_equipment(booking_id)

    if "error" in result:
        return jsonify(result), 400

    return jsonify(result)


# 4. Display Live Equipment Status
@app.route("/status", methods=["GET"])
def status():

    with mutex:
        active = [
            b for b in bookings
            if b["status"] == "allocated"
        ]

        equipment_status = {}

        for name, total in equipment.items():

            in_use = sum(
                1 for b in active
                if b["equipment"] == name
            )

            equipment_status[name] = {
                "total": total,
                "available": total - in_use,
                "in_use": in_use,
                "waiting": len(waiting[name])
            }

        return jsonify({
            "equipment": equipment_status,
            "bookings": list(bookings),
            "waiting_queue": {
                name: list(queue)
                for name, queue in waiting.items()
            },
            "total": sum(equipment.values()),
            "available": sum(
                item["available"]
                for item in equipment_status.values()
            ),
            "in_use": len(active),
            "waiting": sum(
                len(queue)
                for queue in waiting.values()
            )
    })

if __name__ == "__main__":
    app.run(debug=True, threaded=True)
