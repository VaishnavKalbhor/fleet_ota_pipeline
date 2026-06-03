# Mistakes Log

Real mistakes made while building this project, in the order they happened, with what broke, why, and how it got fixed. This is not a cleaned-up list written after the fact -- it's meant to mirror the actual commit history (see git log): most of these show up as a commit that has the bug, followed by a separate commit that fixes it.

## Mistake 1: Container starts but is unreachable from the host

**Commit that introduced it:** `Containerize climate-control service`
**Commit that fixed it:** `Fix Dockerfile: bind uvicorn to 0.0.0.0`

The first Dockerfile ran `uvicorn main:app --port 8000` with no `--host`
flag. `docker build` and `docker run -p 8000:8000 climate-control:dev` both
succeeded, the container logs showed uvicorn running, but
`curl http://localhost:8000/health` from the host just hung / connection
refused.

**Why:** uvicorn's default bind address is `127.0.0.1` (localhost). Inside a
container, "localhost" means the container's own network namespace, not the
host machine -- so the server was listening, just not on an interface
Docker's port mapping could reach.

**Fix:** add `--host 0.0.0.0` to the uvicorn command, so it listens on all
interfaces inside the container and the `-p 8000:8000` port mapping actually
has something to forward to.

This is a genuinely common first-Docker-container mistake, not a
manufactured one -- worth documenting because it looks like nothing is wrong
(no error, no crash) right up until you try to actually use the thing.

## Mistake 2: 5% rollout wave updated zero vehicles

**Commit that introduced it:** `Add toy rollout percentage math experiment`
**Commit that fixed it:** `Fix wave math: force at least 1 vehicle when percentage > 0`

`wave_size(10, 0.05)` computed `int(10 * 0.05) == int(0.5) == 0`. Ran the
script directly and saw it print "5% wave -> 0 vehicles" -- the canary wave,
the whole point of staged rollout, would never actually start.

**Fix:** if the requested percentage is greater than zero, force at least 1
vehicle (`max(1, calculated)`). Added `rollout-controller/tests/test_wave_math.py`
to lock this in before it becomes load-bearing in the real rollout
controller (Week 6).

This is arguably the single most "interview-worthy" bug in the whole
project -- it's an integer-truncation edge case that only shows up at
specific fleet sizes, and it silently breaks the safety mechanism (canary
before wide rollout) that the whole staged-rollout design exists for.

## Mistake 3: Error rate calculated against the whole fleet, not the updated vehicles

**Commit that introduced it:** `Add toy telemetry error-threshold experiment`
**Commit that fixed it:** `Fix error-rate calculation: divide by updated vehicles, not total fleet`

v1 computed `crashes / total_fleet`. In a canary wave (say 1 of 10 vehicles
updated), if that one vehicle crashes, `1/10 = 10%` -- under the 20%
threshold, so `should_rollback` returned `False` even though the real
picture is "the only vehicle we updated crashed."

**Fix:** filter to vehicles that have actually received the update first,
then divide crashes by *that* count. `1 crash / 1 updated = 100%`, correctly
above threshold. Added `rollout-controller/tests/test_error_threshold.py`
(4 tests) covering the canary-crash, healthy-canary, nothing-updated-yet,
and larger-wave cases.

This is the one the plan singles out as "very relevant to safety-critical
staged deployment," and it's right -- getting this backwards makes a
canary wave actively dangerous: the safety mechanism looks calm precisely
because most of the fleet hasn't been touched yet, which is the opposite of
what it should signal.

## Mistake 4: SBOM generated in CI but never uploaded anywhere

**Commit that introduced it:** `Add security scanning workflow: Semgrep, Trivy, SBOM generation`
**Commit that fixed it:** `Upload SBOM as a downloadable build artifact`

The `sbom` job in `security.yml` ran Syft against the built image and wrote
`sbom.spdx.json` inside the runner's workspace, then... stopped. GitHub
Actions runners are ephemeral -- anything written to disk during a job and
not explicitly published (as an artifact, a release asset, a registry
attachment, etc.) simply disappears when the runner is torn down at the
end of the job. The job went green every time, which made this an easy
one to miss: "SBOM generation succeeded" and "the SBOM is actually
available to anyone" are two different claims, and the workflow only
proved the first one.

