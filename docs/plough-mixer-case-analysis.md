# Plough Mixer Case Analysis (Specified Recipe)

## Input case

- Mixer: **plough mixer**
- Volume `V=2.0 m3`, fill factor `phi=0.6`
- Loaded mass `M≈1440 kg`
- Shaft speed `n=30 rpm`, motor power `P=22 kW`
- RTD mean residence `tau=45 s`, cascade cells `n_cells=5`
- Recipe (mass share): cement 20%, sand 75%, hydrated lime 3%, SP-1 1%, silox 1%

## Added parameters to support this case

The following component parameters were added to model/data layer and UI:

- `rho_true` (true density, kg/m3)
- `friction_steel` (friction coefficient against steel)
- `rsd0` (initial segregation coefficient, %)

They are persisted in material DB and used in scaling.

## Simulation snapshot (current implementation)

Dry cascade + scaling run for this exact recipe/mixer setup produced:

- `k_mix_model ≈ 0.0690 1/s`
- `kh ≈ 0.0205 1/s`
- `rho_b_mix ≈ 1466.5 kg/m3`
- `rho_true_mix ≈ 2700.5 kg/m3`
- `friction_steel_mix ≈ 0.474`
- `rsd0_mix ≈ 100%`

H-kinetics runtime approximation (180 s horizon) for plough setup:

- `H_end ≈ 0.950`
- `k_mix_end ≈ 0.401`
- target `H_target=0.95` reached by end of run
- estimated remaining time to target: near zero at 180 s

## Interpretation

- The selected plough setup is sufficient to reach quality target around current cycle time.
- Dominant sensitivity remains to shaft speed and initial segregation (`rsd0`).
- With the provided recipe proportions, inertial sand fraction requires enough circulation intensity; plough geometry with `n=30 rpm` is within feasible range for this reduced model.

## Caveats

- This is a reduced engineering model, not DEM-level particle dynamics.
- Absolute values should be treated as calibrated indicators, while trend/relative changes are more reliable.
- For production deployment, calibration against plant samples is still required.
