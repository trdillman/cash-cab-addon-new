"""
Standalone Analysis - Avoid CashCab Addon

Analyze ASSET_CAR.blend without addon interference.
"""

import bpy
import sys
from pathlib import Path

def disable_cashcab_addon():
    """Attempt to disable the CashCab addon temporarily"""
    try:
        # Get addon preferences
        addon_name = "cash-cab-addon"
        if addon_name in bpy.context.preferences.addons:
            bpy.ops.wm.addon_disable(module=addon_name)
            print("CashCab addon disabled")
            return True
        else:
            print("CashCab addon not found in preferences")
            return False
    except Exception as e:
        print(f"Error disabling addon: {e}")
        return False

def analyze_asset_standalone():
    """Analyze the asset file in a clean environment"""

    print("=== Standalone Asset Analysis ===")
    print("Attempting to analyze ASSET_CAR.blend without addon interference")

    # Try to disable addon first
    addon_disabled = disable_cashcab_addon()

    # Clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for collection in bpy.data.collections:
        if collection.name != 'Master Collection':
            bpy.data.collections.remove(collection, do_unlink=True)

    asset_path = Path(__file__).parent.parent / "assets" / "ASSET_CAR.blend"
    print(f"Asset file path: {asset_path}")

    if not asset_path.exists():
        print("ERROR: ASSET_CAR.blend not found!")
        return False

    # Import the asset file using a different method
    try:
        print("Importing asset file using bpy.data.libraries.load...")

        # Try linking as library and examining structure
        with bpy.data.libraries.load(str(asset_path)) as (data_from_library):
            print(f"Library loaded successfully")
            print(f"Available blocks: {list(data_from_library.keys())}")

        # Check what was imported
        print("\n=== Imported Objects ===")
        for obj in bpy.data.objects:
            print(f"Object: {obj.name}")
            print(f"  Type: {obj.type}")
            print(f"  Location: {obj.location}")
            print(f"  Parent: {obj.parent.name if obj.parent else 'None'}")
            print(f"  Children: {len(obj.children)}")

            # Show parenting relationships
            if len(obj.children) > 0:
                for child in obj.children:
                    print(f"    -> Child: {child.name} (local: {child.location})")

        print("\n=== Imported Collections ===")
        for collection in bpy.data.collections:
            if collection.name != 'Master Collection':
                print(f"Collection: {collection.name}")
                print(f"  Objects: {len(collection.objects)}")
                for obj in collection.objects:
                    print(f"    {obj.name} (parent: {obj.parent.name if obj.parent else 'None'})")

        return True

    except Exception as e:
        print(f"ERROR during import: {e}")
        return False

def main():
    """Run standalone analysis"""
    print("Standalone ASSET_CAR.blend Analysis")
    print("=" * 50)

    success = analyze_asset_standalone()

    if success:
        print("\n" + "=" * 50)
        print("ANALYSIS COMPLETED SUCCESSFULLY")
        print("The asset file structure has been examined")
        return 0
    else:
        print("\n" + "=" * 50)
        print("ANALYSIS FAILED")
        print("Could not examine the asset file")
        return 1

if __name__ == "__main__":
    result = main()
    sys.exit(result)