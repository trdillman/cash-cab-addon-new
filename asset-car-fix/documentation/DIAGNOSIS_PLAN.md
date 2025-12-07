# Diagnosis Plan – Car & Taxi Sign Parenting Issue

## Goals
- Independently diagnose why taxi signs do not follow their parent cars during route import.
- Minimize time-to-signal by using short, targeted experiments.
- Avoid relying on prior failed assumptions or unverified “fix” code.

## Ground Rules
- No production code changes until you explicitly approve an option below.
- Treat all existing “implementation ready” scripts and prior conclusions as suspect.
- Prefer simple, observable tests in Blender over complex theory.

## Key Questions to Answer
- Does the ASSET_CAR asset have the expected internal parent–child hierarchy (car → taxi sign) in a clean Blender session?
- At what point in the CashCab route pipeline does the hierarchy or transform start to diverge from expectations?
- Is the issue caused by:
  - parenting being broken/overwritten, or
  - transforms (matrices, constraints) being applied in a way that effectively pins the sign?

---

## Option A – Asset-First, Environment-Light (Recommended Starting Point)

**Goal:** Establish “ground truth” about the car/sign asset in isolation, then probe how the addon uses it.

**Steps:**
- Open ASSET_CAR (or equivalent) `.blend` directly in a clean Blender session (no CashCab addon).
- Inspect object hierarchy:
  - Identify car root object, taxi sign object, and their parent–child relationship.
  - Note any constraints or drivers on the taxi sign.
- Perform manual tests:
  - Move/rotate the car root and confirm the taxi sign follows as expected.
  - Apply a few matrix transforms in the Python console to verify `matrix_world` behavior.
- Capture findings:
  - Save short notes (hierarchy, constraints, expected behavior) in a new summary doc.

**Pros:**
- Very fast signal on whether the asset itself is well-formed.
- No addon complexity; easier to see pure Blender behavior.

**Cons:**
- Does not yet show where in the CashCab pipeline things go wrong.

**What I would need from you to run this:**
- Path to the real ASSET_CAR `.blend` (or confirmation of its location if already known).
- Permission to use a clean Blender session (no addon) for the initial asset check.

---

## Option B – Minimal Reproduction Inside CashCab (Targeted Pipeline Probe)

**Goal:** Identify the exact pipeline stage where parenting/transform behavior diverges by using a minimal script that mimics the route import, without editing addon code.

**Steps:**
- Create or reuse a small test route and asset configuration that reproduces the bug quickly.
- Write a minimal test script (in `asset-car-fix/test_scripts/`) that:
  - Starts Blender with the CashCab addon enabled.
  - Invokes the same operator(s) the user normally uses to import a route with the car/sign.
  - After each key pipeline step (e.g., asset spawn, placement, animation setup), logs:
    - The car and taxi sign objects.
    - Their `parent`, `matrix_world`, and `matrix_parent_inverse`.
  - Optionally saves a small `.blend` snapshot after the “spawned but before animation” step.
- Run the script in background mode and inspect:
  - When does the sign stop following the car (spawn vs after anim vs after constraints)?
  - Is the parent cleared, or are transforms applied in a way that isolates the sign?

**Pros:**
- Directly exercises the real pipeline without modifying its code.
- Produces concrete logs and/or scenes that pinpoint the failing stage.

**Cons:**
- Slightly more setup than Option A.
- Requires Blender background runs and log inspection.

**What I would need from you to run this:**
- The exact operator (or UI action) you currently use to import routes.
- Confirmation that I may add a new diagnostic test script under `asset-car-fix/test_scripts/` and run it via background Blender.

---

## Option C – Scripted Transform Experiments (Matrix/Parenting Focus)

**Goal:** Rapidly test how different parent/transform sequences (with and without clearing parents) affect the car/sign pair, without touching production code.

**Steps:**
- Duplicate or load a simple scene with one car/sign pair in CashCab’s environment.
- Write a small diagnostic script that:
  - Locates the car and taxi sign objects.
  - Runs a series of scripted experiments:
    - Apply `matrix_world` changes with parents intact.
    - Clear parent (`parent = None`, reset `matrix_parent_inverse`), then apply transforms.
    - Re-parent and re-apply transforms.
  - Logs resulting world positions and hierarchy for each experiment.
- Compare results against behavior observed in the “working” addon version (if accessible).

**Pros:**
- Focused directly on the suspected matrix/parenting interaction.
- Uses short, fast scripts; easy to iterate.

**Cons:**
- Still within the complex addon environment; may conflate root cause with environment issues.
- Requires careful interpretation of matrix math and logs.

**What I would need from you to run this:**
- Permission to add a new diagnostic script (e.g., `diagnostic_parenting_experiments.py`) under `asset-car-fix/test_scripts/`.
- A known scene or simple setup that reliably shows the bug.

---

## Recommended Path & Next Step

**Suggested sequence for speed and clarity:**
1. **Start with Option A** to confirm the asset’s intended hierarchy and behavior in isolation.
2. **Then Option B** to pinpoint the pipeline step that breaks or misapplies parenting/transform logic.
3. Use insights from A+B to decide whether Option C (deeper scripted experiments) is necessary.

---

## Approval Request

Please confirm:
- Which option(s) you want me to execute first (A, B, C, or a combination).
- That you approve:
  - Adding new diagnostic scripts under `asset-car-fix/test_scripts/` (no changes to core addon code yet).
  - Running Blender in background mode with these scripts for logging and scene snapshots.

Once you select an option, I’ll proceed with that diagnostic path and report back findings before proposing any code changes to the addon itself.

