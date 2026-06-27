import importlib.util
import sys
from pathlib import Path

import pytest

_SERVER_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_SERVER_DIR))

_spec = importlib.util.spec_from_file_location(
    "update_server_main", _SERVER_DIR / "main.py"
)
update_server_main = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(update_server_main)

from fastapi.testclient import TestClient

client = TestClient(update_server_main.app)


@pytest.fixture(autouse=True)
def reset_state():
    update_server_main._reset_for_tests()
    yield
    update_server_main._reset_for_tests()


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_get_manifest_returns_default():
    resp = client.get("/manifest")
    assert resp.status_code == 200
    assert resp.json()["target_version"] == "1.0.0"


def test_set_manifest_updates_target_version():
    resp = client.post("/manifest", json={"target_version": "1.2.0"})
    assert resp.status_code == 200
    assert resp.json()["target_version"] == "1.2.0"

    resp = client.get("/manifest")
    assert resp.json()["target_version"] == "1.2.0"


def test_set_manifest_requires_target_version():
    resp = client.post("/manifest", json={"image": "climate-control:2.0.0"})
    assert resp.status_code == 422


def test_telemetry_report_is_stored():
    resp = client.post(
        "/telemetry",
        json={"vehicle_id": "vehicle-01", "current_version": "1.0.0", "status": "healthy"},
    )
    assert resp.status_code == 200

    resp = client.get("/fleet/status")
    body = resp.json()
    assert body["fleet_size"] == 1
    assert body["vehicles"]["vehicle-01"]["current_version"] == "1.0.0"
    assert body["vehicles"]["vehicle-01"]["status"] == "healthy"
    assert "last_seen" in body["vehicles"]["vehicle-01"]


def test_telemetry_requires_all_fields():
    resp = client.post("/telemetry", json={"vehicle_id": "vehicle-01"})
    assert resp.status_code == 422


def test_fleet_status_aggregates_multiple_vehicles():
    for i in range(3):
        client.post(
            "/telemetry",
            json={
                "vehicle_id": f"vehicle-0{i}",
                "current_version": "1.0.0",
                "status": "healthy",
            },
        )
    resp = client.get("/fleet/status")
    assert resp.json()["fleet_size"] == 3


def test_repeated_telemetry_from_same_vehicle_overwrites_not_duplicates():
    client.post(
        "/telemetry",
        json={"vehicle_id": "vehicle-05", "current_version": "1.0.0", "status": "healthy"},
    )
    client.post(
        "/telemetry",
        json={"vehicle_id": "vehicle-05", "current_version": "1.2.0", "status": "updating"},
    )
    resp = client.get("/fleet/status")
    body = resp.json()
    assert body["fleet_size"] == 1
    assert body["vehicles"]["vehicle-05"]["current_version"] == "1.2.0"


def test_events_can_be_recorded_and_listed():
    resp = client.post("/events", json={"event": "wave_started", "wave_percentage": 0.05})
    assert resp.status_code == 200

    resp = client.get("/events")
    body = resp.json()
    assert len(body["events"]) == 1
    assert body["events"][0]["event"] == "wave_started"
    assert "recorded_at" in body["events"][0]


def test_events_require_event_field():
    resp = client.post("/events", json={"wave_percentage": 0.05})
    assert resp.status_code == 422


def test_events_list_preserves_order():
    client.post("/events", json={"event": "wave_started"})
    client.post("/events", json={"event": "wave_promoted"})
    client.post("/events", json={"event": "rollout_complete"})

    resp = client.get("/events")
    names = [e["event"] for e in resp.json()["events"]]
    assert names == ["wave_started", "wave_promoted", "rollout_complete"]
