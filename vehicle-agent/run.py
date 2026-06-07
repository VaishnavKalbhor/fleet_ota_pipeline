"""
Entry point for a single simulated vehicle. Reads its identity and the
update-server URL from the environment (so docker-compose can run several
of these with different VEHICLE_ID values against the same image), then
polls in a loop.

Not covered by pytest -- this is the thin "glue" layer (env vars, sleep
loop, network calls); the logic it calls (agent.py) is what's unit
tested.
"""

import os
import time

import httpx

from agent import run_poll_cycle

VEHICLE_ID = os.environ.get("VEHICLE_ID", "vehicle-unknown")
UPDATE_SERVER_URL = os.environ.get("UPDATE_SERVER_URL", "http://localhost:8000")
STATE_PATH = os.environ.get("STATE_PATH", f"/data/{VEHICLE_ID}-state.json")
POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "10"))


def poll_once() -> dict:
    resp = httpx.get(f"{UPDATE_SERVER_URL}/manifest", timeout=5.0)
    resp.raise_for_status()
    manifest = resp.json()

    state = run_poll_cycle(STATE_PATH, VEHICLE_ID, manifest)

    httpx.post(
        f"{UPDATE_SERVER_URL}/telemetry",
        json={
            "vehicle_id": VEHICLE_ID,
            "current_version": state["current_version"],
            "status": state["status"],
        },
        timeout=5.0,
    )
    return state


def main() -> None:
    print(f"[{VEHICLE_ID}] starting, polling {UPDATE_SERVER_URL} every {POLL_INTERVAL_SECONDS}s")
    while True:
        try:
            state = poll_once()
            print(f"[{VEHICLE_ID}] version={state['current_version']} status={state['status']}")
        except httpx.HTTPError as exc:
            print(f"[{VEHICLE_ID}] poll failed: {exc}")
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
