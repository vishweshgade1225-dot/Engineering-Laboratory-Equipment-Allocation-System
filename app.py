import os
import secrets

from flask import Flask, render_template, request, jsonify, session

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
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
app.config["PUBLIC_DEMO"] = os.environ.get("LABOS_PUBLIC_DEMO") == "1"
app.config["SECRET_KEY"] = secrets.token_bytes(32)
app.config["SESSION_COOKIE_SECURE"] = app.config["PUBLIC_DEMO"]
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


def owns_record(record):
    if not app.config["PUBLIC_DEMO"]:
        return True
    owner = session.get("booking_owner")
    return owner is not None and record.get("owner") == owner


def visible_record(record):
    details = {key: value for key, value in record.items() if key != "owner"}
    if not owns_record(record):
        details["enrollment"] = ""
    return details


# 1. Display Dashboard

@app.route("/")
def home():
    if app.config["PUBLIC_DEMO"] and "booking_owner" not in session:
        session["booking_owner"] = secrets.token_urlsafe(24)
    return render_template(
        "index.html",
        equipment_catalog=EQUIPMENT_CATALOG,
        public_demo=app.config["PUBLIC_DEMO"]
    )

# 2. Book Equipment

@app.route("/book", methods=["POST"])
def book():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Expected a JSON object"}), 400

    student = data.get("student", "")
    enrollment = data.get("enrollment", "")
    department = data.get("department", "")
    laboratory = data.get("laboratory", "")
    equipment_name = data.get("equipment", "")
    purpose = data.get("purpose", "")

    # Validate student information
    if not isinstance(student, str) or not student.strip() or len(student) > 80:
        return jsonify({"error": "Enter a student name of 1 to 80 characters"}), 400

    if not isinstance(enrollment, str) or not 1 <= len(enrollment.strip()) <= 40:
        return jsonify({"error": "Enter a roll number of 1 to 40 characters"}), 400

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

    if app.config["PUBLIC_DEMO"] and "booking_owner" not in session:
        session["booking_owner"] = secrets.token_urlsafe(24)

    result = book_equipment(
        student=student,
        equipment_name=equipment_name,
        enrollment=enrollment.strip(),
        department=department,
        laboratory=laboratory,
        purpose=purpose,
        owner=session.get("booking_owner")
    )

    if "error" in result:
        return jsonify(result), 400

    if "booking" in result:
        result["booking"] = visible_record(result["booking"])
    return jsonify(result)

# 3. Return Equipment
@app.route("/return", methods=["POST"])
def return_item():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Expected a JSON object"}), 400

    booking_id = data.get("booking_id", "")
    if not isinstance(booking_id, str) or not booking_id:
        return jsonify({"error": "Booking ID is required"}), 400

    result = return_equipment(booking_id)

    if "error" in result:
        return jsonify(result), 400

    if "booking" in result:
        result["booking"] = visible_record(result["booking"])
    return jsonify(result)


@app.route("/history/clear", methods=["POST"])
def clear_history():
    if request.get_json(silent=True) != {}:
        return jsonify({"error": "Expected an empty JSON object"}), 400

    with mutex:
        previous_count = len(bookings)
        bookings[:] = [
            booking for booking in bookings
            if booking["status"] != "returned" or not owns_record(booking)
        ]
        return jsonify({"cleared": previous_count - len(bookings)})


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

        response = jsonify({
            "equipment": equipment_status,
            "bookings": [visible_record(booking) for booking in bookings],
            "waiting_queue": {
                name: [visible_record(record) for record in queue]
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
        response.cache_control.no_store = True
        return response

if __name__ == "__main__":
    app.run(debug=True, threaded=True)
