# Standards Mapping (inspired-by, not a compliance claim)

This project is a portfolio simulator, not a certified automotive
system, and nothing in this document claims otherwise. ISO/SAE 21434,
UNECE R155, and UNECE R156 are real automotive cybersecurity and
software-update standards with formal audit, certification, and
type-approval processes behind them -- none of which this project has
gone through. What follows is a mapping of *which concepts* from those
standards this project's design was inspired by and where each shows up
in the code, for someone (an interviewer, a reviewer) who wants to see
that the design choices weren't arbitrary. It is not a self-assessment
against the standards' actual clauses, and it should not be read as one.

## ISO/SAE 21434 (Road vehicles -- Cybersecurity engineering)

| Concept | Where it shows up here |
| --- | --- |
| Threat-informed design decisions, not just "add security tools" | The default-deny NetworkPolicies in `deploy/k8s/network-policy.yaml` and the staged-rollout safety gates in `rollout-controller/controller.py` are both decisions made because of a specific failure mode considered up front, not a checklist item. |
| Dependency and supply-chain risk management | `docs/security-findings.md` (real `pip-audit` findings, triaged not just logged) and the SBOM step in both `security.yml` and `release.yml`. |
| Verification of security controls, not just their presence | `docs/mistakes-log.md` Mistake 10 is specifically about a security gate that existed but didn't actually gate anything -- the standard's emphasis on verifying controls work, not just exist, is the whole reason that bug is worth documenting. |

## UNECE R155 (Cybersecurity Management System)

| Concept | Where it shows up here |
| --- | --- |
| Monitoring for security-relevant events post-deployment | `update-server`'s `/events` and `/telemetry` endpoints, and the Prometheus/Grafana wiring in `telemetry/` (not run against a live cluster, but designed for it). |
| Incident response capability, including rollback | `rollout-controller/controller.py::plan_rollback` and the rollback path in `run_staged_rollout` -- a CSMS expects an organization to be able to respond to and remediate a deployed issue, and an automated rollback triggered by real telemetry thresholds is a concrete (if small-scale) version of that capability. |

## UNECE R156 (Software Update Management System)

| Concept | Where it shows up here |
| --- | --- |
| Staged/controlled rollout rather than fleet-wide simultaneous update | The 5% / 25% / 100% wave sequence in `run_staged_rollout`, directly modeled on R156's expectation that a SUMS assess update safety before wide deployment. |
| Update integrity and authenticity | `experiments/toy_signature_check.py` (fake-signature manifest flow, built to understand the shape) and cosign image signing in `release.yml` -- this project does NOT implement a full Uptane-style signed-metadata chain (root/targets/snapshot/timestamp roles, key rotation, delegation), just the single-signature cosign step, which is a meaningfully smaller guarantee than what a production automotive SUMS would need. |
| Rollback and safe-state guarantee | Same rollback path as R155's incident-response mapping above -- R156 specifically expects an update mechanism to be able to safely reverse a failed update, which is exactly what Mistake 8 in the mistakes log was about getting right. |

## What this project explicitly does NOT claim

No formal risk assessment (TARA) was performed. No independent audit
occurred. The "signing" in this project is a single cosign keyless
signature over a container image, not a full software bill of update
metadata with the multi-role key hierarchy Uptane-inspired systems (and
real automotive SUMS implementations) typically use. The Kubernetes/Helm
deployment config has not been run against a live cluster. None of the
threat modeling here went through a real TARA process. This document
exists to show the standards informed the design vocabulary and
priorities, not to claim conformance.
