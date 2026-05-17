import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from config_parser import parse_config, ConfigError, load_yaml_overrides


def test_valid_config_is_accepted():
    result = parse_config({"target_temperature": 21, "fan_speed": 2, "mode": "auto"})
    assert result["target_temperature"] == 21


def test_missing_temperature_is_rejected():
    with pytest.raises(ConfigError):
        parse_config({"fan_speed": 2, "mode": "auto"})


def test_temperature_too_high_is_rejected():
    with pytest.raises(ConfigError):
        parse_config({"target_temperature": 99, "fan_speed": 2, "mode": "auto"})


def test_temperature_wrong_type_is_rejected():
    with pytest.raises(ConfigError):
        parse_config({"target_temperature": "warm", "fan_speed": 2, "mode": "auto"})


def test_empty_config_is_rejected():
    with pytest.raises(ConfigError):
        parse_config({})


def test_non_dict_config_is_rejected():
    with pytest.raises(ConfigError):
        parse_config("not-a-dict")


def test_defaults_apply_when_optional_fields_missing():
    result = parse_config({"target_temperature": 20})
    assert result["fan_speed"] == 1
    assert result["mode"] == "auto"


def test_invalid_mode_is_rejected():
    with pytest.raises(ConfigError):
        parse_config({"target_temperature": 20, "mode": "turbo"})


def test_load_yaml_overrides_reads_and_validates_example_file():
    example_path = str(Path(__file__).resolve().parents[1] / "examples" / "fleet-config.example.yaml")
    result = load_yaml_overrides(example_path)
    assert result["target_temperature"] == 19
    assert result["fan_speed"] == 3
    assert result["mode"] == "cool"


def test_load_yaml_overrides_rejects_invalid_override(tmp_path):
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("target_temperature: 999\n")
    with pytest.raises(ConfigError):
        load_yaml_overrides(str(bad_file))
