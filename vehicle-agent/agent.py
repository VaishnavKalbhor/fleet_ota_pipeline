"""
vehicle-agent: simulates one vehicle's OTA client. Polls update-server for
the current manifest, decides whether it needs to update, and reports
telemetry back.
"""

import json
import os


def _parse_version(version: str) -> tuple[int, ...]:
    """Parse a dotted version string into a tuple of ints for numeric
    comparison. "1.10.0" -> (1, 10, 0)."""
    return tuple(int(part) for part in version.split("."))


def needs_update(current_version: str, target_version: str) -> bool:
    """True if the vehicle should update to reach target_version."""
    return _parse_version(current_version) < _parse_version(target_version)


class VehicleAgent:
    def __init__(self, vehicle_id: str, current_version: str = "1.0.0"):
        self.vehicle_id = vehicle_id
        self.current_version = current_version
        self.status = "healthy"

    def poll_and_maybe_apply(self, manifest: dict) -> dict:
        target = manifest["target_version"]
        if needs_update(self.current_version, target):
            self._apply_update(target)
        return self.telemetry_report()

    def _apply_update(self, target_version: str) -> None:
        self.current_version = target_version
        self.status = "healthy"

    def telemetry_report(self) -> dict:
        return {
            "vehicle_id": self.vehicle_id,
            "current_version": self.current_version,
            "status": self.status,
        }


def load_state(state_path: str, vehicle_id: str) -> dict:
    """Load this vehicle's persisted state (its view of its own current
    version), or a fresh default if it's never run before."""
    if not os.path.exists(state_path):
        return {"vehicle_id": vehicle_id, "current_version": "1.0.0", "status": "healthy"}
    with open(state_path) as f:
        return json.load(f)


def run_poll_cycle(state_path: str, vehicle_id: str, manifest: dict) -> dict:
    """One poll-apply-report cycle for a vehicle backed by an on-disk
    state file (this is what actually runs on a schedule/loop; the
    VehicleAgent class above is the in-memory building block it's built
    from)."""
    state = load_state(state_path, vehicle_id)
    if needs_update(state["current_version"], manifest["target_version"]):
        state["current_version"] = manifest["target_version"]
        state["status"] = "healthy"
    return state
