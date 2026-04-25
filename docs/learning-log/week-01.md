# Week 1 Learning Log

## Goal

Build a tiny "climate control" service and learn the basics before touching OTA concepts at all: a REST API, unit tests, and a Docker container.

## Building the app

FastAPI app with /health, /version, /config (GET+POST) done first, tests written and passing (4/4) before touching Docker at all -- wanted the app logic solid before adding a container around it.

## Containerizing it

Wrote a Dockerfile using `uvicorn main:app --port 8000` (matching the plan's example command literally). Building it next.

## Mistake found: container unreachable

Built the image and ran it -- no errors, uvicorn logs looked fine, but couldn't reach it from outside the container. Missing `--host 0.0.0.0` in the CMD (uvicorn defaults to binding 127.0.0.1, which inside a container isn't reachable via the host port mapping). Fixed and documented in docs/mistakes-log.md -- this is exactly the kind of "worked in the logs, didn't work in practice" bug that's easy to lose an hour to.
