# Mathematical Apparatus and Model Basis

This module is based on the technical documents:
- "Models of mixing of dry and wet granular materials: from PDE/PBM to transfer matrices";
- "Technical description, mathematical models and development specification for a model-based control module".

## Modeling hierarchy (from detailed physics to control-ready model)

The source documentation describes a standard hierarchy:
- **DEM**: particle-level contact/capillary mechanics;
- **KTGF**: continuum granular flow for fast collision-driven regimes;
- **Axial dispersion PDE**: scalar transport for concentration/moisture/temperature;
- **CSTR-in-series (RTD reduction)**: control-oriented state-space model;
- **PBM/PBE**: wet granulation quality dynamics (particle-size evolution).

For real-time control and simulation UI, this repository uses the **CSTR-in-series reduction**, because it gives compact and identifiable linear dynamics.

## Dry mixing model used in code

For `n` cells and mean residence time `tau`:
- `k = n / tau`
- concentration dynamics:
  - `dc1/dt = k * (c_in - c1)`
  - `dci/dt = k * (c_{i-1} - ci)`, `i = 2..n`
- temperature dynamics:
  - `dT1/dt = k * (T_in - T1) + kh * (T_wall - T1)`
  - `dTi/dt = k * (T_{i-1} - Ti) + kh * (T_wall - Ti)`, `i = 2..n`

This corresponds to the reduced transfer/state-space representation from the specification and is suitable for further MPC/observer extensions.

## Wet mixing extension described in specification

The second document defines a wet model (`w < 60%`) with states:
- concentration chain `c_1..c_n`;
- moisture chain `w_1..w_n`;
- reduced PBM quality proxy `eta_1..eta_n` (zero moment deviation).

Coupling is moisture-to-quality through effective agglomeration terms (`Ka`, `Kb`, `w*`), with liquid injection into configurable zone `j_add`.

Implemented wet dynamics include:
- `component_1..N` transport across cells;
- moisture transport with liquid injection source (`qL`, `b_q`, `j_add`);
- reduced PBM-like quality state `eta` with agglomeration/breakage terms;
- optional chemical reaction block with configurable effects:
  - heat release (temperature source term),
  - precipitation (additional `eta` sink),
  - gas evolution (moisture stripping term).

## Assumptions and applicability limits

- Linearization is local around an operating point.
- Parameters (`k`, `kh`, `Ka`, `Kb`, `Pe`, `D`) are regime-dependent and must be identified.
- Strong regime transitions (for example, moisture-driven pendular to funicular changes) require re-identification or LPV adaptation.
- 1D compartment models do not explicitly resolve radial segregation.
