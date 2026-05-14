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
