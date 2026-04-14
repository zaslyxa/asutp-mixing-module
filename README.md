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

## Build Windows EXE

1. Install packaging dependencies:

```bash
pip install -e .[ui,packaging]
```

2. Build single-file executable (PowerShell):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_exe.ps1 -Clean
```

3. Result:
- `dist/asutp-mixing-module.exe`

The EXE starts the Streamlit UI launcher and uses local `config/` and `reports/` folders in the runtime directory.

## Build Windows Installer (.exe setup)

1. Install [Inno Setup 6](https://jrsoftware.org/isinfo.php).
2. Build installer (includes EXE build by default):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_installer.ps1
```

Optional (if EXE is already built):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_installer.ps1 -SkipExeBuild
```

3. Result:
- `dist/asutp-mixing-module-setup.exe`

Installer includes:
- app executable,
- `config/` defaults,
- `docs/` reference files,
- start menu shortcut and optional desktop shortcut.

### Installer versioning

- Installer version is auto-read from `pyproject.toml` (`project.version`).
- Optional manual override:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_installer.ps1 -Version 0.2.0
```

### Code signing (optional)

If you have a code-signing certificate (`.pfx`):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_installer.ps1 `
  -CertFile "C:\secure\codesign.pfx" `
  -CertPassword "YOUR_PASSWORD"
```

Optional parameters:
- `-SignToolPath` to specify `signtool.exe` explicitly,
- `-TimestampUrl` to use a custom timestamp server.

The script signs both `dist/asutp-mixing-module.exe` and `dist/asutp-mixing-module-setup.exe`.
Before signing, the script validates the certificate validity period and fails early if the certificate is expired or not yet valid.

### Silent install

For unattended deployment:

```powershell
dist\asutp-mixing-module-setup.exe /VERYSILENT /NORESTART /SP- /SUPPRESSMSGBOXES
```

Optional custom install directory:

```powershell
dist\asutp-mixing-module-setup.exe /VERYSILENT /DIR="C:\ASUTP\MixingModule"
```

### CI nightly build template

A ready workflow template is included at:
- `.github/workflows/nightly-build.yml`

It runs on Windows nightly (and manually), executes tests, builds EXE + installer, and uploads artifacts.

For signed builds in CI, set repository secrets:
- `WIN_CODESIGN_PFX_BASE64` (base64-encoded `.pfx`),
- `WIN_CODESIGN_PFX_PASSWORD`.

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
