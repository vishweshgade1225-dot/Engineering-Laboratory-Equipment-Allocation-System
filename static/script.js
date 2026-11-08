/* LABOS — LIVE CONTROL CENTER */

const bookingForm = document.getElementById("booking-form");
const bookingMessage = document.getElementById("booking-message");

function equipmentLabel(name) {
    return name.replaceAll("_", " ")
        .replace(/\b\w/g, letter => letter.toUpperCase());
}

// 1. Update dashboard statistics and equipment cards
async function updateDashboard() {
    try {
        const response = await fetch("/status");

        if (!response.ok) {
            throw new Error("Failed to load dashboard");
        }

        const data = await response.json();

        // Generate equipment cards using live Flask data
        renderEquipmentCards(data.equipment);
        renderSemaphoreMonitor(data.equipment);

        document.getElementById("total").textContent = data.total;
        document.getElementById("available").textContent = data.available;
        document.getElementById("in-use").textContent = data.in_use;
        document.getElementById("waiting").textContent = data.waiting;

        document.querySelectorAll(".equipment-card").forEach(card => {
            const name = card.dataset.equipment;
            const item = data.equipment[name];

            if (!item) return;

            card.querySelector(".equipment-count strong").textContent =
                `${item.available} / ${item.total}`;

            const percentage = item.total > 0
                ? (item.available / item.total) * 100
                : 0;

            card.querySelector(".progress-fill").style.width =
                `${percentage}%`;
        });


Object.entries(data.equipment).forEach(([name, item]) => {
    const semaphoreDisplay = document.getElementById(`sem-${name}`);

    if (semaphoreDisplay) {
        semaphoreDisplay.textContent =
            `${item.available} / ${item.total}`;
    }
});


        updateHistory(data.bookings);
        updateWaitingQueue(data.waiting_queue);
    } catch (error) {
        console.error("Dashboard update failed:", error);
    }
}

// 2. Display allocation history

function updateHistory(bookings) {
    const historyBody = document.getElementById("history-body");
    historyBody.replaceChildren();

    if (bookings.length === 0) {
        const row = historyBody.insertRow();
        const cell = row.insertCell();

        cell.colSpan = 9;
        cell.className = "empty-state";
        cell.textContent = "No allocation history yet.";
        return;
    }

    bookings.slice().reverse().forEach(booking => {
        const row = historyBody.insertRow();

        // Display complete student details
        row.insertCell().textContent = booking.student;
        row.insertCell().textContent = booking.enrollment || "—";
        row.insertCell().textContent = booking.department || "—";
        row.insertCell().textContent = booking.laboratory || "—";

        // Display readable equipment name
        row.insertCell().textContent =
            booking.equipment.split("|").pop();

        row.insertCell().textContent = booking.purpose || "—";
        row.insertCell().textContent = booking.time;
        row.insertCell().textContent = booking.status;

        // Return equipment button
        const actionCell = row.insertCell();

        if (booking.status === "allocated") {
            const button = document.createElement("button");
            button.className = "return-btn";
            button.textContent = "Return Equipment";

            button.addEventListener("click", () => {
                returnEquipment(booking.id);
            });

            actionCell.appendChild(button);
        } else {
            actionCell.textContent = "—";
        }
    });
}

// 3. Submit equipment booking
bookingForm.addEventListener("submit", async event => {
    event.preventDefault();

    const student = document.getElementById("student").value.trim();
    const enrollment = document.getElementById("enrollment").value.trim();
    const department = document.getElementById("department").value;
    const laboratory = document.getElementById("laboratory").value;
    const equipment = document.getElementById("equipment").value;
    const purpose = document.getElementById("purpose").value;

    if (
        !student ||
        !enrollment ||
        !department ||
        !laboratory ||
        !equipment ||
        !purpose
    ) {
        bookingMessage.textContent = "Please fill in all fields.";
        bookingMessage.style.color = "#fb7185";
        return;
    }

    try {
        const response = await fetch("/book", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                student,
                enrollment,
                department,
                laboratory,
                equipment,
                purpose
            })

        });

        const result = await response.json();

        bookingMessage.textContent =
            result.message || result.error || "Request failed.";

        bookingMessage.style.color =
            result.status === "waiting" ? "#fbbf24" : "#2dd4bf";


        if (response.ok) {
            bookingForm.reset();

            // Reset dependent dropdowns
            laboratorySelect.innerHTML =
                '<option value="">Select Laboratory</option>';

            equipmentSelect.innerHTML =
                '<option value="">Select Equipment</option>';
        }


        await updateDashboard();

    } catch (error) {
        bookingMessage.textContent = "Server connection failed.";
        bookingMessage.style.color = "#fb7185";
    }
});

// 4. Return equipment
async function returnEquipment(bookingId) {
    try {
        const response = await fetch("/return", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ booking_id: bookingId })
        });

        const result = await response.json();

        if (!response.ok) {
            alert(result.error || "Return failed.");
            return;
        }

        bookingMessage.textContent = result.message;
        bookingMessage.style.color = "#2dd4bf";

        await updateDashboard();

    } catch (error) {
        alert("Unable to return equipment.");
    }
}

// 5. Automatically refresh every 2 seconds
updateDashboard();
setInterval(updateDashboard, 2000);

