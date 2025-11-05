# app.py
from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest

from .run import run  # your run() from the module you showed

app = Flask(__name__)

# Friendly labels + simple state (latest counts per phase)
PHASE_LABELS = {
    "personas": "Generating personas",
    "agents": "Running agents",
    "surveys": "Filling surveys",
    "all": "All tasks",
}
progress_state = {
    "last_phase": None,
    "counts": {
        "personas": {"current": 0, "total": 0},
        "agents": {"current": 0, "total": 0},
        "surveys": {"current": 0, "total": 0},
    },
}


def _format_progress() -> dict:
    phase = progress_state["last_phase"]
    if not phase:
        return {"status": "idle", "message": "No run started yet."}

    c = progress_state["counts"].get(phase, {"current": 0, "total": 0})
    label = PHASE_LABELS.get(phase, phase.title())
    return {
        "phase": phase,
        "label": label,
        "current": c.get("current", 0),
        "total": c.get("total", 0),
        "message": f"{label}: {c.get('current', 0)}/{c.get('total', 0)}",
    }


def _print_compact(phase: str):
    label = PHASE_LABELS.get(phase, phase.title())
    c = progress_state["counts"].get(phase, {"current": 0, "total": 0})
    current, total = c.get("current", 0), c.get("total", 0)
    print(f"[PROGRESS] {label}: {current}/{total}", flush=True)


def log_progress(evt: dict):
    # evt looks like: {"phase":"agents","status":"progress","current":k,"total":n}
    phase = evt.get("phase")
    status = evt.get("status")

    if phase in progress_state["counts"]:
        # update totals/currents if present
        if "total" in evt:
            progress_state["counts"][phase]["total"] = evt["total"]
        if status == "start":
            # initialize current to 0 at start
            progress_state["counts"][phase]["current"] = 0
        if "current" in evt:
            progress_state["counts"][phase]["current"] = evt["current"]

        progress_state["last_phase"] = phase
        _print_compact(phase)

    elif phase == "all" and status == "done":
        print("[PROGRESS] ✅ Done.", flush=True)
    else:
        # unknown/misc event — still show something if helpful
        print(f"[PROGRESS] {evt}", flush=True)


@app.post("/run")
def run_endpoint():
    # Parse JSON body
    payload = request.get_json(silent=True)
    if payload is None:
        raise BadRequest("Expected application/json body")

    # Minimal required fields (raise 400 if missing)
    required = [
        "total_personas",
        "demographics",
        "general_intent",
        "start_url",
        "max_steps",
        "questionnaire",
    ]
    missing = [k for k in required if k not in payload]
    if missing:
        raise BadRequest(f"Missing required fields: {', '.join(missing)}")

    try:
        # Optional flags with defaults
        headless = bool(payload.get("headless", True))

        # Call your pipeline
        result = run(
            total_personas=int(payload["total_personas"]),
            demographics=payload["demographics"],
            general_intent=payload["general_intent"],
            start_url=payload["start_url"],
            max_steps=int(payload["max_steps"]),
            concurrency=int(payload.get("concurrency", 4)),
            example_persona=payload.get("example_persona", None),
            questionnaire=payload["questionnaire"],
            # optional
            headless=headless,
            on_progress=log_progress,
        )
        return jsonify(result), 200

    except BadRequest:
        # re-raise validation errors as-is
        raise
    except Exception as e:
        # Minimal error surface; expand logging as needed
        return jsonify({"status": "error", "error": str(e)}), 500


@app.get("/progress")
def progress_endpoint():
    return jsonify(_format_progress()), 200


if __name__ == "__main__":
    # Minimal dev server
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=False, threaded=True)
