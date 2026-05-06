"""
Toy experiment: given telemetry from vehicles, decide whether a rollout
should continue or roll back.

v1 divided crashes by the WHOLE fleet size. That's wrong during a canary
rollout: if only 1 of 10 vehicles has been updated and that one vehicle
crashes, the real failure rate is 100% (1 out of 1 UPDATED vehicles), not
10% (1 out of 10 TOTAL vehicles). Dividing by the whole fleet meant a
canary wave could crash-loop indefinitely without ever tripping rollback,
because the denominator kept the crash rate artificially low until most of
the fleet had already been updated -- exactly backwards from what a canary
is supposed to catch early. See docs/mistakes-log.md.
"""

CRASH_RATE_THRESHOLD = 0.20


def should_rollback(telemetry: list[dict]) -> bool:
    updated = [t for t in telemetry if t["status"] != "not_updated"]
    if not updated:
        return False
    crashes = sum(1 for t in updated if t["status"] == "crash")
    crash_rate = crashes / len(updated)
    return crash_rate > CRASH_RATE_THRESHOLD


if __name__ == "__main__":
    # Canary wave: only 1 of the 10-vehicle fleet has actually been updated.
    telemetry = [
        {"vehicle_id": "ecu-01", "version": "1.1.0", "status": "crash"},
        {"vehicle_id": "ecu-02", "version": "1.0.0", "status": "not_updated"},
        {"vehicle_id": "ecu-03", "version": "1.0.0", "status": "not_updated"},
        {"vehicle_id": "ecu-04", "version": "1.0.0", "status": "not_updated"},
        {"vehicle_id": "ecu-05", "version": "1.0.0", "status": "not_updated"},
        {"vehicle_id": "ecu-06", "version": "1.0.0", "status": "not_updated"},
        {"vehicle_id": "ecu-07", "version": "1.0.0", "status": "not_updated"},
        {"vehicle_id": "ecu-08", "version": "1.0.0", "status": "not_updated"},
        {"vehicle_id": "ecu-09", "version": "1.0.0", "status": "not_updated"},
        {"vehicle_id": "ecu-10", "version": "1.0.0", "status": "not_updated"},
    ]
    updated = [t for t in telemetry if t["status"] != "not_updated"]
    crashes = sum(1 for t in updated if t["status"] == "crash")
    print(f"crashes={crashes}, updated_vehicles={len(updated)}, crash_rate={crashes/len(updated):.0%}")
    print("should_rollback:", should_rollback(telemetry))
