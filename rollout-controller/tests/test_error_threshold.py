import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "experiments"))
from toy_telemetry_threshold import should_rollback


def test_canary_crash_triggers_rollback_even_with_small_fleet_fraction():
    # 1 of 10 vehicles updated, and that one crashed -- 100% failure among
    # updated vehicles should trigger rollback even though it's only 10%
    # of the total fleet.
    telemetry = [{"vehicle_id": "ecu-01", "version": "1.1.0", "status": "crash"}] + [
        {"vehicle_id": f"ecu-{i:02d}", "version": "1.0.0", "status": "not_updated"}
        for i in range(2, 11)
    ]
    assert should_rollback(telemetry) is True


def test_healthy_canary_does_not_rollback():
    telemetry = [{"vehicle_id": "ecu-01", "version": "1.1.0", "status": "healthy"}] + [
        {"vehicle_id": f"ecu-{i:02d}", "version": "1.0.0", "status": "not_updated"}
        for i in range(2, 11)
    ]
    assert should_rollback(telemetry) is False


def test_no_vehicles_updated_yet_does_not_rollback():
    telemetry = [
        {"vehicle_id": f"ecu-{i:02d}", "version": "1.0.0", "status": "not_updated"}
        for i in range(1, 11)
    ]
    assert should_rollback(telemetry) is False


def test_error_rate_above_threshold_across_larger_wave():
    # 25% wave = ~3 vehicles updated; 1 crash out of 3 is ~33%, above the 20% threshold.
    telemetry = [
        {"vehicle_id": "ecu-01", "version": "1.1.0", "status": "crash"},
        {"vehicle_id": "ecu-02", "version": "1.1.0", "status": "healthy"},
        {"vehicle_id": "ecu-03", "version": "1.1.0", "status": "healthy"},
    ] + [
        {"vehicle_id": f"ecu-{i:02d}", "version": "1.0.0", "status": "not_updated"}
        for i in range(4, 11)
    ]
    assert should_rollback(telemetry) is True
