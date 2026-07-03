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

## Mistake 7: Vehicle agents pointed at `localhost` instead of the Compose service name

**Commit that introduced it:** `Add docker-compose fleet simulation: update-server + 5 vehicle agents`
**Commit that fixed it:** `Point vehicle agents at the update-server Compose service name`

**Note on verification:** this one is different from the others in this
log. Docker isn't available in the environment this project is being
built in (no Docker daemon, no `docker compose` binary), so unlike
Mistakes 1, 2, 3, 5, and 6, I couldn't actually run `docker compose up`
and watch this fail. What follows is a config mistake I'm confident is
real because it's a deterministic fact about how Compose's networking
works, not something I ran and observed -- flagging that distinction
explicitly rather than implying I tested something I didn't.

Each `vehicle-agent-0N` service was given
`UPDATE_SERVER_URL: http://localhost:8000`. Inside a container,
`localhost` / `127.0.0.1` always refers to that container itself, never
another container on the same Compose network -- Compose gives every
service its own network namespace and makes services reachable from each
other by *service name* (Compose sets up a DNS entry per service name
on the shared network), not via the host's or another container's
loopback address. So every `vehicle-agent-0N` container would have tried
to reach an update-server on its own loopback interface, where nothing
is listening, and every poll would fail with a connection error --
which `run.py`'s `except httpx.HTTPError` catches and logs, so the
container would stay "up" and just spin forever printing poll failures
instead of crashing loudly. That's arguably worse than a crash: a
quick `docker compose ps` would show five healthy-looking containers
while none of them are actually doing anything.

**Fix:** changed `UPDATE_SERVER_URL` to `http://update-server:8000` --
`update-server` is the service name Compose already resolves on the
shared default network, matching the `update-server` service block at
the top of `docker-compose.yml`. `run.py`'s own default
(`http://localhost:8000`) is left as-is on purpose: that default is for
running the script directly on a dev machine against a locally-running
update-server, where `localhost` is correct -- the bug was specifically
in the Compose environment values overriding that default with the same
(wrong, for that context) value.

## Mistake 8: Rollback logic reused the forward-only version check, so it could never move backward

**Commit that introduced it:** `Add rollout-controller: staged waves, rollback planning, manifest builder`
**Commit that fixed it:** `Fix plan_rollback: use inequality, not needs_update, to detect rollback action`

`plan_rollback()` called `needs_update(current_version, previous_version)`
to decide whether a rollback action was needed. `needs_update()` is
correct for its actual purpose (deciding whether to *update forward* to a
newer target) but rollback is the opposite operation: a vehicle on a
broken new version (say `1.3.0`) needs to move *backward* to a
previously-known-good version (`1.2.0`). `needs_update("1.3.0", "1.2.0")`
is `False` -- `1.3.0` is not older than `1.2.0` -- so `plan_rollback`
returned `None`, meaning "no action needed," for the exact scenario
rollback exists to handle. The test written alongside this bug
(`test_rollback_from_broken_new_version_to_older_safe_version_is_triggered`)
failed with `assert None is not None` before the fix, confirming this
wasn't just a suspicious-looking line -- it's a rollback path that
silently does nothing.

This is the single most dangerous bug in the mistakes log so far: every
other bug here (wave math, error-rate denominator, version comparison)
makes the system behave *incorrectly*, but this one makes the system's
own safety mechanism -- the thing that's supposed to fire when
`should_rollback()` says a wave is unhealthy -- a no-op. `should_rollback`
correctly detecting danger and `plan_rollback` correctly acting on it are
two different code paths, and only testing the first one (which is what
the Week 2 toy experiment did) would have missed this entirely.

**Fix:** `plan_rollback` now compares versions with plain inequality
(via the same `_parse_version` tuple parsing used elsewhere, so
`"1.3.0"` and `"1.3"` aren't treated as different by a formatting
accident) instead of the forward-only `needs_update` check. Any mismatch
between current and the rollback target is an action, in either
direction.

## Mistake 9: Rollout manifests referenced the mutable `:latest` image tag

**Commit that introduced it:** `Add rollout-controller: staged waves, rollback planning, manifest builder`
**Commit that fixed it:** `Pin rollout manifests to the target version's image tag, not :latest`

