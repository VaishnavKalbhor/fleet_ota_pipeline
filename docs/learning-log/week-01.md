# Week 1 Learning Log

## Goal

Build a tiny "climate control" service and learn the basics before touching OTA concepts at all: a REST API, unit tests, and a Docker container.

## Building the app

FastAPI app with /health, /version, /config (GET+POST) done first, tests written and passing (4/4) before touching Docker at all -- wanted the app logic solid before adding a container around it.

## Containerizing it

Wrote a Dockerfile using `uvicorn main:app --port 8000` (matching the plan's example command literally). Building it next.
