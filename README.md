# Fleet-OTA

A portfolio project simulating a secure CI/CD and over-the-air (OTA)
update pipeline for a fleet of connected-vehicle microservices: staged
rollouts, automatic rollback, security scanning, image signing, and
telemetry-driven decisions.

**This is not a certified automotive system.** It doesn't implement
ISO/SAE 21434, UNECE R155, or UNECE R156 -- see
[`docs/standards-mapping.md`](docs/standards-mapping.md) for exactly
which concepts from those standards informed the design, and an
explicit list of what isn't claimed.

## What's in here

| Component | What it does |
| --- | --- |
| `app/` | `climate-control` -- the FastAPI microservice being "updated." Health/version/config endpoints, Prometheus metrics, YAML config overrides. |
| `update-server/` | Fleet source of truth: current manifest (target version + image), telemetry ingestion, fleet status, rollout event log. |
| `vehicle-agent/` | Simulated vehicle client: polls the manifest, decides whether to update, applies it, persists state, reports telemetry. |
| `rollout-controller/` | Staged rollout orchestration (5% -> 25% -> 100%), canary health checks, rollback planning, security-gated promotion. |
| `deploy/k8s/`, `deploy/helm/fleet-ota/`, `argocd/` | Kubernetes manifests, a hand-written Helm chart, and an ArgoCD Application -- written and reviewed, not run against a live cluster (see caveats below). |
| `.github/workflows/` | `ci.yml` (tests + build), `security.yml` (Semgrep, Trivy, pip-audit, SBOM), `release.yml` (build, push, sign, SBOM). |
| `telemetry/` | Prometheus scrape config + Grafana dashboard for `climate-control`'s real `/metrics` output. |
| `experiments/` | Small throwaway scripts from Week 2 that surfaced two of the bugs below before they ever reached real code. |
| `docs/` | Week-by-week learning log, the mistakes log, security findings, GitOps notes, standards mapping, demo script. |

## Getting started

```
python3 -m venv .venv
.venv/bin/python3 -m pip install -r app/requirements.txt -r update-server/requirements.txt -r vehicle-agent/requirements.txt
.venv/bin/python3 -m pytest app/tests update-server/tests vehicle-agent/tests rollout-controller/tests -v
```

Or, with `make` (see `Makefile`): `make install`, `make test`,
`make demo`, `make lint-yaml`.

54 tests, all passing as of the last commit. Run
`.venv/bin/python3 rollout-controller/demo_rollout.py` to see a healthy
rollout, a crash-triggered rollback, and a security-blocked rollout, all
with real captured output (also in
[`docs/rollout-demo.md`](docs/rollout-demo.md)).

## Interesting bugs and lessons

Every one of these was actually hit and actually fixed -- see
[`docs/mistakes-log.md`](docs/mistakes-log.md) for the full writeup of
each, including commit references and (where possible) the exact wrong
output observed before the fix.

| # | Bug | Why it's interesting |
| --- | --- | --- |
| 1 | `uvicorn` bound to `127.0.0.1` instead of `0.0.0.0` in the Dockerfile | The classic "works when I run it directly, unreachable in a container" gotcha. |
| 2 | 5% rollout wave computed to 0 vehicles via `int()` truncation | Silently disables the entire canary safety mechanism for smaller fleets. |
| 3 | Crash rate calculated against the whole fleet instead of updated vehicles | Makes a canary failure look calm precisely because most of the fleet hasn't been touched yet. |
| 4 | SBOM generated in CI but never uploaded as an artifact | Job stays green; the artifact just doesn't exist anywhere. |
| 5 | Version comparison used string ordering (`"1.10.0" < "1.2.0"` is `True`) | Correct for versions 1.0-1.9, silently wrong the moment a component hits double digits. |
| 6 | Poll cycle computed an update but never persisted it | The "agent reinstalls forever" failure mode -- correct in memory, never written to disk. |
| 7 | Vehicle agents in Docker Compose pointed at `localhost` instead of the service name | Reasoned through, not executed (no Docker in this dev environment) -- flagged as such. |
| 8 | Rollback reused the forward-only version check, so it could never move backward | The most dangerous bug here: it doesn't misbehave, it makes the safety mechanism a no-op. |
| 9 | Rollout manifests referenced the mutable `:latest` tag | Breaks the guarantee that a canary and a wide rollout pull the same image. |
| 10 | Wave promotion gate accepted a security-scan flag and then ignored it | A failed scan and a passed scan produced the identical "promotion allowed" result. |
| 11 | Release workflow missing `id-token: write` for cosign keyless signing | Reasoned through, not executed -- a hard, loud failure rather than a silent one. |

## Honesty about what's verified versus reviewed

This project draws a hard line between two claims that look similar but
aren't: "I ran this and watched the real output" and "I read this
carefully and I'm confident it's correct." Every doc in this repo that
makes either claim says explicitly which one it's making. Concretely:

**Actually run and verified in this dev environment:** all Python
application logic (`app/`, `update-server/`, `vehicle-agent/`,
`rollout-controller/`), all 54 tests, the `pip-audit` findings in
`docs/security-findings.md`, the real `/metrics` output confirmed
against `telemetry/README.md`'s dashboard queries, `make lint-yaml`
parsing every plain YAML file in the repo, and the three rollout demo
scenarios in `docs/rollout-demo.md`.

**Written and reviewed, not executed** (no Docker, no Kubernetes
cluster, no cloud account, no GitHub Actions runner available in this
dev environment): `docker-compose.yml`, everything in `deploy/k8s/` and
`deploy/helm/`, `argocd/application.yaml`, and the GitHub Actions
workflows themselves (their YAML is syntactically valid and hand-reviewed
for correctness, but none has actually triggered on GitHub).

## Status

Complete through the original 8-week plan. See
[`docs/learning-log/`](docs/learning-log/) for the week-by-week build
narrative and [`docs/demo-script.md`](docs/demo-script.md) for a guided
walkthrough of the whole project.
