# Week 2 Learning Log

## Goal

Small throwaway experiments testing individual OTA ideas in isolation, before building the real update-server/vehicle-agent/rollout-controller in Month 2.

## What got built

- `experiments/toy_rollout_math.py` -- hit and fixed the int-truncation bug (see mistakes-log.md Mistake 2)
- `experiments/toy_vehicle_agent.py` -- polling loop against a hardcoded fake server response; version comparison and retry shape
- `experiments/toy_telemetry_threshold.py` -- hit and fixed the wrong-denominator bug (see mistakes-log.md Mistake 3)
- `experiments/toy_signature_check.py` -- fake-signature manifest flow, to understand the shape before cosign does real signing in Week 7
- `app/config_parser.py` + `app/tests/test_config_parser.py` -- strict config validation, 8 tests passing; this becomes the fuzzing target if that stretch goal happens later

## Reflection

Both real bugs this week (rollout math, error-rate denominator) are the kind that don't show up unless you actually run the numbers for a specific fleet size -- they'd pass a superficial code review. Writing them as tiny standalone scripts first, before they're buried inside the real rollout controller, made both bugs obvious within seconds of running the file. That's the actual argument for building throwaway experiments before the real system: cheap to run, cheap to be wrong in, cheap to fix.
