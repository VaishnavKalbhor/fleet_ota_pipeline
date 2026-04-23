"""
climate-control: a tiny FastAPI service used to learn the CI/CD and OTA
pipeline before any OTA-specific concepts get involved. Deliberately simple.
"""
from fastapi import FastAPI

app = FastAPI(title="climate-control")

SERVICE_NAME = "climate-control"
VERSION = "1.0.0"

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
def set_config(config: dict):
    _config.update(config)
    return _config
