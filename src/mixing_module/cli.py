from __future__ import annotations

import argparse

from .cascade import DryCascadeConfig, run_dry_cascade
from .simulator import SimulationConfig, run_simulation
from .wet_model import WetCascadeConfig, run_wet_cascade


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run simple mixing process simulation")
    parser.add_argument("--model", choices=("tank", "dry-cascade", "wet-cascade"), default="dry-cascade")
    parser.add_argument("--seconds", type=float, default=60.0, help="simulation duration, s")
    parser.add_argument("--step", type=float, default=1.0, help="time step, s")
    parser.add_argument("--cells", type=int, default=3, help="number of cascade cells")
    parser.add_argument("--tau", type=float, default=45.0, help="mean residence time, s")
    parser.add_argument("--kh", type=float, default=0.02, help="wall heat exchange coefficient")
    parser.add_argument("--components", type=int, default=2, help="number of recipe components (wet)")
    parser.add_argument("--reaction", action="store_true", help="enable reaction block (wet)")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.model == "tank":
        cfg = SimulationConfig(duration_s=args.seconds, dt_s=args.step)
        points = run_simulation(cfg)
        last = points[-1]
        print(
            "tank model complete: "
            f"time={last.time_s:.1f}s, concentration={last.concentration:.4f}, volume={last.volume_m3:.3f}m3"
        )
        return

    if args.model == "dry-cascade":
        cfg = DryCascadeConfig(
            duration_s=args.seconds,
            dt_s=args.step,
            cells=args.cells,
            tau_s=args.tau,
            kh=args.kh,
        )
        points = run_dry_cascade(cfg)
        last = points[-1]
        print(
            "dry-cascade model complete: "
            f"time={last.time_s:.1f}s, c_out={last.concentrations[-1]:.4f}, T_out={last.temperatures[-1]:.2f}C"
        )
        return

    inlet = tuple(1.0 if i == 0 else 0.0 for i in range(args.components))
    initial = tuple(0.0 for _ in range(args.components))
    cfg = WetCascadeConfig(
        duration_s=args.seconds,
        dt_s=args.step,
        cells=args.cells,
        tau_s=args.tau,
        kh=args.kh,
        component_inlet=inlet,
        component_initial=initial,
        reaction_enabled=args.reaction,
        reaction_rate=0.05 if args.reaction else 0.0,
        effect_heat_release=args.reaction,
    )
    points = run_wet_cascade(cfg)
    last = points[-1]
    print(
        "wet-cascade model complete: "
        f"time={last.time_s:.1f}s, comp1_out={last.components[-1][0]:.4f}, "
        f"w_out={last.moisture[-1]:.4f}, eta_out={last.eta[-1]:.4f}, T_out={last.temperatures[-1]:.2f}C"
    )


if __name__ == "__main__":
    main()
