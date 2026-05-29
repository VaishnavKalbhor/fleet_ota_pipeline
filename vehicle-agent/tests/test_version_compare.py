import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent import needs_update


def test_needs_update_when_target_is_newer_simple_case():
    assert needs_update("1.0.0", "1.2.0") is True


def test_no_update_when_already_current():
    assert needs_update("1.2.0", "1.2.0") is False


def test_double_digit_minor_version_is_compared_numerically_not_lexically():
    # 1.10.0 is a NEWER version than 1.2.0 (minor 10 > minor 2), so a vehicle
    # already on 1.10.0 should NOT be told it needs to "update" to 1.2.0.
    assert needs_update("1.10.0", "1.2.0") is False
