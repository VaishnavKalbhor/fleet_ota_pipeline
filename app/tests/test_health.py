import importlib.util
import sys
from pathlib import Path

_MAIN_PATH = Path(__file__).resolve().parents[1] / "main.py"
_spec = importlib.util.spec_from_file_location("climate_control_main", _MAIN_PATH)
_module = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _module
_spec.loader.exec_module(_module)
app = _module.app

from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_returns_200():
    resp = client.get("/health")
    assert resp.status_code == 200


def test_health_reports_healthy_status():
    resp = client.get("/health")
    assert resp.json()["status"] == "healthy"
