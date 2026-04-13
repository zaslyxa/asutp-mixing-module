from __future__ import annotations

import argparse

from .simulator import SimulationConfig, run_simulation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run simple mixing process simulation")
    parser.add_argument("--seconds", type=float, default=60.0, help="simulation duration, s")
    parser.add_argument("--step", type=float, default=1.0, help="time step, s")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    cfg = SimulationConfig(duration_s=args.seconds, dt_s=args.step)
    points = run_simulation(cfg)
    last = points[-1]
    print(
        "simulation complete: "
        f"time={last.time_s:.1f}s, concentration={last.concentration:.4f}, volume={last.volume_m3:.3f}m3"
    )


if __name__ == "__main__":
    main()
