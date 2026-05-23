# Week 3 Learning Log

## Goal

Turn the toy app into a properly CI-tested service, and get the security pipeline (Semgrep/Trivy/Syft) running around it.

## App changes

Added `/metrics` (prometheus-fastapi-instrumentator), wired `APP_VERSION` through as an env var / Docker build ARG so each built image can be stamped with its own version -- this is how a "vehicle" later reports which version it's actually running, not just what the source code says. Moved config validation into its own `app/config_parser.py` module (built in Week 2) and wired `POST /config` to actually use it, returning 422 on invalid config instead of silently accepting garbage.

14/14 tests passing (8 config parser + 3 health + 3 version).

## CI and security pipeline

Added `.github/workflows/ci.yml` -- checkout, Python 3.12, install app deps, `pytest -v`, then a Docker build of the app image (build only, no push yet -- that's Week 7's `release.yml`).

Added `.github/workflows/security.yml` with four jobs: Semgrep (SAST), Trivy (container image scan, configured to fail on CRITICAL/HIGH), a `dependency-scan` job running `pip-audit` against `app/requirements.txt`, and an SBOM job (Syft, SPDX format).

Hit a real one here: the SBOM job generated `sbom.spdx.json` and then just... ended. GitHub Actions runners are thrown away at the end of the job, so anything written to disk and not explicitly published as an artifact never leaves the runner -- the job stays green, but there's nothing to actually download. See mistakes-log.md Mistake 4. Fixed with `actions/upload-artifact@v4`.

Also added a small feature -- `config_parser.load_yaml_overrides()`, letting an operator ship a per-trim config override as a YAML file -- and pinned `PyYAML==5.3.1` for it in `app/requirements.txt`. Once the `dependency-scan` job existed, running `pip-audit -r app/requirements.txt` locally immediately flagged that exact pin (`PYSEC-2021-142`, fixed in PyYAML 5.4+), plus two findings this project doesn't directly control yet (`starlette` via FastAPI's transitive pin, and dev-only `pytest`). Bumped PyYAML to 6.0.2, confirmed with a second `pip-audit` run that the PyYAML finding is gone, and logged the other two as tracked/accepted-for-now in `docs/security-findings.md` rather than quietly ignoring them or rushing an unrelated transitive-dependency bump.

16/16 tests passing (10 config parser + 3 health + 3 version) at end of week.

## Reflection

This week's bugs (missing SBOM upload, vulnerable dependency pin) are both things a superficial "does the workflow YAML look reasonable" read would miss -- the SBOM one only shows up if you ask "where does that file actually end up," and the PyYAML one only shows up once there's an actual scanner running against the actual pin, not just eyeballing a version number. That's the same lesson as Week 2's toy-experiment bugs, just one layer up: the pipeline meant to catch mistakes needs the same scrutiny as the code it's scanning, or it just adds a false sense of security instead of removing one.
