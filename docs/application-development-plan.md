# Application Development Plan (No-Code Scope)

## Goal
Create a production-grade desktop application around the existing mixing module, distributed as Windows EXE, with clear UX, telemetry integration, and validation workflows.

## Phase 1: Product Definition (1-2 weeks)
- Finalize operator personas (technologist, process engineer, shift operator).
- Define usage scenarios: recipe setup, online monitoring, post-batch analysis, integration export.
- Freeze MVP requirements and acceptance criteria for each scenario.
- Agree non-functional targets: startup time, data persistence, offline mode, traceability.

## Phase 2: Architecture and Packaging (1-2 weeks)
- Choose desktop shell strategy:
  - A) Streamlit-based EXE (fast path),
  - B) Dedicated desktop shell (PySide/Tauri/Electron) for advanced UX.
- Define app boundaries: simulation core, UI layer, integration layer, persistence.
- Formalize schema versions for recipe, thresholds, payloads, evidence bundle.
- Set packaging pipeline (PyInstaller build + optional installer wrapper like Inno Setup).

## Phase 3: UX and Workflow Hardening (2-4 weeks)
- Stabilize layout modes and role-based presets.
- Add guided workflow states: Draft -> Validated -> Production-ready.
- Add guardrails:
  - validation before run,
  - validation before export/publish,
  - explicit alarm handling flow.
- Implement structured notifications and operator action logs.

## Phase 4: Data and Version Governance (2-3 weeks)
- Add robust revisioning for recipes and thresholds (history, compare, rollback).
- Add changelog generation and evidence bundle as standard release artifacts.
- Introduce metadata: author, reason, environment, approval status.
- Add integrity checks for serialized configs and payloads.

## Phase 5: Integration and Runtime Reliability (2-4 weeks)
- Harden MQTT/OPC contracts with schema checks and backward compatibility rules.
- Add publish dry-run and replay tools.
- Add runtime health panel (latency, dropped samples, historian write status).
- Add baseline drift monitoring and confidence diagnostics for long campaigns.

## Phase 6: QA and Release Management (2-3 weeks)
- Expand automated tests:
  - domain/unit,
  - config migration,
  - export/integration snapshots,
  - UI smoke tests.
- Add CI pipeline for test + artifact build + release evidence packaging.
- Define release checklist and rollback playbook.
- Run pilot with representative recipes and acceptance protocol.

## EXE Delivery Plan
- Step 1: Ship single-file EXE for pilot (`scripts/build_exe.ps1`).
- Step 2: Add signed installer (Inno Setup or MSIX), desktop/start-menu shortcuts.
- Step 3: Add auto-update channel (optional), version pinning, and migration guardrails.

## Risks and Mitigations
- UI framework limits for heavy desktop UX -> keep shell abstraction and plan optional migration.
- Config drift across machines -> enforce migration/validation at startup.
- Integration regressions -> snapshot tests for contracts and payload schemas.
- Operational misuse -> onboarding, validation gates, and evidence-first workflow.
