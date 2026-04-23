import importlib.util
import sys
from pathlib import Path

_MAIN_PATH = Path(__file__).resolve().parents[1] / "main.py"
_spec = importlib.util.spec_from_file_location("climate_control_main_v", _MAIN_PATH)
_module = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _module
_spec.loader.exec_module(_module)
app = _module.app

from fastapi.testclient import TestClient

client = TestClient(app)


def test_version_returns_version_field():
    resp = client.get("/version")
    assert resp.status_code == 200
    assert "version" in resp.json()


def test_version_returns_service_name():
    resp = client.get("/version")
    assert resp.json()["service"] == "climate-control"
