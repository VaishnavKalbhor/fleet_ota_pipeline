import importlib.util
import os
import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_APP_DIR))

os.environ["APP_VERSION"] = "2.3.4"

_spec = importlib.util.spec_from_file_location("climate_control_main_v", _APP_DIR / "main.py")
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


def test_version_reflects_app_version_env_var():
    resp = client.get("/version")
    assert resp.json()["version"] == "2.3.4"
