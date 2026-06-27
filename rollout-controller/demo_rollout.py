import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from controller import run_staged_rollout
import json

def healthy(n):
    return [{"vehicle_id": f"v{i}", "status": "healthy"} for i in range(n)]

print("=== Scenario 1: Healthy rollout (20-vehicle fleet, 1.2.0 -> 1.3.0) ===")
events, status = run_staged_rollout(
    fleet_size=20,
    target_version="1.3.0",
    previous_version="1.2.0",
    security_scan_passed=True,
    telemetry_by_wave=[healthy(1), healthy(5), healthy(20)],
)
print(f"final status: {status}\n")
for e in events:
    print(json.dumps(e))

print("\n=== Scenario 2: Broken canary triggers rollback (20-vehicle fleet, 1.2.0 -> 1.3.0) ===")
events, status = run_staged_rollout(
    fleet_size=20,
    target_version="1.3.0",
    previous_version="1.2.0",
    security_scan_passed=True,
    telemetry_by_wave=[[{"vehicle_id": "v0", "status": "crash"}]],
)
print(f"final status: {status}\n")
for e in events:
    print(json.dumps(e))

print("\n=== Scenario 3: Security scan failure blocks promotion after a healthy canary ===")
events, status = run_staged_rollout(
    fleet_size=20,
    target_version="1.3.0",
    previous_version="1.2.0",
    security_scan_passed=False,
    telemetry_by_wave=[healthy(1)],
)
print(f"final status: {status}\n")
for e in events:
    print(json.dumps(e))
