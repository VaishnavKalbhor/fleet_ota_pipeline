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
    previous_version. Rollback is a deliberate move to a specific
    (usually older) version, so this must not reuse needs_update()'s
    forward-only "is target newer" check -- any mismatch between current
    and the rollback target means an action is needed, regardless of
    which direction that is."""
    if _parse_version(current_version) != _parse_version(previous_version):
        return {"action": "apply", "target_version": previous_version}
    return None


def build_manifest_for_wave(target_version: str) -> dict:
    """Build the manifest a wave should be rolled out with. The image tag
    is pinned to target_version, not "latest" -- see
    docs/mistakes-log.md Mistake 9 for why that distinction matters for
    a staged rollout specifically."""
    return {
        "target_version": target_version,
        "image": f"climate-control:{target_version}",
    }


def is_wave_promotion_allowed(canary_healthy: bool, security_scan_passed: bool) -> bool:
    """Decide whether it's safe to promote from the current wave to the
    next one (5% -> 25% -> 100%). Both gates must pass -- a healthy
    canary says nothing about whether the image that canary ran also
    cleared the security pipeline (Trivy/Semgrep/pip-audit from Week 3),
    and a green canary is not a substitute for a security gate that's
    supposed to run independently."""
    return canary_healthy and security_scan_passed


WAVE_PERCENTAGES = [0.05, 0.25, 1.0]


def run_staged_rollout(
    fleet_size: int,
    target_version: str,
    previous_version: str,
    security_scan_passed: bool,
    telemetry_by_wave: list[list[dict]],
) -> tuple[list[dict], str]:
    """
    Drive a rollout through the 5% / 25% / 100% waves, deciding after
    each wave whether to promote, roll back, or stop because the
    security gate blocked it.

    telemetry_by_wave[i] is the telemetry snapshot to evaluate for
    WAVE_PERCENTAGES[i]. Returns (events, final_status), where
    final_status is one of "complete", "rolled_back", "blocked".
    """
    events: list[dict] = []
    manifest = build_manifest_for_wave(target_version)

    for i, pct in enumerate(WAVE_PERCENTAGES):
        size = wave_size(fleet_size, pct)
        events.append(
            {
                "event": "wave_started",
                "wave_percentage": pct,
                "vehicle_count": size,
                "target_version": target_version,
                "image": manifest["image"],
            }
        )

        telemetry = telemetry_by_wave[i]
        if should_rollback(telemetry):
            events.append(
                {
                    "event": "rollback_triggered",
                    "wave_percentage": pct,
                    "reason": "crash_rate_exceeded_threshold",
                }
            )
            action = plan_rollback(target_version, previous_version)
            events.append(
                {
                    "event": "rollback_applied",
                    "target_version": action["target_version"] if action else previous_version,
                }
            )
            return events, "rolled_back"

        if not is_wave_promotion_allowed(canary_healthy=True, security_scan_passed=security_scan_passed):
            events.append(
                {
                    "event": "promotion_blocked",
                    "wave_percentage": pct,
                    "reason": "security_scan_failed",
                }
            )
            return events, "blocked"

        events.append({"event": "wave_promoted", "wave_percentage": pct})

    events.append({"event": "rollout_complete", "target_version": target_version})
    return events, "complete"
