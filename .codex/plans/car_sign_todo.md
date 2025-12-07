# Car & Taxi Sign Diagnosis – TODO

- [x] Read existing asset-car-fix documentation and progress reports.
- [x] Run and fix `analyze_real_asset.py` to inspect `ASSET_CAR.blend` in isolation.
- [x] Create `pipeline_taxi_sign_diagnostics.py` to inspect car/sign state in arbitrary scenes.
- [x] Add `headless_route_import_and_diagnostics.py` to:
  - enable `cash-cab-addon`,
  - call `bpy.ops.blosm.fetch_route_map(...)` with a controlled test route,
  - then run both `pipeline_taxi_sign_diagnostics` and `animation_follow_diagnostics`.
- [x] Run the headless route-import diagnostic and capture logs.
- [x] Compare asset-only, headless-import, and saved failure scenes to locate the failure step.
- [x] Implement asset-level fix script to clean up taxi sign transforms in `assets/ASSET_CAR.blend` (with backup).
- [x] Implement runtime workaround in `route/anim.py` to repair broken taxi sign transforms at import time.
- [ ] Re-run headless route import + diagnostics to verify car/sign behavior (currently still failing sign follow; needs tuning).
- [ ] Prepare a short verification guide for final manual UI testing in Blender.