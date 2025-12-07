"""
Minimal pipeline diagnostic for car/sign parenting during route import.

This script is intended to be run in Blender with the CashCab addon enabled
and a route already imported (or after the user triggers the route import
operator manually). It does NOT modify any addon code.
"""

import bpy
from mathutils import Vector


def _log_header(title: str) -> None:
    bar = "=" * 60
    print(f"\n{bar}\n{title}\n{bar}")


def _get_car_and_sign_objects():
    cars = []
    signs = []
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        name_l = obj.name.lower()
        if any(k in name_l for k in ["car", "vehicle", "body"]):
            cars.append(obj)
        elif any(k in name_l for k in ["taxi", "sign"]):
            signs.append(obj)
    return cars, signs


def inspect_pipeline_state():
    """Inspect current scene for car/sign parenting and transforms."""
    _log_header("PIPELINE TAXI SIGN DIAGNOSTICS")

    cars, signs = _get_car_and_sign_objects()

    print(f"\nFound {len(cars)} car-like mesh objects:")
    for car in cars:
        print(
            f"  - {car.name} | loc={tuple(car.location)} "
            f"| world={tuple(car.matrix_world.translation)} "
            f"| parent={car.parent.name if car.parent else 'None'}"
        )

    print(f"\nFound {len(signs)} taxi/sign mesh objects:")
    for sign in signs:
        print(
            f"  - {sign.name} | loc={tuple(sign.location)} "
            f"| world={tuple(sign.matrix_world.translation)} "
            f"| parent={sign.parent.name if sign.parent else 'None'}"
        )

    _log_header("PARENTING RELATIONSHIPS")
    pair_count = 0
    for sign in signs:
        parent = sign.parent
        if parent and parent in cars:
            pair_count += 1
            local = tuple(sign.location)
            world = tuple(sign.matrix_world.translation)
            print(f"\n✓ {sign.name} parented to {parent.name}")
            print(f"  local={local}")
            print(f"  world={world}")
            print(f"  parent_world={tuple(parent.matrix_world.translation)}")
            print(f"  matrix_parent_inverse={tuple(sign.matrix_parent_inverse.translation)}")
        else:
            print(f"\n❌ {sign.name} has no car parent")
            if parent:
                print(f"  current parent: {parent.name} ({parent.type})")

    if pair_count == 0:
        print("\nNo taxi signs parented to detected car objects.")

    _log_header("ORIGIN / STATIONARY CHECK")
    origin = Vector((0.0, 0.0, 0.0))
    for sign in signs:
        dist_world = (sign.matrix_world.translation - origin).length
        print(
            f"{sign.name}: world_dist_from_origin={dist_world:.6f}, "
            f"world={tuple(sign.matrix_world.translation)}"
        )


def main():
    inspect_pipeline_state()


if __name__ == "__main__":
    main()