`build_manifest_for_wave()` always set `"image": "climate-control:latest"`
regardless of which `target_version` the wave was rolling out. `:latest`
is a mutable tag -- whatever image was most recently pushed under that
name -- not a fixed reference to a specific build. For a staged rollout
that's a real problem, not just a style nitpick: the whole premise of a
5% canary wave is "test this exact build on a small slice of the fleet
before trusting it everywhere." If the 5% wave pulls `:latest` and the
95% wave pulls `:latest` again later, there's no guarantee those two
pulls resolve to the same image -- someone could push a new build to
`:latest` in between (a hotfix for something unrelated, a CI re-run,
anything), and the wide rollout would silently deploy a *different,
never-canaried* image while the manifest still claims a specific
`target_version` was validated.

**Fix:** the manifest's `image` field now interpolates `target_version`
directly (`climate-control:1.3.0`, not `climate-control:latest`), so the
tag a wave pulls is exactly and only the build that was tested at that
version. `test_manifest_pins_an_immutable_tag_matching_target_version`
confirms the manifest's image tag always matches the version it claims
to be rolling out.

Combined with Mistake 8 (rollback), this week's controller had two ways
the safety story around "canary something small before trusting it
everywhere" could quietly fail: rollback that doesn't roll back, and a
canary that might not even be testing the build that later gets promoted.

## Mistake 10: Wave promotion gate ignored the security scan result entirely

**Commit that introduced it:** `Add wave promotion gate for staged rollout`
**Commit that fixed it:** `Require both a healthy canary and a passed security scan to promote a wave`

`is_wave_promotion_allowed()` took both `canary_healthy` and
`security_scan_passed` as parameters -- which reads, at a glance, like a
function that checks both -- but the function body only ever returned
`canary_healthy`. `security_scan_passed` was accepted and silently
ignored. `test_promotion_blocked_when_security_scan_failed_even_if_canary_healthy`
called it with a healthy canary and a *failed* scan and got `True` back:
promotion allowed, gate passed, despite the one input specifically meant
to block that outcome.

This is the same shape as Week 3's missing-SBOM-upload mistake in one
sense (a step that looks like it's doing its job because the pipeline
stays green) but more dangerous, because it's not "the artifact is
missing," it's "a security failure produces the identical outcome as a
security pass." Nothing about running this function would ever surface
the bug unless a test specifically exercised the security-failed case --
the security-passed path (which is what almost every manual/happy-path
test would check first) returns the same answer either way the bug
exists or not.

**Fix:** the function now requires both conditions
(`canary_healthy and security_scan_passed`). This closes out the
Week 5 "mistake period": five distinct, real problems this week and
last (rollback direction, mutable tags, and this gate, plus the two
already-fixed lessons from Week 2 ported into the real controller
without regressing them) -- all caught by writing a test for the
specific case each bug gets wrong, not by general code review.

## Mistake 11: Release workflow missing `id-token: write` for cosign keyless signing

**Commit that introduced it:** `Add release workflow: build, push, SBOM, cosign signing`
**Commit that fixed it:** `Grant id-token: write permission for cosign keyless signing`

**Note on verification:** same caveat as Mistake 7 -- this environment
has no GitHub Actions runner and no way to actually push to a registry
or run `cosign`, so this wasn't observed failing in a live run. It's
included because it's a specific, well-documented requirement of how
cosign's keyless signing works, not a guess.

`cosign sign --yes` without a static key pair uses Sigstore's keyless
flow: the workflow needs to mint a short-lived OIDC identity token bound
to the job (via GitHub's OIDC provider) and present it to Fulcio to get
a signing certificate. That OIDC token is only issued to a job if the
workflow explicitly requests it with `permissions: id-token: write` --
without it, the `id-token` permission defaults to `none` under the
default (least-privilege) permissions model, and `cosign sign` fails
outright rather than silently skipping the signature. The original
`release.yml` set `contents: read` and `packages: write` (both genuinely
needed -- checkout and pushing to GHCR) but not `id-token: write`, which
would have made the entire signing step fail on the first real tag push.

Unlike Mistake 7 (a step that "succeeds" but produces nothing useful),
this one is a hard failure -- the job would show a clear red X on the
`cosign sign` step. Less dangerous in that sense (nobody ships an
unsigned image thinking it's signed), but still worth catching before
the first real release rather than after.

**Fix:** added `id-token: write` to the job's `permissions` block,
alongside `contents: read` and `packages: write`.
