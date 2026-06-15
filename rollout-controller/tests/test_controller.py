import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from controller import build_manifest_for_wave, plan_rollback, wave_size, should_rollback


def test_wave_size_still_correct_when_ported():
    assert wave_size(10, 0.05) == 1


def test_should_rollback_still_correct_when_ported():
    telemetry = [
        {"vehicle_id": "v1", "status": "crash"},
        {"vehicle_id": "v2", "status": "not_updated"},
    ]
    assert should_rollback(telemetry) is True


def test_rollback_from_broken_new_version_to_older_safe_version_is_triggered():
    # current_version is the broken NEW version; previous_version is the
    # older, previously-known-good version. Rolling back means moving
    # backward on purpose.
    action = plan_rollback(current_version="1.3.0", previous_version="1.2.0")
    assert action is not None
    assert action["target_version"] == "1.2.0"


def test_no_rollback_action_when_already_on_previous_version():
    action = plan_rollback(current_version="1.2.0", previous_version="1.2.0")
    assert action is None


def test_manifest_pins_an_immutable_tag_matching_target_version():
    manifest = build_manifest_for_wave("1.3.0")
    assert manifest["image"] == "climate-control:1.3.0"
