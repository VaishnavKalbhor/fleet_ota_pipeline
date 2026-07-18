# Week 8 Learning Log

## Goal

Close the project out: monitoring config validated against the app's
real `/metrics` output, an explicit (non-compliance) standards mapping,
a demo script, a final README, and a Makefile so the whole thing is
runnable with a couple of commands.

## What got built

- `telemetry/prometheus.yml` + `telemetry/grafana-dashboard.json` --
  built against metric names confirmed by actually running the app and
  reading its real `/metrics` output, not just the library's documented
  defaults. Caught one detail worth documenting along the way: status
  codes come back grouped (`"5xx"`, not `"500"`), which the dashboard's
  regex query happens to still match correctly, but wouldn't have if it
  had been written to match an exact numeric code.
- `docs/standards-mapping.md` -- maps specific design decisions in this
  project (default-deny network policies, staged rollout, rollback,
  dependency scanning) to concepts from ISO/SAE 21434, UNECE R155, and
  UNECE R156, with an explicit closing section on what's NOT claimed
  (no TARA, no audit, no Uptane-style multi-role signing, no live
  cluster validation).
- `docs/demo-script.md` -- a 10-15 minute walkthrough built entirely
  around things that are actually runnable without Docker/Kubernetes/a
  cloud account.
- `README.md` -- full rewrite: component table, getting-started
  commands, the bugs/lessons table pulled from all 11 mistakes-log
  entries, and an explicit "verified vs. reviewed" section splitting
  what was actually run in this dev environment from what was written
  and hand-checked but never executed.
- `Makefile` -- `install`, `test`, `demo`, `lint-yaml`, `clean`. Ran
  each target for real before committing (`make test` -> 54 passed,
  `make lint-yaml` -> every plain YAML file in the repo parses, `make
  demo` -> the same three-scenario output as `docs/rollout-demo.md`).

54/54 tests passing, all Makefile targets confirmed working, at the
close of the project.

## Reflection

The most useful thing built this week wasn't a new feature -- it was
the README's "verified vs. reviewed" section, because writing it forced
a real accounting of exactly which parts of this eight-week project
were actually executed and observed versus written correctly and
reviewed carefully but never run. Those are both legitimate things to
show in a portfolio project, but conflating them is exactly the kind of
overclaiming that a technical reviewer would catch immediately -- and
the mistakes log itself is proof of why that distinction matters: every
bug that was "caught by reading the code carefully" (Mistakes 7 and 11)
is still just reasoning, however careful, right up until something
actually runs it. Keeping that line visible throughout the project,
rather than only admitting it once at the end, was the point.
