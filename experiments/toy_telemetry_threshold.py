"""
Toy experiment: given telemetry from vehicles, decide whether a rollout
should continue or roll back.
"""

CRASH_RATE_THRESHOLD = 0.20


def should_rollback(telemetry: list[dict]) -> bool:
    crashes = sum(1 for t in telemetry if t["status"] == "crash")
    total_fleet = len(telemetry)
    crash_rate = crashes / total_fleet if total_fleet else 0.0
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
    crashes = sum(1 for t in telemetry if t["status"] == "crash")
    print(f"crashes={crashes}, fleet_size={len(telemetry)}, crash_rate={crashes/len(telemetry):.0%}")
    print("should_rollback:", should_rollback(telemetry))
