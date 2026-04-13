# Error Check Report

This report compares the initial scaffold with the provided technical specifications.

## Findings

1. **Model fidelity gap (fixed)**
   - Initial implementation had a single ideal tank with no compartment chain.
   - Specification requires CSTR-in-series (RTD-consistent) dynamics with `n` cells.
   - Fixed by adding `run_dry_cascade()` with configurable `cells`, `tau`, and `kh`.

2. **Missing thermal channel (fixed)**
   - Initial model tracked only concentration and volume.
   - Specification explicitly includes thermal dynamics (`T_in`, `T_wall`, `kh`).
   - Fixed in new cascade model and CLI/UI outputs.

3. **No process visualization UI (fixed)**
   - Initial scaffold had CLI only.
   - Added Streamlit UI with:
     - concentration vs time by cell;
     - temperature vs time by cell;
     - cell profile snapshot for selected time.

4. **Time discretization edge case (known)**
   - Legacy tank model uses integer step truncation for non-divisible `duration/dt`.
   - New cascade model uses rounded step count; if strict final-time matching is required,
     implement variable last-step integration.

5. **Wet PBM dynamics gap (fixed at model level)**
   - Specification requires wet blocks (`w`, `eta`, `Ka`, `Kb`, `qL`, `j_add`) with reaction-sensitive behavior.
   - Implemented in `run_wet_cascade()` with:
     - component-wise states (`component_1..N`);
     - moisture and reduced PBM quality channel (`eta`);
     - injection zone `j_add` and wet gains (`b_q`, `Ka`, `Kb`);
     - optional reaction effects (heat release, precipitation, gas evolution).
   - Remaining work is production-grade identification/observer tuning, not the structural model itself.

## Conclusion

Critical structural mismatches for dry/wet simulation and visualization are resolved.
Residual risks are now mostly related to calibration quality and plant-data identification.
