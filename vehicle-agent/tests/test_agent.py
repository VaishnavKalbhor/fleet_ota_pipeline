import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent import VehicleAgent


def test_agent_applies_update_when_behind():
    agent = VehicleAgent("vehicle-01", current_version="1.0.0")
    report = agent.poll_and_maybe_apply({"target_version": "1.2.0"})
    assert report["current_version"] == "1.2.0"
    assert report["status"] == "healthy"


def test_agent_does_not_apply_when_already_current():
    agent = VehicleAgent("vehicle-01", current_version="1.2.0")
    report = agent.poll_and_maybe_apply({"target_version": "1.2.0"})
    assert report["current_version"] == "1.2.0"


def test_agent_does_not_downgrade_from_newer_double_digit_version():
    agent = VehicleAgent("vehicle-01", current_version="1.10.0")
    report = agent.poll_and_maybe_apply({"target_version": "1.2.0"})
    assert report["current_version"] == "1.10.0"


def test_telemetry_report_includes_vehicle_id():
    agent = VehicleAgent("vehicle-07")
    report = agent.telemetry_report()
    assert report["vehicle_id"] == "vehicle-07"
