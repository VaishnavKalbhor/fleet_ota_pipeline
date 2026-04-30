"""
Toy experiment: given a fleet size and a rollout percentage, how many
vehicles should get the update in this wave?

v1 of this used plain int(fleet_size * percentage), which meant a 5% wave
against a 10-vehicle fleet computed int(0.5) == 0 -- the canary wave would
update nobody. See docs/mistakes-log.md.
"""


def wave_size(fleet_size: int, percentage: float) -> int:
    calculated = int(fleet_size * percentage)
    if percentage > 0:
        return max(1, calculated)
    return calculated


if __name__ == "__main__":
    fleet_size = 10
    for pct in [0.05, 0.25, 1.0]:
        print(f"{pct * 100:.0f}% wave -> {wave_size(fleet_size, pct)} vehicles")
