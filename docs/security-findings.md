# Security Findings

Findings from actually running the scanning tools this project wires into
CI, not a hypothetical "if we ran a scanner it would probably find
something" list. Where a tool can run in this dev environment, the output
below is real (copy-pasted from a real run) with the date it was run and
what was fixed afterward. Where a tool needs GitHub Actions or Docker to
run (Semgrep via `returntocorp/semgrep-action`, Trivy against a built
image), it's marked as "runbook only, not yet executed" -- written
correctly by hand-review, but not something I've watched actually run in
this repo.

## Finding 1: PyYAML 5.3.1 pinned in app/requirements.txt (fixed)

**Tool:** `pip-audit -r app/requirements.txt` (run locally, matches the
`dependency-scan` job added in `security.yml`)
**Status:** Fixed
**Date found / fixed:** same session, Week 3

Real output from `pip-audit -r app/requirements.txt` against the
requirements file as it existed right after the fleet-config YAML feature
was added:

```
Found 12 known vulnerabilities in 3 packages
Name      Version ID              Fix Versions
--------- ------- --------------- ------------
pytest    8.3.3   PYSEC-2026-1845 9.0.3
pyyaml    5.3.1   PYSEC-2021-142  5.4
pyyaml    5.3.1   PYSEC-2021-142  5.4
starlette 0.38.6  PYSEC-2026-161  1.0.1
starlette 0.38.6  PYSEC-2026-161  1.0.1
starlette 0.38.6  PYSEC-2026-248  1.3.0
starlette 0.38.6  PYSEC-2026-249  1.3.1
starlette 0.38.6  PYSEC-2026-248  1.3.0
starlette 0.38.6  PYSEC-2026-1943 0.40.0
starlette 0.38.6  PYSEC-2026-1941 0.47.2
starlette 0.38.6  PYSEC-2026-2281 1.1.0
starlette 0.38.6  PYSEC-2026-2280 1.1.0
```

The PyYAML finding (`PYSEC-2021-142`) is the one this project directly
controls and directly introduced: `app/requirements.txt` pinned
`PyYAML==5.3.1` when the fleet-config override loader
(`config_parser.load_yaml_overrides`) was added. `load_yaml_overrides`
itself only ever calls `yaml.safe_load`, never plain `yaml.load` -- so the
*code path* in this repo was never exploitable the way the classic
"arbitrary object deserialization via `yaml.load`" CVEs describe. But
`pip-audit` (like Trivy or any dependency scanner) flags the *version*,
not how carefully a given call site uses it, and that's the right
behavior: a safe call site today doesn't guarantee every future call site
stays safe, and a scanner that only flagged actually-exploited code paths
would need to solve a much harder problem than "is this version listed as
vulnerable."

**Fix:** bumped the pin to `PyYAML==6.0.2` in `app/requirements.txt`
(current stable release with the fix). Re-running `pip-audit` afterward
no longer lists a PyYAML finding.

## Finding 2: starlette / pytest findings against pinned versions (tracked, not fixed this week)

**Tool:** `pip-audit -r app/requirements.txt`
**Status:** Accepted for now / tracked
**Why not fixed immediately:** `starlette` isn't pinned directly in this
project's `requirements.txt` -- it's a transitive dependency pulled in by
`fastapi==0.115.0`, and `pytest` is a dev/test-only dependency, not
something shipped in the container image. Bumping either means checking
FastAPI/Starlette compatibility (a transitive-dependency bump can break
things in ways a direct pin doesn't) and isn't a one-line fix the way the
direct PyYAML pin was. Logging it here instead of quietly ignoring it is
the honest move: a real team would triage this the same way -- fix what's
cheap and direct now, track what needs a compatibility check as a
follow-up rather than let scanning findings just scroll off the CI log
unread.

**Planned follow-up:** revisit the FastAPI/Starlette pin together in a
later week once the update-server and vehicle-agent services exist too,
so all three Python services get bumped in one pass instead of three
separate dependency-only commits.

## Finding 3: Semgrep / Trivy findings (not yet executed)

**Tool:** Semgrep (`sast` job) and Trivy (`container-scan` job) in
`security.yml`
**Status:** Runbook only
Both jobs are configured and reviewed by hand for correctness (right
config packs, right image reference, `exit-code: "1"` so Trivy actually
fails the job instead of just reporting), but this dev environment can't
build a Docker image or run these GitHub Actions locally, so there's no
real output to paste here yet. They'll produce real findings the first
time a PR triggers them on GitHub -- worth re-reading this section after
that happens, since a workflow that looks right on paper and a workflow
that's actually been fed a real vulnerable base image are different
claims.
