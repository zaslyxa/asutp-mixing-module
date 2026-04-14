# ASUTP Mixing Module: User Guide

## 1) What this application does

ASUTP Mixing Module is a desktop/web tool for:
- recipe-driven dry and wet mixing simulation,
- material-based parameter scaling (`MaterialConfig`),
- homogenization quality analysis (`H(t)`, `RSD`, `Lacey`, `H_rel`),
- integration payload preparation (OPC/MQTT),
- export of reports and release evidence artifacts.

---

## 2) System requirements

- Windows 10/11 x64
- Python 3.11+ (only if you run from source)
- Optional for installer build (developers): Inno Setup 6

---

## 3) Installation options

### Option A: Install with setup `.exe` (recommended for operators)

1. Get installer file:
   - `asutp-mixing-module-setup.exe`
2. Run installer.
3. Follow wizard steps:
   - choose install directory,
   - choose whether to create desktop shortcut.
4. Finish and launch application.

### Option B: Portable EXE (no installer)

1. Get file:
   - `asutp-mixing-module.exe`
2. Place it in a working folder (for example `C:\ASUTP\MixingModule`).
3. Run executable directly.

### Option C: Run from source (engineering/debug mode)

```bash
pip install -e .[ui]
python -m streamlit run src/mixing_module/ui.py
```

---

## 4) First launch checklist

1. Open the app.
2. In sidebar:
   - choose recipe (`Dry mixing` or `Wet mixing`),
   - choose layout mode (`Desktop`, `Balanced`, `Focus charts`).
3. In left panel (`MaterialConfig`):
   - select components and masses,
   - verify risk tags in component card.
4. In right panel:
   - configure process parameters,
   - run analysis in `HomogenizationViz`,
   - check status messages and KPI strip.

---

## 5) Daily workflow (recommended)

## Step 1: Configure recipe

- Load existing recipe (`.json` / `.yaml`) from sidebar.
- Or configure parameters manually.
- Save recipe when ready.

## Step 2: Configure materials

- In `MaterialConfig`, select materials from catalog.
- Enter mass for each component.
- Enable `Use auto scaling` if required.
- Review:
  - effective mixture properties,
  - warnings,
  - component risk card.

## Step 3: Run process model

- For `Dry mixing`: review concentration and temperature dynamics.
- For `Wet mixing`: review outlet channels and temperature.
- In `HomogenizationViz`, monitor:
  - `H(t)`,
  - `RSD(t)`,
  - target ETA,
  - confidence,
  - trend/drift statuses.

## Step 4: Integration and export

Open `Integration` tab to:
- validate OPC payload schema,
- inspect MQTT topics,
- simulate publish bundle,
- export report,
- export `H`-curve CSV/PNG,
- export release evidence ZIP.

---

## 6) Recipe and revision management

- `Save current recipe to file` stores active configuration.
- `Save revision snapshot` / `Save full recipe revision` stores history.
- `Recipe revision history` lets you:
  - load previous revision,
  - diff revision with current state,
  - generate recipe changelog markdown.

---

## 7) Threshold profiles and alarms

In sidebar `Risk thresholds editor`:
- choose profile (`normal`, `conservative`, `aggressive`, `custom`),
- apply/reset/export/import thresholds,
- save to `config/viz_params.yaml`.

App validates thresholds at startup and reports invalid values.

---

## 8) Output artifacts and where to find them

- Reports: `reports/`
- Historian DB: `config/historian.db`
- Material DB: `config/materials.db`
- Recipe cache: `config/recipe_cache.json`
- Recipe revisions: `config/recipe_versions/`
- Release evidence ZIP: `reports/release-evidence-*.zip`

---

## 9) Silent installation (for IT deployment)

```powershell
asutp-mixing-module-setup.exe /VERYSILENT /NORESTART /SP- /SUPPRESSMSGBOXES
```

Custom install path:

```powershell
asutp-mixing-module-setup.exe /VERYSILENT /DIR="C:\ASUTP\MixingModule"
```

---

## 10) Troubleshooting

## App does not start
- Check antivirus restrictions and Windows SmartScreen prompts.
- Ensure all app files are in place (`config`, `docs`, executable).

## Empty charts or invalid metrics
- Verify component masses are non-zero.
- Verify recipe and model match process type (dry vs wet).

## Payload validation errors
- Open `Integration` tab and inspect missing keys.
- Ensure `schema_version` is set and required fields are present.

## Config validation errors at startup
- Open `config/viz_params.yaml`.
- Fix invalid ranges or click threshold reset in UI.

---

## 11) Update procedure

### For installer deployment
1. Close running app.
2. Run new installer.
3. Install to same directory.
4. Launch and verify config migration message.

### For portable EXE
1. Replace executable file.
2. Keep existing `config/` and `reports/`.
3. Launch and verify startup validations.

