# Telemetry

`prometheus.yml` -- scrape config, syntax-checked but not run against a
real Prometheus server (no Prometheus binary in this dev environment).

`grafana-dashboard.json` -- three panels (request rate, p95 latency,
5xx rate) built against `http_requests_total` and
`http_request_duration_seconds_bucket`. These aren't taken on faith from
the library's docs -- hit `/metrics` on a real `TestClient` instance of
`app/main.py` and confirmed the actual output, for example:

```
http_requests_total{handler="/health",method="GET",status="2xx"} 1.0
http_request_duration_seconds_bucket{handler="/health",le="0.1",method="GET"} 1.0
```

One detail worth noting: `status` comes back grouped as `"2xx"`/`"5xx"`,
not a specific numeric code -- `prometheus-fastapi-instrumentator`
groups status codes by default. The dashboard's 5xx-rate query uses
`status=~"5.."`, which still matches the literal string `"5xx"` (`5`
followed by any two characters), so it works correctly against the real
label value, but that's worth flagging as a "looks like it's matching
numeric codes, actually matches the grouped label" detail rather than
something obviously correct on a first read.

What's still not verified: this hasn't been scraped by a real Prometheus
server, and neither JSON file has been imported into an actual Grafana
instance -- both require software this dev environment doesn't have
installed.
