# ASUTP Mixing Module (Standalone)

Standalone mini-program for modeling a mixing process.  
This repository is prepared as an isolated module that can later be integrated into the main ASUTP project.

## Current status

Initial project scaffold is ready:
- core simulation domain model;
- deterministic simulation runner;
- simple CLI entry point;
- baseline unit tests.

## Quick start

1. Install Python 3.11+.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -e .[dev]
```

4. Run CLI demo:

```bash
python -m mixing_module.cli --seconds 30 --step 0.5
```

5. Run tests:

```bash
pytest -q
```

## Module scope (to be finalized by technical specification)

- input stream flow rates and temperatures;
- tank volume and concentration tracking over time;
- simple quality check for target concentration;
- extension points for control-loop integration.

## Planned next steps

- formalize equations and constraints from technical specification;
- add configuration file support and scenario presets;
- add charts/export for simulation results.
