# Rollout Demo: Healthy, Rolled-Back, and Blocked

Real output from `rollout-controller/demo_rollout.py`, run with
`.venv/bin/python3 rollout-controller/demo_rollout.py`. Each scenario
drives `run_staged_rollout()` with a hand-built telemetry snapshot per
wave and prints the exact event log the function returns -- this is not
a mocked-up example transcript, it's copy-pasted from an actual run.

## Scenario 1: Healthy rollout, all three waves promote

20-vehicle fleet, rolling from `1.2.0` to `1.3.0`, every wave reports
healthy telemetry and the security scan passed.

```
final status: complete

{"event": "wave_started", "wave_percentage": 0.05, "vehicle_count": 1, "target_version": "1.3.0", "image": "climate-control:1.3.0"}
{"event": "wave_promoted", "wave_percentage": 0.05}
{"event": "wave_started", "wave_percentage": 0.25, "vehicle_count": 5, "target_version": "1.3.0", "image": "climate-control:1.3.0"}
{"event": "wave_promoted", "wave_percentage": 0.25}
{"event": "wave_started", "wave_percentage": 1.0, "vehicle_count": 20, "target_version": "1.3.0", "image": "climate-control:1.3.0"}
{"event": "wave_promoted", "wave_percentage": 1.0}
{"event": "rollout_complete", "target_version": "1.3.0"}
```

Note every `wave_started` event carries `"image": "climate-control:1.3.0"`
-- the pinned tag from Mistake 9's fix, not `:latest`. All three waves
pull the exact same image.

## Scenario 2: Broken canary triggers an immediate rollback

Same fleet and target version, but the single vehicle in the 5% canary
wave reports a crash.

```
final status: rolled_back

{"event": "wave_started", "wave_percentage": 0.05, "vehicle_count": 1, "target_version": "1.3.0", "image": "climate-control:1.3.0"}
{"event": "rollback_triggered", "wave_percentage": 0.05, "reason": "crash_rate_exceeded_threshold"}
{"event": "rollback_applied", "target_version": "1.2.0"}
```

The rollout never reaches the 25% or 100% waves -- `should_rollback()`
fires on the canary's own telemetry (1 crash out of 1 updated vehicle is
a 100% crash rate, well above the 20% threshold) and `plan_rollback()`
correctly moves the fleet *backward* to `1.2.0` (this is exactly the
path Mistake 8 broke before it was fixed -- before that fix, this
scenario's `rollback_applied` step would never have fired at all).

## Scenario 3: A healthy canary still gets blocked by a failed security scan

Same fleet, canary telemetry is healthy, but `security_scan_passed=False`
(simulating a Trivy/Semgrep/pip-audit failure from the Week 3 pipeline).

```
final status: blocked

{"event": "wave_started", "wave_percentage": 0.05, "vehicle_count": 1, "target_version": "1.3.0", "image": "climate-control:1.3.0"}
{"event": "promotion_blocked", "wave_percentage": 0.05, "reason": "security_scan_failed"}
```

The canary itself looked fine -- no crash, no rollback -- but the
rollout still stops after wave 1 because `is_wave_promotion_allowed()`
requires both a healthy canary *and* a passed security scan (the fix for
Mistake 10; before that fix, this scenario would have produced
`wave_promoted` instead of `promotion_blocked`, silently ignoring the
failed scan).

## What isn't demonstrated here

This script exercises `run_staged_rollout()` directly with hand-built
telemetry -- it doesn't start `update-server`, post real telemetry from
real `vehicle-agent` processes, or push these events to the
`/events` endpoint over HTTP. That end-to-end wiring (rollout-controller
as a long-running process polling real fleet state and posting real
events) is a reasonable next step but wasn't built in this pass; the
`/events` endpoint exists and is tested (see `update-server/tests`), and
this script's event dicts are shaped to match what it expects, but
nothing here has actually POSTed to a running server.