function updateWaitingQueue(waitingQueue) {
    const queueList = document.getElementById("queue-list");

    queueList.replaceChildren();

    if (!waitingQueue) {
        queueList.textContent = "Waiting queue data unavailable.";
        return;
    }

    let totalWaiting = 0;

    Object.entries(waitingQueue).forEach(([equipment, students]) => {
        students.forEach((student, index) => {
            totalWaiting++;

            const row = document.createElement("div");
            row.className = "history-row";

            const details = document.createElement("span");
            details.textContent =
                `${student.student} (${student.enrollment}) | ` +
                `${equipment.split("|").pop()} | ` +
                `Position ${index + 1}`;

            const status = document.createElement("span");
            status.textContent = "WAITING";
            status.style.color = "#fbbf24";

            row.appendChild(details);
            row.appendChild(status);
            queueList.appendChild(row);
        });
    });

    document.getElementById("queue-count").textContent = totalWaiting;

    if (totalWaiting === 0) {
        queueList.textContent = "No students currently waiting.";
    }
}

/* =====================================
   DEPARTMENT-WISE EQUIPMENT SELECTION
===================================== */

const catalogElement = document.getElementById(
    "equipment-catalog-data"
);

const equipmentCatalog = JSON.parse(
    catalogElement.textContent
);

const departmentSelect = document.getElementById("department");
const laboratorySelect = document.getElementById("laboratory");
const equipmentSelect = document.getElementById("equipment");

function addDropdownOption(select, value, label) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    select.appendChild(option);
}

// When department changes
departmentSelect.addEventListener("change", function () {

    laboratorySelect.innerHTML =
        '<option value="">Select Laboratory</option>';

    equipmentSelect.innerHTML =
        '<option value="">Select Equipment</option>';

    const department = departmentSelect.value;

    if (!department || !equipmentCatalog[department]) {
        return;
    }

    const laboratories = equipmentCatalog[department];

    Object.keys(laboratories).forEach(function (laboratory) {
        addDropdownOption(
            laboratorySelect,
            laboratory,
            laboratory
        );
    });

});

// When laboratory changes
laboratorySelect.addEventListener("change", function () {

    equipmentSelect.innerHTML =
        '<option value="">Select Equipment</option>';

    const department = departmentSelect.value;
    const laboratory = laboratorySelect.value;

    if (!department || !laboratory) {
        return;
    }

    const items = equipmentCatalog[department][laboratory];

    Object.entries(items).forEach(function ([name, quantity]) {

        const equipmentId =
            `${department}|${laboratory}|${name}`;

        addDropdownOption(
            equipmentSelect,
            equipmentId,
            `${name} (${quantity} units)`
        );

    });

});

function renderEquipmentCards(equipmentData) {
    const grid = document.getElementById("equipment-grid");

    if (!grid) return;


    grid.replaceChildren();

    // Get selected department
    const departmentFilter = document.getElementById(
        "equipment-department-filter"
    );

    const selectedDepartment = departmentFilter
        ? departmentFilter.value
        : "all";

    const searchInput = document.getElementById(
        "equipment-search-input"
    );

    const searchText = searchInput
        ? searchInput.value.trim().toLowerCase()
        : "";

    // Filter equipment by department
    Object.entries(equipmentData)

        .filter(([equipmentId]) => {
            const [department, laboratory, equipmentName] =
                equipmentId.split("|");

            const matchesDepartment =
                selectedDepartment === "all" ||
                department === selectedDepartment;

            const matchesSearch =
                equipmentName.toLowerCase().includes(searchText) ||
                laboratory.toLowerCase().includes(searchText) ||
                department.toLowerCase().includes(searchText);

            return matchesDepartment && matchesSearch;
        })

        .forEach(([equipmentId, item]) => {

        const [department, laboratory, equipmentName] =
            equipmentId.split("|");

        const card = document.createElement("div");
        card.className = "equipment-card";
        card.dataset.equipment = equipmentId;

        const icon = document.createElement("div");
        icon.className = "equipment-icon";
        icon.textContent = "⚙";

        const title = document.createElement("h3");
        title.textContent = equipmentName;

        const description = document.createElement("p");
        description.textContent =
            `${department} | ${laboratory}`;

        const count = document.createElement("div");
        count.className = "equipment-count";

        const strong = document.createElement("strong");
        strong.textContent =
            `${item.available} / ${item.total}`;

        const label = document.createElement("span");
        label.textContent = "Available";

        count.appendChild(strong);
        count.appendChild(label);

        const track = document.createElement("div");
        track.className = "progress-track";

        const fill = document.createElement("div");
        fill.className = "progress-fill";
        fill.style.width =
            `${item.total > 0 ? (item.available / item.total) * 100 : 0}%`;

        track.appendChild(fill);

        card.appendChild(icon);
        card.appendChild(title);
        card.appendChild(description);
        card.appendChild(count);
        card.appendChild(track);

        grid.appendChild(card);
    });

    if (grid.children.length === 0) {
        const message = document.createElement("p");
        message.className = "empty-state";
        message.textContent =
            "No equipment found. Try another search or department.";
        grid.appendChild(message);
    }
}

function renderSemaphoreMonitor(equipmentData) {
    const container = document.getElementById("semaphore-list");

    if (!container) return;

    container.replaceChildren();

    Object.entries(equipmentData).forEach(([equipmentId, item]) => {
        const [department, laboratory, equipmentName] =
            equipmentId.split("|");

        const row = document.createElement("div");
        row.className = "semaphore-row";

        const label = document.createElement("span");
        label.textContent = `${department} | ${equipmentName}`;
        label.title = laboratory;

        const count = document.createElement("strong");
        count.textContent = `${item.available} / ${item.total}`;

        row.appendChild(label);
        row.appendChild(count);

        container.appendChild(row);
    });
}
