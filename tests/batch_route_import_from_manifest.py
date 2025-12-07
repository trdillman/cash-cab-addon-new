"""
Batch Route Import from Manifest
================================

Reads a manifest text file that lists many Cash Cab map tasks and, for each
entry, performs a full "Fetch Route & Map" import into its own .blend file.

Expected manifest format (one entry per line, comments allowed):
  [TASKID][Pickup Address - Dropoff Address][yymmdd(#YYYY-MM-DD)]-V01

Example:
  [CC10079][18 Yorkville Ave - 1006 Bloor St W][251208(#2025-12-08)]-V01

Usage (from this addon folder):

  blender -b --python batch_route_import_from_manifest.py -- \\
      "C:\\path\\to\\DECEMBER_8.txt" \\
      "C:\\path\\to\\output_folder"

If output_folder is omitted, .blend files are written next to the manifest.

Each entry produces an individual .blend file named:
  {TASKID}_{pickup_slug}_to_{dropoff_slug}.blend
"""

import bpy
import sys
from pathlib import Path
from typing import List, Optional, Tuple


# -----------------------------------------------------------------------------
# Parsing helpers
# -----------------------------------------------------------------------------

def _slugify(text: str) -> str:
    """Turn an address string into a safe filename fragment."""
    keep = []
    for ch in text.strip():
        if ch.isalnum():
            keep.append(ch)
        elif ch in {" ", "-", "_"}:
            keep.append("_")
        # else drop punctuation
    slug = "".join(keep).strip("_")
    return slug or "route"


def parse_manifest_line(line: str) -> Optional[Tuple[str, str, str]]:
    """Parse one manifest line into (task_id, pickup, dropoff).

    Returns None for comments/blank lines or invalid entries.
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    # Strip trailing version suffix like -V01
    core = line
    if "-V" in line:
        core = line.rsplit("-V", 1)[0]

    # Split [A][B][C] into three parts
    if not (core.startswith("[") and core.endswith("]")):
        return None
    parts = core.split("][")
    if len(parts) < 2:
        return None

    task_id = parts[0].lstrip("[").strip()
    addr_block = parts[1].rstrip("]").strip()

    if " - " not in addr_block:
        return None
    pickup, dropoff = [p.strip() for p in addr_block.split(" - ", 1)]
    if not pickup or not dropoff:
        return None

    return task_id, pickup, dropoff


def read_manifest(path: Path) -> List[Tuple[str, str, str]]:
    entries: List[Tuple[str, str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        parsed = parse_manifest_line(raw)
        if parsed is not None:
            entries.append(parsed)
    return entries


# -----------------------------------------------------------------------------
# Blender / Addon bootstrap
# -----------------------------------------------------------------------------

def _load_addon_from_this_folder():
    """Load this folder as 'cash_cab_addon' and register it."""
    addon_dir = Path(__file__).resolve().parent
    init_path = addon_dir / "__init__.py"

    if not init_path.exists():
        raise RuntimeError(f"__init__.py not found at {init_path}")

    if "cash_cab_addon" in sys.modules:
        module = sys.modules["cash_cab_addon"]
    else:
        import importlib.util

        spec = importlib.util.spec_from_file_location("cash_cab_addon", init_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("Could not create module spec for cash_cab_addon")
        module = importlib.util.module_from_spec(spec)
        sys.modules["cash_cab_addon"] = module
        spec.loader.exec_module(module)

    # (Re)register addon to ensure operators and props exist
    try:
        module.register()
    except Exception:
        # If already registered, ignore
        pass
    return module


def _reset_to_empty_scene():
    """Reset Blender to a clean empty scene."""
    try:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    except Exception:
        # Fallback: delete all objects from current scene
        for obj in list(bpy.data.objects):
            try:
                bpy.data.objects.remove(obj, do_unlink=True)
            except Exception:
                pass


def _run_single_route(task_id: str, pickup: str, dropoff: str, out_path: Path):
    """Run Fetch Route & Map for a single route and save a .blend."""
    print(f"[BATCH] Processing {task_id}: {pickup} -> {dropoff}")

    _reset_to_empty_scene()

    scene = bpy.context.scene
    addon = getattr(scene, "blosm", None)
    if addon is None:
        print(f"[BATCH] ERROR: scene.blosm not found; is the addon registered?")
        return

    # Configure route addresses and import flags
    addon.route_start_address = pickup
    addon.route_end_address = dropoff
    addon.route_import_roads = True
    addon.route_import_buildings = True
    addon.route_create_preview_animation = True

    # Sensible animation defaults; user can tweak later
    try:
        scene.blosm_anim_start = 15
        scene.blosm_anim_end = 150
        scene.blosm_lead_frames = 1
    except Exception:
        pass

    # Run Fetch Route & Map
    print("[BATCH] Invoking BLOSM_OT_FetchRouteMap")
    try:
        res = bpy.ops.blosm.fetch_route_map("EXEC_DEFAULT")
        print(f"[BATCH] fetch_route_map result: {res}")
    except Exception as exc:
        print(f"[BATCH] ERROR running fetch_route_map: {exc}")
        return

    # Run finalizer + keyframes
    try:
        from cash_cab_addon.route import pipeline_finalizer as pf
        from cash_cab_addon.route import anim as route_anim
    except Exception as exc:
        print(f"[BATCH] ERROR importing route modules: {exc}")
        return

    try:
        pf_result = pf.run(scene)
        print(f"[BATCH] pipeline_finalizer.run keys: {sorted(pf_result.keys())}")
    except Exception as exc:
        print(f"[BATCH] ERROR running pipeline_finalizer.run: {exc}")

    try:
        route_anim.force_follow_keyframes(scene)
        print("[BATCH] Forced follow keyframes")
    except Exception as exc:
        print(f"[BATCH] ERROR forcing follow keyframes: {exc}")

    # Save per-route .blend
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        bpy.ops.wm.save_mainfile(filepath=str(out_path))
        print(f"[BATCH] Saved {out_path}")
    except Exception as exc:
        print(f"[BATCH] ERROR saving blend {out_path}: {exc}")


def main():
    # Parse arguments after '--'
    argv = sys.argv
    if "--" in argv:
        idx = argv.index("--") + 1
        user_args = argv[idx:]
    else:
        user_args = []

    if not user_args:
        print("[BATCH] ERROR: No manifest path provided. Use: -- path/to/manifest.txt [output_dir]")
        return

    manifest_path = Path(user_args[0]).expanduser().resolve()
    if len(user_args) > 1:
        output_dir = Path(user_args[1]).expanduser().resolve()
    else:
        output_dir = manifest_path.parent

    print(f"[BATCH] Manifest: {manifest_path}")
    print(f"[BATCH] Output dir: {output_dir}")

    if not manifest_path.exists():
        print("[BATCH] ERROR: Manifest file does not exist.")
        return

    entries = read_manifest(manifest_path)
    if not entries:
        print("[BATCH] No valid entries found in manifest.")
        return

    print(f"[BATCH] Found {len(entries)} route entries")

    _load_addon_from_this_folder()

    for task_id, pickup, dropoff in entries:
        pickup_slug = _slugify(pickup)
        dropoff_slug = _slugify(dropoff)
        filename = f"{task_id}_{pickup_slug}_to_{dropoff_slug}.blend"
        out_path = output_dir / filename
        _run_single_route(task_id, pickup, dropoff, out_path)


if __name__ == "__main__":
    main()

