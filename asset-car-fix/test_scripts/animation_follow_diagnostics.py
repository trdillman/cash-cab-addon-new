"""
Animation Follow Diagnostics for Car & Taxi Sign

Run inside Blender (headless or UI) on a scene that already contains
car and taxi sign objects (e.g., saved test scenes from asset-car-fix).

This script:
- Detects car-like and taxi/sign-like mesh objects.
- Steps through the animation frame range.
- Logs how far the sign is from the car and from the world origin.

It does NOT modify any addon code or scene data.
"""

import bpy
from mathutils import Vector


def _log_header(title: str) -> None:
    bar = "=" * 80
    print(f"\n{bar}\n{title}\n{bar}")


def _find_car_and_sign():
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


def analyze_follow_behavior():
    scene = bpy.context.scene
    if scene is None:
        print("No active scene, aborting.")
        return

    _log_header("ANIMATION FOLLOW DIAGNOSTICS")
    print(f"Scene: {scene.name}")

    cars, signs = _find_car_and_sign()
    print(f"Detected {len(cars)} car-like meshes and {len(signs)} taxi/sign meshes.")

    if not cars or not signs:
        print("Insufficient objects to analyze (need at least one car and one sign).")
        return

    # For now, use the first car and first sign as the primary pair
    car = cars[0]
    sign = signs[0]

    print(f"Using car: {car.name}")
    print(f"Using sign: {sign.name}")
    print(f"Sign parent: {sign.parent.name if sign.parent else 'None'}")

    frame_start = scene.frame_start
    frame_end = scene.frame_end
    frame_step = max(1, (frame_end - frame_start) // 20)  # ~20 samples across range

    origin = Vector((0.0, 0.0, 0.0))

    distances_car = []
    distances_origin = []

    _log_header("FRAME-BY-FRAME DISTANCES")
    for frame in range(frame_start, frame_end + 1, frame_step):
        scene.frame_set(frame)

        car_pos = car.matrix_world.translation.copy()
        sign_pos = sign.matrix_world.translation.copy()

        dist_to_car = (sign_pos - car_pos).length
        dist_to_origin = (sign_pos - origin).length

        distances_car.append(dist_to_car)
        distances_origin.append(dist_to_origin)

        print(
            f"Frame {frame:4d} | car={tuple(round(c, 3) for c in car_pos)} "
            f"| sign={tuple(round(s, 3) for s in sign_pos)} "
            f"| d(sign,car)={dist_to_car:.3f} "
            f"| d(sign,origin)={dist_to_origin:.3f}"
        )

    if not distances_car:
        print("No frames sampled; check frame range.")
        return

    _log_header("SUMMARY")
    min_dc = min(distances_car)
    max_dc = max(distances_car)
    min_do = min(distances_origin)
    max_do = max(distances_origin)

    print(f"Sign-to-car distance: min={min_dc:.3f}, max={max_dc:.3f}")
    print(f"Sign-to-origin distance: min={min_do:.3f}, max={max_do:.3f}")

    if max_dc < 10.0:
        print("✅ Sign stays reasonably near the car across sampled frames.")
    else:
        print("❌ Sign drifts or stays far from the car during animation.")

    if max_do < 5.0:
        print("⚠️ Sign remains near world origin most of the time.")


def main():
    analyze_follow_behavior()


if __name__ == "__main__":
    main()