**Fix:** added an `actions/upload-artifact@v4` step right after the Syft
step, uploading `sbom.spdx.json` with a 90-day retention window. Now the
SBOM shows up as a downloadable artifact on the workflow run summary --
which is the whole point of generating one in the first place (traceable,
inspectable dependency inventory per build).

This one doesn't need a live GitHub Actions run to verify: it's a
structural fact about the YAML. A `run:`/action step that writes a file
and is never followed by an upload/publish step for that file has no way
for the artifact to leave the runner, regardless of whether the step
itself succeeds. Caught this by re-reading the workflow the way a
reviewer would, rather than by running it.

## Mistake 5: Version comparison used string ordering instead of numeric ordering

**Commit that introduced it:** `Add vehicle-agent polling and update logic`
**Commit that fixed it:** `Fix version comparison: parse version parts as integers, not strings`

`needs_update()` compared version strings directly (`current_version <
target_version`). That's Python string comparison, which is
lexicographic/character-by-character -- and dotted version numbers are not
strings for ordering purposes once any component reaches two digits.
`"1.10.0" < "1.2.0"` is `True` in plain string comparison (`'1' == '1'`,
then `'.' == '.'`, then `'1' < '2'`), even though `1.10.0` is the *newer*
version (minor version 10 vs minor version 2). A vehicle already running
`1.10.0` would see a manifest targeting `1.2.0` and think it needed to
"update" -- effectively downgrading itself, or at minimum flip-flopping
between versions depending on which vehicles polled when.

Wrote the regression test (`test_double_digit_minor_version_is_compared_numerically_not_lexically`)
*with* the buggy code still in place and watched it fail with the exact
wrong-direction result (`needs_update("1.10.0", "1.2.0")` returned `True`)
before writing the fix, so this isn't a hypothetical -- it's a bug that
was actually observed.

**Fix:** parse each version string into a tuple of ints
(`"1.10.0" -> (1, 10, 0)`) and compare the tuples, which is Python's
normal numeric tuple ordering. All 7 vehicle-agent tests pass after the
fix, including the double-digit regression case.

This is the classic "works fine in every manual test because nobody
happens to test past version 9" bug -- the kind of thing that looks
completely correct through versions 1.0 through 1.9 and then silently
breaks fleet-wide the day a service crosses into double-digit minor or
patch versions.

## Mistake 6: Poll cycle computed the update but never saved it, so vehicles "updated" forever without converging

**Commit that introduced it:** `Add persisted on-disk state for vehicle-agent poll cycles`
**Commit that fixed it:** `Persist state after every poll cycle so updates actually stick`

`run_poll_cycle()` loaded a vehicle's on-disk state, applied the update
logic to the in-memory `state` dict, and returned it -- but never wrote
that dict back to `state_path`. Every individual cycle looked completely
correct in isolation (call it once, the returned dict shows the new
version) which is exactly why this is an easy one to miss in a quick
manual check. The regression test in the previous commit calls
`run_poll_cycle()` five times in a row against the same state file and
then reads the file back, and the file didn't just show the old version
-- it didn't exist at all, because nothing ever called `open(..., "w")`.

In a real agent that polls on a timer (or reloads its state after a
restart, which is the more realistic trigger), this is the "agent
reinstalls the same update forever" failure mode: every cycle sees stale
on-disk state, concludes it's still behind, "applies" the update again in
memory, and throws that result away before the next cycle starts from
the same stale file. From the fleet's perspective (via telemetry, once
that's wired to this loop) it would look like a vehicle stuck
permanently in an "updating" loop that never resolves to "healthy at the
target version."

**Fix:** added `save_state()` and call it at the end of `run_poll_cycle()`,
after applying any update, before returning. Re-ran the exact same
five-cycle test and the persisted file now reads back the target version
after the first cycle and stays there.

This mistake and the previous one (Mistake 5, version comparison) are
both in the same file for a reason: they're the two ways a "did this
vehicle successfully update" check can lie to you -- one by getting the
comparison direction wrong, the other by never actually recording the
outcome of a comparison that was correct.
