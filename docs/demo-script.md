# Demo Script

A walkthrough for presenting this project (interview, portfolio review)
in about 10-15 minutes, using only what's actually runnable in a plain
Python environment -- no Docker, Kubernetes, or cloud account required
to follow along.

## 1. The pitch (30 seconds)

"This simulates an OTA update pipeline for a fleet of connected
vehicles: a climate-control microservice as the thing being updated, a
staged rollout controller (5% -> 25% -> 100%) with automatic rollback,
and a CI/CD pipeline with security scanning and image signing. It's
explicitly a portfolio simulator, not a certified automotive system --
see `docs/standards-mapping.md` for exactly where that line is drawn."

## 2. Run the full test suite (1 minute)

```
python3 -m venv .venv && .venv/bin/python3 -m pip install -r app/requirements.txt -r update-server/requirements.txt -r vehicle-agent/requirements.txt
.venv/bin/python3 -m pytest app/tests update-server/tests vehicle-agent/tests rollout-controller/tests -v
```

54 tests, all passing. Worth pointing out live: these aren't just
"does it import" smoke tests -- several are regression tests written
specifically to catch a bug that was actually hit (see step 4).

## 3. Run the rollout demo (2 minutes)

```
.venv/bin/python3 rollout-controller/demo_rollout.py
```

Shows three real scenarios from one script: a healthy rollout
completing all three waves, a crashing canary triggering an automatic
rollback, and a healthy canary still getting blocked because the
security scan failed. `docs/rollout-demo.md` has the full annotated
output if there's no time to run it live.

## 4. Walk through `docs/mistakes-log.md` (3-5 minutes, the core of the demo)

This is the most interesting part to talk through, not just show. Pick
2-3 of these depending on the audience:

- **Mistake 5 / 8** (version comparison, rollback direction) -- both are
  "the code looks obviously right until you test a case nobody tries by
  hand" bugs. Good for demonstrating testing instinct.
- **Mistake 10** (security gate that didn't gate) -- good for a
  security-focused conversation: a passing pipeline and a compromised
  one produced the same "green" result.
- **Mistake 7** (Compose hostname) -- good for demonstrating the
  difference between "I ran this and watched it fail" and "I reasoned
  through why this would fail" -- this repo is honest about which bugs
  are which, and that distinction is itself worth pointing out.

For each one: what the bug was, how it was caught (a specific test, or
specific reasoning), and why the fix is correct -- not just "it's
fixed now."

## 5. Show the pipeline config, briefly (2 minutes)

`.github/workflows/security.yml` and `release.yml` -- Semgrep, Trivy,
pip-audit, SBOM generation, cosign signing. Be upfront that these
haven't run in real GitHub Actions in this dev environment (no way to
trigger that here), but `docs/security-findings.md` has real
`pip-audit` output from running it locally against the actual
requirements file.

## 6. Show the Kubernetes/Helm/ArgoCD layer, briefly (1-2 minutes)

`deploy/k8s/`, `deploy/helm/fleet-ota/`, `argocd/application.yaml`.
Same honesty: reviewed by hand and structurally validated, not run
against a live cluster in this project (unlike the earlier AutoGitOps
Platform project, which did validate similar config against a free
local `kind` cluster -- that path exists here too if it's worth doing
later).

## 7. Close (30 seconds)

Point at `docs/learning-log/` for the week-by-week build narrative and
`docs/standards-mapping.md` for where the ISO/SAE 21434 / UNECE R155 /
R156 concepts actually show up in the design -- and repeat, clearly,
that none of this is a compliance claim.
