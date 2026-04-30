import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "experiments"))
from toy_rollout_math import wave_size


def test_five_percent_of_ten_returns_at_least_one():
    assert wave_size(10, 0.05) == 1


def test_twenty_five_percent_of_ten_returns_at_least_two():
    assert wave_size(10, 0.25) >= 2


def test_hundred_percent_of_ten_returns_ten():
    assert wave_size(10, 1.0) == 10


def test_zero_percent_returns_zero():
    assert wave_size(10, 0.0) == 0
