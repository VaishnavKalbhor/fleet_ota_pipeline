"""
update-server: the fleet's source of truth for "what version should
vehicles be running" and "what are vehicles actually reporting."

Deliberately simple in-memory state -- a real fleet backend would use a
database, but the point of this simulator is the OTA control-flow logic
(manifests, telemetry, rollout waves), not building a production data
layer.
"""

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException

app = FastAPI(title="update-server")

_manifest = {
    "target_version": "1.0.0",
    "image": "climate-control:1.0.0",
}

_fleet_state: dict[str, dict] = {}


def _reset_for_tests() -> None:
    """Test-only helper. Not exposed over HTTP."""
    global _manifest, _fleet_state
    _manifest = {"target_version": "1.0.0", "image": "climate-control:1.0.0"}
    _fleet_state = {}


@app.get("/health")
def health():
    return {"status": "healthy", "service": "update-server"}


@app.get("/manifest")
def get_manifest():
    return _manifest


@app.post("/manifest")
def set_manifest(new_manifest: dict):
    if "target_version" not in new_manifest:
        raise HTTPException(status_code=422, detail="target_version is required")
    _manifest["target_version"] = new_manifest["target_version"]
    if "image" in new_manifest:
        _manifest["image"] = new_manifest["image"]
    return _manifest


@app.post("/telemetry")
def report_telemetry(report: dict):
    for field in ("vehicle_id", "current_version", "status"):
        if field not in report:
            raise HTTPException(status_code=422, detail=f"{field} is required")

    vehicle_id = report["vehicle_id"]
    _fleet_state[vehicle_id] = {
        "current_version": report["current_version"],
        "status": report["status"],
        "last_seen": datetime.now(timezone.utc).isoformat(),
    }
    return {"received": True}


@app.get("/fleet/status")
def fleet_status():
    return {
        "target_version": _manifest["target_version"],
        "fleet_size": len(_fleet_state),
        "vehicles": _fleet_state,
    }
