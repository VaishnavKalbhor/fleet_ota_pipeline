# Week 6 Learning Log

## Goal

Turn last week's individual rollout-controller functions into an actual
staged-rollout sequence, add a fleet-visible event log, and produce a
real demo of what a healthy rollout, a rollback, and a security-blocked
rollout each look like.

## What got built

- `rollout-controller/controller.py::run_staged_rollout()` -- drives
  the 5% / 25% / 100% waves in order, calling `should_rollback()` after
  each wave's telemetry and `is_wave_promotion_allowed()` before
  advancing to the next one, stopping early on either a rollback or a
  blocked promotion. Returns a full event list plus a final status
  (`complete` / `rolled_back` / `blocked`).
- `update-server/main.py` -- `/events` (POST to record, GET to list),
  so rollout actions have a fleet-visible audit trail the same way
  telemetry does. 3 new tests.
- `rollout-controller/demo_rollout.py` + `docs/rollout-demo.md` -- ran
  all three scenarios for real and captured the actual event-log output
  rather than writing up what they'd probably look like.

18 rollout-controller tests + 11 update-server tests passing (54 total
project tests).

## No new mistake this week, on purpose

Every other week's log in this project documents at least one bug that
was hit and fixed. This week doesn't, and that's worth being honest
about rather than manufacturing one: `run_staged_rollout()` is
mostly composition of functions that were already individually tested
last week (`wave_size`, `should_rollback`, `plan_rollback`,
`is_wave_promotion_allowed`, `build_manifest_for_wave`) plus sequencing
logic simple enough (a loop over three fixed percentages, early-return
on the two stop conditions) that the three scenario tests passed on the
first run. Padding this log with an invented bug just to keep a streak
going would go against the whole point of the mistakes-log -- it's
supposed to be a real record, not a quota.

## Reflection

The three-scenario demo turned out to be a good sanity check on last
week's fixes, even without a new bug: Scenario 2's `rollback_applied`
event and Scenario 3's `promotion_blocked` event are both outcomes that
Mistakes 8 and 10 would have produced *silently wrong* results for
before they were fixed (a rollback that never applies, a block that
never blocks). Running the actual scenario and reading the actual event
log is a more convincing verification than the unit tests alone --
unit tests check a function's return value in isolation, but the
demo confirms those return values compose into an event sequence that
tells the right story end to end.
