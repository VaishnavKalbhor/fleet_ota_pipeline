"""
rollout-controller: orchestrates a staged rollout (5% -> 25% -> 100%),
decides whether telemetry from the current wave says it's safe to
proceed, and can plan a rollback.

Two pieces of logic here are *ported*, not new: `wave_size()` and
`should_rollback()` are the exact fixed versions from the Week 2 toy
experiments (see docs/mistakes-log.md Mistakes 2 and 3) -- this is where
those lessons actually get used for real, so they're brought over
correct from the start rather than re-broken and re-fixed for show.
"""

CRASH_RATE_THRESHOLD = 0.20


def wave_size(fleet_size: int, percentage: float) -> int:
    """How many vehicles a given rollout percentage covers. Always at
    least 1 vehicle once percentage > 0 (Mistake 2, Week 2)."""
    calculated = int(fleet_size * percentage)
    if percentage > 0:
        return max(1, calculated)
    return calculated


def should_rollback(telemetry: list[dict]) -> bool:
    """True if the crash rate among *updated* vehicles exceeds the
    threshold. Denominator is updated vehicles, not the whole fleet
    (Mistake 3, Week 2)."""
    updated = [t for t in telemetry if t["status"] != "not_updated"]
    if not updated:
        return False
    crashes = sum(1 for t in updated if t["status"] == "crash")
    crash_rate = crashes / len(updated)
    return crash_rate > CRASH_RATE_THRESHOLD


def _parse_version(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def needs_update(current_version: str, target_version: str) -> bool:
    return _parse_version(current_version) < _parse_version(target_version)


def plan_rollback(current_version: str, previous_version: str) -> dict | None:
    """Decide what action (if any) is needed to roll a vehicle back to
    previous_version."""
    if needs_update(current_version, previous_version):
        return {"action": "apply", "target_version": previous_version}
    return None


def build_manifest_for_wave(target_version: str) -> dict:
    """Build the manifest a wave should be rolled out with."""
    return {
        "target_version": target_version,
        "image": "climate-control:latest",
    }
