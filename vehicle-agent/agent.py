"""
vehicle-agent: simulates one vehicle's OTA client. Polls update-server for
the current manifest, decides whether it needs to update, and reports
telemetry back.
"""


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
