import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent import run_poll_cycle


def test_repeated_poll_cycles_eventually_converge_on_disk(tmp_path):
    state_path = str(tmp_path / "vehicle-01-state.json")
    manifest = {"target_version": "1.2.0"}

    for _ in range(5):
        run_poll_cycle(state_path, "vehicle-01", manifest)

    # The on-disk record is what a real reboot/restart would read back.
    # If the cycle never persisted its result, this file either doesn't
    # exist, or still shows the pre-update version no matter how many
    # cycles ran.
    with open(state_path) as f:
        persisted = json.load(f)

    assert persisted["current_version"] == "1.2.0"


def test_poll_cycle_return_value_matches_what_gets_persisted(tmp_path):
    state_path = str(tmp_path / "vehicle-02-state.json")
    manifest = {"target_version": "1.2.0"}

    result = run_poll_cycle(state_path, "vehicle-02", manifest)
    assert result["current_version"] == "1.2.0"

    with open(state_path) as f:
        persisted = json.load(f)

    assert persisted["current_version"] == result["current_version"]
