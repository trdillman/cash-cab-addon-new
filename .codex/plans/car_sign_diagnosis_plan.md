# Car & Taxi Sign Diagnosis Plan (Headless)

## 1) Ground Truth – Asset-Only (Option A)
- Use `asset-car-fix/test_scripts/analyze_real_asset.py` headlessly.
- Confirm real `assets/ASSET_CAR.blend` hierarchy:
  - Car root, taxi sign child, CAR_TRAIL, curves.
- Observe how parenting and transforms behave when the asset is linked/instanced in a clean scene.
- Treat this as the reference for “correct” car/sign relationships and expected transform behavior.

## 2) True Pipeline Reproduction – Headless (Option B)
- Add `asset-car-fix/test_scripts/headless_route_import_and_diagnostics.py` that:
  - Enables `cash-cab-addon`.
  - Calls `bpy.ops.blosm.fetch_route_map(...)` with a small, controlled test route
    (or a cached/test configuration if available).
  - After the operator completes, calls `pipeline_taxi_sign_diagnostics.inspect_pipeline_state()` to log:
    - Car and taxi sign objects.
    - Parents, `matrix_world`, `matrix_parent_inverse`.
    - Distance-from-origin / obvious "stuck" behavior.
  - Optionally saves the resulting scene into `asset-car-fix/test_results/test_scenes/` for future comparison.
- Run entirely in background Blender (no UI), so it mirrors pressing the GUI "Fetch Route & Map" button.

## 3) Pinpoint the Failure Step
- Compare three perspectives:
  1. Pure asset behavior from Option A (clean, linked asset only).
  2. Post-import scene from the headless route-import run (real pipeline).
  3. Existing failure scenes in `asset-car-fix/test_results/test_scenes/`.
- Determine if the bug is primarily:
  - Parenting being cleared/rewired at some stage, or
  - Parenting preserved but transforms (`matrix_world`, `matrix_parent_inverse`, constraints) applied
    in a way that pins or offsets the taxi sign.

## 4) Propose Minimal Code-Change Options
- Based on the failure location, draft 1–2 **small, concrete** fixes, likely in:
  - `route/anim.py` (positioning logic), and/or
  - Asset append/instancing path (how ASSET_CAR is brought into the scene).
- Example fix directions:
  - Apply transforms on the correct hierarchy level while preserving existing parent/child + `matrix_parent_inverse`.
  - Avoid clearing parent or overwriting `matrix_parent_inverse` for ASSET_CAR children in the critical step.
- For each option, specify:
  - Exact code block(s) to change.
  - Expected impact on headless diagnostics from Step 2.
- Request explicit approval before modifying any addon code.

## 5) Implement & Re-Test Headlessly (After Approval)
- Apply the selected minimal fix.
- Re-run:
  - The headless route-import runner (Step 2).
  - The asset-only test (Step 1) to ensure no regressions.
  - Diagnostics against existing test scenes where relevant.
- Summarize:
  - Whether taxi signs now move with cars (positions and parent relationships),
    including simple distance metrics.
  - Any observable side effects.

## 6) Final User Verification
- After headless tests show expected behavior, ask you to:
  - Enable the updated addon in Blender UI.
  - Run your normal "Fetch Route & Map" workflow.
  - Visually verify that taxi signs now follow cars during route animation.