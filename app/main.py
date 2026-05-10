"""
climate-control: the vehicle-side workload that gets built, tested, scanned,
signed, and rolled out to simulated vehicle ECUs via the OTA pipeline.
"""
import os

from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator

from config_parser import parse_config, ConfigError

app = FastAPI(title="climate-control")

SERVICE_NAME = "climate-control"
# Read at import time so each built image can be stamped with its own
# version via `docker build --build-arg APP_VERSION=1.1.0` -> ENV in the
# Dockerfile. This is how a "vehicle" (an instance of this service) reports
# which version it's running.
VERSION = os.environ.get("APP_VERSION", "1.0.0")

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

_config = {
    "target_temperature": 21,
    "fan_speed": 2,
    "mode": "auto",
}


@app.get("/health")
def health():
    return {"service": SERVICE_NAME, "version": VERSION, "status": "healthy"}


@app.get("/version")
def version():
    return {"service": SERVICE_NAME, "version": VERSION}


@app.get("/config")
def get_config():
    return _config


@app.post("/config")
def set_config(raw_config: dict):
    global _config
    try:
        merged = {**_config, **raw_config}
        validated = parse_config(merged)
    except ConfigError as e:
        raise HTTPException(status_code=422, detail=str(e))
    _config = validated
    return _config
