"""
Toy experiment: given a fleet size and a rollout percentage, how many
vehicles should get the update in this wave?
"""


def wave_size(fleet_size: int, percentage: float) -> int:
    return int(fleet_size * percentage)


if __name__ == "__main__":
    fleet_size = 10
    for pct in [0.05, 0.25, 1.0]:
        print(f"{pct * 100:.0f}% wave -> {wave_size(fleet_size, pct)} vehicles")
