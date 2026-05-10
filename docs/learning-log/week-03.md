# Week 3 Learning Log

## Goal

Turn the toy app into a properly CI-tested service, and get the security pipeline (Semgrep/Trivy/Syft) running around it.

## App changes

Added `/metrics` (prometheus-fastapi-instrumentator), wired `APP_VERSION` through as an env var / Docker build ARG so each built image can be stamped with its own version -- this is how a "vehicle" later reports which version it's actually running, not just what the source code says. Moved config validation into its own `app/config_parser.py` module (built in Week 2) and wired `POST /config` to actually use it, returning 422 on invalid config instead of silently accepting garbage.

14/14 tests passing (8 config parser + 3 health + 3 version).
