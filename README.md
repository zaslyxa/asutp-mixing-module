# ASUTP Mixing Module (Standalone)

Standalone mini-program for modeling a mixing process.  
This repository is prepared as an isolated module that can later be integrated into the main ASUTP project.

## Current status

The module includes:
- dry mixing CSTR-in-series simulation core (RTD-compatible reduced model);
- full wet model (components 1..N, moisture, PBM proxy eta, temperature);
- optional chemical reaction block with effects (heat release, precipitation, gas evolution);
- recipe-driven model selection (dry/wet);
- recipe save/load in JSON and YAML formats;
- MaterialConfig layer: component database (SQLite) + recipe scaling to model parameters;
- HomogenizationViz layer: online RSD/Lacey/H_rel metrics, endpoint prediction, OPC payload and report export;
- H(t) kinetics runtime with online/post-batch/predictive modes, historian storage, and CSV/PNG export;
- thermal channel dynamics per compartment;
- CLI runner for tank and cascade modes;
- Streamlit UI for process visualization;
- baseline tests and technical documentation.

## Quick start

1. Install Python 3.11+.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -e .[dev]
```

4. Run CLI demo (wet cascade):

```bash
python -m mixing_module.cli --model wet-cascade --seconds 120 --step 1 --cells 3 --tau 45 --kh 0.02 --components 3 --reaction
```

5. Run UI visualization:

```bash
pip install -e .[ui]
python -m streamlit run src/mixing_module/ui.py
```

In UI sidebar you can load and save recipe files (for example `recipes/my_recipe.yaml`).
For wet recipes, MaterialConfig computes effective mixture properties and auto-scales model parameters (`tau`, `kh`, `Ka`, `b_q`) from material data.
HomogenizationViz widgets are available in wet mode: gauges, trends, profile, what-if prediction, OPC payload preview, and report export.
The H(t) chart supports online monitoring, historical batch overlay, and predictive what-if scenarios.

6. Run tests:

```bash
pytest -q
```

## Mathematical basis

The repository now documents the mathematical apparatus from the provided technical specifications:
- model hierarchy DEM/KTGF/PDE/RTD/PBM;
- reduced state-space equations for dry and wet regimes (`c`, `w`, `eta`);
- assumptions and applicability limits for control use-cases.

See:
- `docs/mathematical-apparatus.md`
- `docs/error-check-report.md`

## Module scope (next milestones)

- input stream flow rates and temperatures;
- concentration and temperature tracking by compartments;
- recipe-level persistence and import/export;
- extension points for control-loop integration.

## Planned next steps

- add RTD identification and parameter calibration tools;
- add export of simulated trajectories for ASUTP integration tests;
- connect model-choice logic to external recipe storage.
