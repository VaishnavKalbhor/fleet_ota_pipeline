# Week 7 Learning Log

## Goal

Move from "the app and control logic work" to "here's how a real build
would actually ship" -- a signed, SBOM'd release pipeline, and the
Kubernetes/Helm/ArgoCD config that pipeline's output would deploy into.

## What got built

- `.github/workflows/release.yml` -- tag-triggered build, push to GHCR,
  Syft SBOM (uploaded as an artifact, learning Week 3's lesson), cosign
  keyless image signing. Hit and fixed a real permissions bug here (see
  mistakes-log.md Mistake 11).
- `deploy/k8s/` -- plain Kubernetes manifests for both services:
  namespace, deployments (non-root, dropped capabilities, read-only root
  filesystem, resource requests/limits, readiness/liveness probes on
  `/health`), services, an HPA for climate-control, and default-deny
  NetworkPolicies with explicit allows (same pattern as the earlier
  AutoSecureOps project).
- `deploy/helm/fleet-ota/` -- the same deployment shape as a hand-written
  Helm chart, parameterized via `values.yaml`.
- `argocd/application.yaml` + `docs/gitops-workflow.md` -- how ArgoCD
  would sync this chart from Git, and an explicit note on why the
  release pipeline doesn't auto-commit a `values.yaml` bump back into
  `main` (avoiding a self-triggering loop and an untraceable commit
  history).

## Honesty about what's actually verified this week

Nothing in `deploy/k8s`, `deploy/helm`, or `argocd` has touched a real
cluster -- this dev environment has no `kubectl`, `helm`, or `argocd`
CLI, and no Docker to even build the images `release.yml` would push.
What *was* actually checked: every plain YAML file parses
(`yaml.safe_load`), and every Helm template's surrounding YAML structure
is sound once its `{{ }}` expressions are stripped out (a real check,
just not the same as `helm template` rendering real values and
validating the output against the Kubernetes API schema). Labeling that
distinction clearly in `deploy/helm/fleet-ota/README.md` and
`docs/gitops-workflow.md` matters more this week than most, since this
is the point in the project where "written correctly" and "proven
correct" diverge the furthest.

## Reflection

Mistake 11 (missing `id-token: write`) is a different flavor of bug than
most of this project's mistakes-log: it's not a logic error that
produces a wrong answer, it's a missing grant that causes a hard, loud
failure the first time the workflow actually runs. In a sense that's the
*safer* kind of mistake to make -- nobody ships an unsigned image
thinking it's signed, because the job fails outright -- which is a good
argument for why "does the security-critical step fail loudly or fail
silently" is worth thinking about deliberately when designing a
pipeline, not just whether the step exists at all.
