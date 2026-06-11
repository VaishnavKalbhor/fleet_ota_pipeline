# Week 4 Learning Log

## Goal

Build the actual OTA control-flow services -- update-server (fleet's
source of truth for target version + telemetry) and vehicle-agent (the
simulated client that polls, decides whether to update, and reports
back) -- and wire five simulated vehicles up against one update-server
with docker-compose.

## What got built

- `update-server/main.py` -- `/manifest` (GET/POST), `/telemetry` (POST),
  `/fleet/status` (GET), `/health`. In-memory state (a real fleet backend
  would use a database; the point here is the control-flow logic, not a
  production data layer). 8 tests passing.
- `vehicle-agent/agent.py` -- `needs_update()`, `VehicleAgent` (in-memory
  building block), and `load_state()`/`save_state()`/`run_poll_cycle()`
  (on-disk-backed poll cycle, what actually runs on a loop). Hit and
  fixed two real bugs here (see mistakes-log.md Mistakes 5 and 6).
- `vehicle-agent/run.py` -- the actual entry point a container runs:
  reads `VEHICLE_ID`/`UPDATE_SERVER_URL`/`STATE_PATH`/
  `POLL_INTERVAL_SECONDS` from the environment, loops calling
  `update-server` over HTTP.
- `docker-compose.yml` -- one `update-server` plus five distinct
  `vehicle-agent-0N` services, each with its own `VEHICLE_ID`. Hit and
  fixed a networking bug here (see mistakes-log.md Mistake 7).

25/25 tests passing across update-server (8) + vehicle-agent (9) +
app (16 -- unchanged from Week 3) by end of week.

## A design decision, not a bug: five services, not one scaled service

Docker Compose's `deploy.replicas` (or `docker compose up --scale`) would
have been the shorter way to write "five vehicle agents" -- one service
block instead of five near-identical ones. Deliberately didn't do that,
because Compose gives scaled replicas of the *same* service a shared
environment by default; getting each replica a distinct `VEHICLE_ID`
that way needs an entrypoint script that derives an ID from the
container's hostname/replica index at runtime, which is exactly the kind
of thing that's easy to get wrong (two replicas racing to read the same
"next ID" file, or a naive scheme that collides after a restart) and
would produce a genuinely confusing bug: five containers all reporting
telemetry under the same `vehicle_id`, so `/fleet/status` would show a
fleet of size 1 no matter how many agents were actually running. Five
explicit service blocks with hardcoded `VEHICLE_ID` values are more
lines of YAML but have zero ambiguity about which container is which
vehicle -- worth calling out as a case where the "obviously more elegant"
option was rejected on purpose, not just not yet gotten to.

## Reflection

Both real bugs this week (Mistakes 5 and 6) are in the same 40-line file
and are both flavors of the same underlying risk: a function that
computes the right answer in memory but either compares the wrong things
or never writes the answer down. Neither would show up from reading
`agent.py` top to bottom and nodding along -- both needed a test that
called the function more than once, or with an input that isn't the
first thing you'd try by hand (a two-digit version number; five
consecutive poll cycles instead of one). The docker-compose hostname
mistake (Mistake 7) is a different category entirely -- it's not a logic
bug at all, it's a config value that's "wrong" only in light of how
Compose's networking actually works, and it's the one mistake this week
I could reason through carefully but not actually watch fail, since this
dev environment has no Docker.
