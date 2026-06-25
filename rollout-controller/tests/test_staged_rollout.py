import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from controller import run_staged_rollout


def _healthy_telemetry(updated_count: int) -> list[dict]:
    return [{"vehicle_id": f"v{i}", "status": "healthy"} for i in range(updated_count)]


def test_healthy_rollout_completes_all_three_waves():
    telemetry_by_wave = [
        _healthy_telemetry(1),   # 5% of 20
        _healthy_telemetry(5),   # 25% of 20
        _healthy_telemetry(20),  # 100% of 20
    ]
    events, status = run_staged_rollout(
        fleet_size=20,
        target_version="1.3.0",
        previous_version="1.2.0",
        security_scan_passed=True,
        telemetry_by_wave=telemetry_by_wave,
    )
    assert status == "complete"
    event_names = [e["event"] for e in events]
    assert event_names.count("wave_started") == 3
    assert event_names.count("wave_promoted") == 3
    assert event_names[-1] == "rollout_complete"
    # Every wave_started event should reference the pinned version tag,
    # not "latest" (Mistake 9 regression check at the orchestration level).
    assert all(e["image"] == "climate-control:1.3.0" for e in events if e["event"] == "wave_started")


def test_broken_canary_triggers_rollback_and_stops_before_wider_rollout():
    canary_telemetry = [
        {"vehicle_id": "v0", "status": "crash"},
    ]
    events, status = run_staged_rollout(
        fleet_size=20,
        target_version="1.3.0",
        previous_version="1.2.0",
        security_scan_passed=True,
        telemetry_by_wave=[canary_telemetry],  # rollback happens before wave 2 is ever reached
    )
    assert status == "rolled_back"
    event_names = [e["event"] for e in events]
    assert event_names == ["wave_started", "rollback_triggered", "rollback_applied"]
    rollback_event = events[-1]
    assert rollback_event["target_version"] == "1.2.0"


def test_failed_security_scan_blocks_promotion_after_healthy_canary():
    events, status = run_staged_rollout(
        fleet_size=20,
        target_version="1.3.0",
        previous_version="1.2.0",
        security_scan_passed=False,
        telemetry_by_wave=[_healthy_telemetry(1)],
    )
    assert status == "blocked"
    event_names = [e["event"] for e in events]
    assert event_names == ["wave_started", "promotion_blocked"]
