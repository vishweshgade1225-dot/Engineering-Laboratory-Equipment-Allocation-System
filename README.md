# LabOS · Engineering Lab Equipment Allocation

LabOS is a Flask dashboard for booking and returning engineering lab equipment. Students select a department, laboratory, and item, then enter their enrollment details and purpose. If every unit of an item is in use, LabOS adds the student to a first-in, first-out queue and assigns the next returned unit to the student at the front of that queue.

## Run locally

From the project directory, use Python 3.12 to create a virtual environment, install Flask, and start the development server.

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

### macOS or Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Open the [LabOS dashboard](http://127.0.0.1:5000). The server runs in Flask debug mode for local development. Bookings and waiting queues live in memory and reset whenever the server process restarts.

## HTTP endpoints

| Method and path | Purpose |
| --- | --- |
| `GET /` | Open the dashboard |
| `GET /status` | Read inventory counts, bookings, and waiting queues |
| `POST /book` | Submit JSON with `student`, `enrollment`, `department`, `laboratory`, `equipment`, and `purpose` |
| `POST /return` | Return equipment by sending JSON with its `booking_id` |

For `POST /book`, use the full `department|laboratory|equipment` ID and choose `Practical`, `Experiment`, `Project`, or `Research` as the purpose.

## Project layout

| Path | Purpose |
| --- | --- |
| `app.py` | Serves the dashboard and exposes the booking, return, and status endpoints |
| `equipment.py` | Manages inventory capacity, bookings, and waiting queues using bounded semaphores and a shared lock |
| `equipment_catalog.py` | Defines equipment quantities by department and laboratory |
| `templates/index.html` | Dashboard markup |
| `static/script.js` and `static/style.css` | Dashboard behavior and styling |

## Check the booking flow

Submit a booking from the dashboard and confirm that the in-use count increases. Fill an item's capacity, submit another request, then return one of the active bookings to verify that the first waiting student receives it.

Run `python test_concurrency.py` to check capacity under simultaneous requests, independent equipment semaphores, and first-in, first-out reassignment on return.

## Deploy a public demo

In the [Render dashboard](https://dashboard.render.com/), create a Blueprint from this repository. [`render.yaml`](render.yaml) installs the requirements, starts Waitress on Render's assigned port, and checks the dashboard at `/`.

The deployment uses one server process with multiple threads so every request sees the same inventory and queue. No application secrets are required. Demo mode uses fictional names and discards submitted enrollment numbers. All visitors share the same bookings, and the state resets whenever the server restarts, redeploys, or spins down.
