# Week 5 Learning Log

## Goal

The "mistake period" the plan calls out explicitly: build the real
rollout-controller module and let the hard staged-rollout problems
actually surface, rather than assuming Week 2's toy-experiment fixes
would just carry over cleanly.

## What got built

- `rollout-controller/controller.py` -- `wave_size()` and
  `should_rollback()` ported in as their already-fixed Week 2 versions
  (no new bug there on purpose -- those lessons are applied, not
  relearned), plus three genuinely new pieces: `plan_rollback()`,
  `build_manifest_for_wave()`, and `is_wave_promotion_allowed()`.
- 15 tests across `test_controller.py` (new) plus the existing
  `test_wave_math.py` / `test_error_threshold.py` (unchanged, still
  passing against the ported functions).

## Three new mistakes this week

1. **Rollback direction (Mistake 8).** `plan_rollback` reused the
   forward-only `needs_update` check, so a vehicle that needed to roll
   *back* to an older version was told no action was needed. The most
   dangerous bug in the project so far -- it doesn't misbehave, it turns
   the safety mechanism into a no-op.
2. **Mutable `:latest` tag (Mistake 9).** Rollout manifests always
   referenced `climate-control:latest` instead of the specific version
   being rolled out, which breaks the entire point of a canary wave:
   there's no guarantee the 5% wave and the 100% wave pull the same
   image.
3. **Security gate silently bypassed (Mistake 10).** The wave-promotion
   gate accepted a `security_scan_passed` flag and then never checked
   it -- a failed security scan and a passed one produced the identical
   "promotion allowed" result.

All three were caught by writing a test for the specific scenario each
bug gets wrong (an older rollback target, a specific version string, a
failed-scan input) and watching it fail against the real code before
writing the fix -- not by re-reading the code and spotting something
suspicious.

15/15 rollout-controller tests, 41 total project tests, all passing at
end of week.

## Reflection

The plan called this the "mistake period" going in, and in hindsight
that framing was right for a specific reason: every bug this week is in
logic that *looks* obviously correct on a first read (`if
needs_update(...)`, `return canary_healthy`, a manifest builder that
takes a version and returns... a manifest) and only breaks in a
scenario that isn't the first one anyone would think to test by hand.
Building the toy experiments first in Week 2 wasn't wasted effort even
though two of the five real bugs this project has hit so far were
already fixed by then -- it's specifically because the *reasoning*
practiced there (test the case that "obviously" works, then
deliberately test the case that doesn't) is what caught the three new
ones here.
