"""
Tiny climate-config parser/validator. Deliberately strict and small -- this
becomes the fuzzing target later (mentioned in the plan as a stretch goal;
not built in this pass, but this is the module it would point at).
"""


class ConfigError(ValueError):
    pass


def parse_config(raw: dict) -> dict:
    if not isinstance(raw, dict):
        raise ConfigError("config must be a JSON object")

    if "target_temperature" not in raw:
        raise ConfigError("missing required field: target_temperature")

    temp = raw["target_temperature"]
    if not isinstance(temp, (int, float)) or isinstance(temp, bool):
        raise ConfigError("target_temperature must be a number")
    if not (10 <= temp <= 32):
        raise ConfigError("target_temperature must be between 10 and 32")

    fan_speed = raw.get("fan_speed", 1)
    if not isinstance(fan_speed, int) or isinstance(fan_speed, bool):
        raise ConfigError("fan_speed must be an integer")
    if not (0 <= fan_speed <= 5):
        raise ConfigError("fan_speed must be between 0 and 5")

    mode = raw.get("mode", "auto")
    if mode not in ("auto", "cool", "heat", "off"):
        raise ConfigError("mode must be one of auto, cool, heat, off")

    return {
        "target_temperature": temp,
        "fan_speed": fan_speed,
        "mode": mode,
    }
