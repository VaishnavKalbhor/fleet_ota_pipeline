# Telemetry

`prometheus.yml` -- scrape config, syntax-checked but not run against a
real Prometheus server (no Prometheus binary in this dev environment).

`grafana-dashboard.json` -- three panels (request rate, p95 latency,
5xx rate) built against `http_requests_total` and
`http_request_duration_seconds_bucket`, which are
`prometheus-fastapi-instrumentator`'s documented default metric names
(the library instruments FastAPI's `handler`/`method`/`status` labels
automatically once `Instrumentator().instrument(app).expose(app,
endpoint="/metrics")` is called, which `app/main.py` does). Not verified
against a live scrape in this environment -- the metric names are taken
from the library's own defaults, not confirmed against a running
`/metrics` endpoint hit by a real Prometheus instance.

Neither file has been imported into an actual Grafana instance.
