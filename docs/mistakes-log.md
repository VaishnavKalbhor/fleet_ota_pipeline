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
