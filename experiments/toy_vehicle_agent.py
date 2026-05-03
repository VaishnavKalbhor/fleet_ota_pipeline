"""
Toy experiment: simulate one ECU polling for updates against a fake
(hardcoded) server response, with no real HTTP involved yet. Goal is to
learn the polling loop / version comparison / retry shape before wiring up
a real update server (Week 4).
"""
import time


def fake_server_response(poll_count: int) -> dict:
    """Pretends to be the update server. Ships a new version on the 3rd poll."""
    if poll_count >= 3:
        return {"version": "1.1.0", "image": "climate-control:1.1.0"}
    return {"version": "1.0.0", "image": "climate-control:1.0.0"}


def apply_update(target: dict) -> bool:
    print(f"  Downloading {target['image']}...")
    print(f"  Applying {target['image']}...")
    return True  # toy version always "succeeds"


def run(max_polls: int = 5, poll_interval_seconds: float = 0.0):
    current_version = "1.0.0"
    poll_count = 0

    while poll_count < max_polls:
        poll_count += 1
        latest = fake_server_response(poll_count)
        print(f"Poll {poll_count}: current={current_version}, latest={latest['version']}")

        if latest["version"] != current_version:
            success = apply_update(latest)
            if success:
                current_version = latest["version"]
                print(f"  Update applied. Now running {current_version}.")
            else:
                print("  Update failed, staying on current version, will retry next poll.")

        time.sleep(poll_interval_seconds)

    return current_version


if __name__ == "__main__":
    final_version = run()
    print(f"\nFinal version after {5} polls: {final_version}")
